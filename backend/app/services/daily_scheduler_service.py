import json
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.core.database import SessionLocal, create_db_engine
from app.models import ScheduledJobRun, NotificationSettings
from app.services.inventory_alert_service import InventoryAlertService
from app.services.email_service import EmailNotificationService

logger = logging.getLogger("stocksense.scheduler")
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


class DailySchedulerService:
    """
    Automated daily scheduled inventory check engine.
    Runs independently of user logins, creates daily snapshots,
    triggers email notifications, and logs execution to Neon PostgreSQL.
    """

    @classmethod
    def execute_daily_inventory_check(
        cls,
        db: Session,
        scheduled_for: Optional[datetime] = None,
        force_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the daily inventory audit, snapshotting, and email notifications.
        Prevents duplicate execution on the same calendar day unless force_run=True.
        """
        now_dt = datetime.now(KOLKATA_TZ)
        today = now_dt.date()
        sched_time = scheduled_for or now_dt

        # Check if already completed successfully for today
        if not force_run:
            existing_run = (
                db.query(ScheduledJobRun)
                .filter(
                    ScheduledJobRun.job_name == "daily_inventory_check",
                    ScheduledJobRun.status == "success"
                )
                .order_by(desc(ScheduledJobRun.started_at))
                .first()
            )
            if existing_run and existing_run.started_at.astimezone(KOLKATA_TZ).date() == today:
                logger.info(f"Daily inventory check already completed today ({today}). Skipping duplicate run.")
                return {
                    "status": "skipped",
                    "message": f"Daily check already executed successfully for {today}.",
                    "run_id": existing_run.id,
                }

        # Initialize ScheduledJobRun entry
        job_run = ScheduledJobRun(
            job_name="daily_inventory_check",
            scheduled_at=sched_time,
            started_at=now_dt,
            status="running"
        )
        db.add(job_run)
        db.commit()
        db.refresh(job_run)

        try:
            # 1. Reconcile alerts and generate daily snapshot in Neon
            summary_data = InventoryAlertService.reconcile_and_snapshot(
                db=db,
                reporting_date=today,
                job_run_id=job_run.id
            )

            # 2. Dispatch email notifications
            email_results = EmailNotificationService.send_scheduled_inventory_email(
                db=db,
                summary_data=summary_data,
                reporting_date=today,
                report_type="daily_inventory",
                job_run_id=job_run.id
            )

            # 3. Finalize Job Run Log
            summary_counts = {
                "near_expiry_count": summary_data["summary"]["near_expiry_count"],
                "low_stock_count": summary_data["summary"]["low_stock_count"],
                "out_of_stock_count": summary_data["summary"]["out_of_stock_count"],
                "emails_attempted": len(email_results),
                "emails_accepted": sum(1 for e in email_results if e.get("status") == "accepted"),
            }

            finished_dt = datetime.now(KOLKATA_TZ)
            job_run.finished_at = finished_dt
            job_run.status = "success"
            job_run.summary_counts = json.dumps(summary_counts)
            db.commit()

            return {
                "status": "success",
                "run_id": job_run.id,
                "summary": summary_counts,
                "email_results": email_results,
                "execution_duration_seconds": round((finished_dt - now_dt).total_seconds(), 2)
            }

        except Exception as e:
            db.rollback()
            err_msg = str(e)
            logger.error(f"Daily inventory check failed: {err_msg}", exc_info=True)
            job_run.finished_at = datetime.now(KOLKATA_TZ)
            job_run.status = "failed"
            job_run.error_details = err_msg
            db.commit()
            return {
                "status": "failed",
                "run_id": job_run.id,
                "error": err_msg
            }


# Background Async Worker for FastAPI lifespan
async def start_scheduler_loop():
    """
    Background heartbeat loop checking every 60 seconds if the current local time (Asia/Kolkata)
    matches the configured INVENTORY_CHECK_TIME (default 08:00) and hasn't executed yet today.
    """
    logger.info(f"Daily Inventory Scheduler active. Target schedule: {settings.INVENTORY_CHECK_TIME} ({settings.APP_TIMEZONE}).")
    while True:
        try:
            now_kolkata = datetime.now(KOLKATA_TZ)
            current_time_str = now_kolkata.strftime("%H:%M")

            if current_time_str == settings.INVENTORY_CHECK_TIME:
                engine = create_db_engine()
                from sqlalchemy.orm import sessionmaker
                Session = sessionmaker(bind=engine)
                db = Session()
                try:
                    DailySchedulerService.execute_daily_inventory_check(db=db)
                finally:
                    db.close()
                # Sleep 70 seconds to avoid multiple triggers within the same minute
                await asyncio.sleep(70)
        except Exception as e:
            logger.error(f"Scheduler worker error: {e}")
        await asyncio.sleep(30)
