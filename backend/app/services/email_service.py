import smtplib
import uuid
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import NotificationSettings, EmailDeliveryLog, ScheduledJobRun

logger = logging.getLogger("stocksense.email")
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


class EmailNotificationService:
    """
    Handles generation of responsive HTML/plain-text inventory alert emails,
    SMTP delivery with TLS, bounded retries, deduplication via idempotency keys,
    and audit logging in Neon PostgreSQL.
    """

    @classmethod
    def generate_html_template(
        cls,
        summary_data: Dict[str, Any],
        reporting_date: date,
        settings_obj: Optional[NotificationSettings] = None
    ) -> str:
        rep_date_str = reporting_date.strftime("%A, %d %B %Y")
        summary = summary_data.get("summary", {})
        near_expiry_count = summary.get("near_expiry_count", 0)
        low_stock_count = summary.get("low_stock_count", 0)
        out_of_stock_count = summary.get("out_of_stock_count", 0)
        alerts_url = f"{settings.APP_PUBLIC_URL}/alerts"

        # Check enabled categories
        enabled_cats = settings_obj.categories.split(",") if settings_obj and settings_obj.categories else [
            "near_expiry", "low_stock", "out_of_stock", "sales_summary"
        ]
        enabled_cats = [c.strip() for c in enabled_cats]

        # Near Expiry Rows
        near_expiry_rows = ""
        if "near_expiry" in enabled_cats:
            for item in summary_data.get("near_expiry", [])[:10]:
                is_crit = item["severity"] == "critical"
                badge_bg = "#FEE2E2" if is_crit else "#FEF3C7"
                badge_color = "#991B1B" if is_crit else "#92400E"
                near_expiry_rows += f"""
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 10px; font-weight: 600; color: #111827;">{item['product_name']}<br><span style="font-size: 11px; color: #6B7280; font-weight: normal;">SKU: {item['sku']} | Batch: {item['batch_number']}</span></td>
                    <td style="padding: 10px; text-align: center; color: #374151;">{item['remaining_quantity']}</td>
                    <td style="padding: 10px; text-align: center; color: #374151;">{item['expiry_date']}</td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600;">
                            {item['days_until_expiry']} days left
                        </span>
                    </td>
                    <td style="padding: 10px; font-size: 12px; color: #4B5563;">{item['recommended_action']}</td>
                </tr>
                """

        # Low Stock Rows
        low_stock_rows = ""
        if "low_stock" in enabled_cats:
            for item in summary_data.get("low_stock", [])[:10]:
                low_stock_rows += f"""
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 10px; font-weight: 600; color: #111827;">{item['product_name']}<br><span style="font-size: 11px; color: #6B7280; font-weight: normal;">SKU: {item['sku']}</span></td>
                    <td style="padding: 10px; text-align: center; font-weight: bold; color: #D97706;">{item['current_stock']}</td>
                    <td style="padding: 10px; text-align: center; color: #4B5563;">{item['reorder_threshold']}</td>
                    <td style="padding: 10px; text-align: center; color: #10B981; font-weight: 600;">+{item['suggested_reorder_qty']}</td>
                    <td style="padding: 10px; font-size: 12px; color: #4B5563;">{item['recommended_action']}</td>
                </tr>
                """

        # Out of Stock Rows
        out_of_stock_rows = ""
        if "out_of_stock" in enabled_cats:
            for item in summary_data.get("out_of_stock", [])[:10]:
                out_of_stock_rows += f"""
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 10px; font-weight: 600; color: #111827;">{item['product_name']}<br><span style="font-size: 11px; color: #6B7280; font-weight: normal;">SKU: {item['sku']}</span></td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="background-color: #FEE2E2; color: #B91C1C; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700;">OUT OF STOCK</span>
                    </td>
                    <td style="padding: 10px; font-size: 12px; color: #4B5563;">{item['last_stock_movement']}</td>
                    <td style="padding: 10px; font-size: 12px; color: #B91C1C; font-weight: 500;">{item['recommended_action']}</td>
                </tr>
                """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StockSense Daily Inventory Alert</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #F3F4F6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1F2937;">
            <div style="max-width: 680px; margin: 20px auto; background-color: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 24px 32px; color: #FFFFFF;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">StockSense</h1>
                            <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.9;">Smart Inventory & Expiry Tracker for Small Retailers</p>
                        </div>
                    </div>
                    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.2); font-size: 13px;">
                        <span>📅 <strong>Report Date:</strong> {rep_date_str}</span> | <span>🕒 <strong>Timezone:</strong> Asia/Kolkata</span>
                    </div>
                </div>

                <!-- KPI Metric Cards -->
                <div style="padding: 24px 32px 12px 32px;">
                    <div style="display: table; width: 100%; border-collapse: separate; border-spacing: 12px 0;">
                        <div style="display: table-cell; width: 33.33%; background-color: #FEF3C7; border: 1px solid #FCD34D; border-radius: 8px; padding: 14px; text-align: center;">
                            <div style="font-size: 11px; font-weight: 700; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px;">Near Expiry (≤7d)</div>
                            <div style="font-size: 28px; font-weight: 800; color: #B45309; margin-top: 4px;">{near_expiry_count}</div>
                        </div>
                        <div style="display: table-cell; width: 33.33%; background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px; text-align: center;">
                            <div style="font-size: 11px; font-weight: 700; color: #1E40AF; text-transform: uppercase; letter-spacing: 0.5px;">Low Stock</div>
                            <div style="font-size: 28px; font-weight: 800; color: #1D4ED8; margin-top: 4px;">{low_stock_count}</div>
                        </div>
                        <div style="display: table-cell; width: 33.33%; background-color: #FEE2E2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 14px; text-align: center;">
                            <div style="font-size: 11px; font-weight: 700; color: #991B1B; text-transform: uppercase; letter-spacing: 0.5px;">Out of Stock</div>
                            <div style="font-size: 28px; font-weight: 800; color: #DC2626; margin-top: 4px;">{out_of_stock_count}</div>
                        </div>
                    </div>
                </div>

                <!-- Section 1: Near Expiry -->
                {f'''
                <div style="padding: 16px 32px;">
                    <h2 style="font-size: 16px; font-weight: 700; color: #92400E; margin-bottom: 8px; border-left: 4px solid #F59E0B; padding-left: 8px;">
                        ⚠️ Products Nearing Expiry ({near_expiry_count})
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                        <thead>
                            <tr style="background-color: #F9FAFB; border-bottom: 2px solid #E5E7EB; color: #6B7280; font-size: 11px; text-transform: uppercase;">
                                <th style="padding: 8px 10px;">Product & Batch</th>
                                <th style="padding: 8px 10px; text-align: center;">Qty</th>
                                <th style="padding: 8px 10px; text-align: center;">Expiry</th>
                                <th style="padding: 8px 10px; text-align: center;">Status</th>
                                <th style="padding: 8px 10px;">Recommended Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {near_expiry_rows if near_expiry_rows else '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #6B7280;">No products currently nearing expiry.</td></tr>'}
                        </tbody>
                    </table>
                </div>
                ''' if "near_expiry" in enabled_cats else ''}

                <!-- Section 2: Low Stock -->
                {f'''
                <div style="padding: 16px 32px;">
                    <h2 style="font-size: 16px; font-weight: 700; color: #1E40AF; margin-bottom: 8px; border-left: 4px solid #3B82F6; padding-left: 8px;">
                        📉 Very Low-Stock Products ({low_stock_count})
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                        <thead>
                            <tr style="background-color: #F9FAFB; border-bottom: 2px solid #E5E7EB; color: #6B7280; font-size: 11px; text-transform: uppercase;">
                                <th style="padding: 8px 10px;">Product</th>
                                <th style="padding: 8px 10px; text-align: center;">Current Stock</th>
                                <th style="padding: 8px 10px; text-align: center;">Threshold</th>
                                <th style="padding: 8px 10px; text-align: center;">Reorder Qty</th>
                                <th style="padding: 8px 10px;">Recommended Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {low_stock_rows if low_stock_rows else '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #6B7280;">No products currently below reorder thresholds.</td></tr>'}
                        </tbody>
                    </table>
                </div>
                ''' if "low_stock" in enabled_cats else ''}

                <!-- Section 3: Out of Stock -->
                {f'''
                <div style="padding: 16px 32px;">
                    <h2 style="font-size: 16px; font-weight: 700; color: #991B1B; margin-bottom: 8px; border-left: 4px solid #EF4444; padding-left: 8px;">
                        🚨 Completely Out-of-Stock Products ({out_of_stock_count})
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                        <thead>
                            <tr style="background-color: #F9FAFB; border-bottom: 2px solid #E5E7EB; color: #6B7280; font-size: 11px; text-transform: uppercase;">
                                <th style="padding: 8px 10px;">Product</th>
                                <th style="padding: 8px 10px; text-align: center;">Status</th>
                                <th style="padding: 8px 10px;">Last Stock Movement</th>
                                <th style="padding: 8px 10px;">Replenishment Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {out_of_stock_rows if out_of_stock_rows else '<tr><td colspan="4" style="padding: 12px; text-align: center; color: #6B7280;">No out-of-stock items detected.</td></tr>'}
                        </tbody>
                    </table>
                </div>
                ''' if "out_of_stock" in enabled_cats else ''}

                <!-- CTA Button -->
                <div style="padding: 24px 32px; text-align: center; background-color: #F9FAFB; border-top: 1px solid #E5E7EB; margin-top: 20px;">
                    <a href="{alerts_url}" style="display: inline-block; background: #2563EB; color: #FFFFFF; font-weight: 600; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-size: 14px; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);">
                        View All Active Alerts in StockSense &rarr;
                    </a>
                    <p style="margin: 12px 0 0 0; font-size: 12px; color: #6B7280;">
                        This automated notification was generated by StockSense scheduled inventory check.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @classmethod
    def generate_plain_text(
        cls,
        summary_data: Dict[str, Any],
        reporting_date: date,
        settings_obj: Optional[NotificationSettings] = None
    ) -> str:
        summary = summary_data.get("summary", {})
        lines = [
            "=" * 60,
            "STOCKSENSE — DAILY INVENTORY & EXPIRY ALERT REPORT",
            "=" * 60,
            f"Report Date: {reporting_date.strftime('%Y-%m-%d')} (Asia/Kolkata)",
            f"Near Expiry: {summary.get('near_expiry_count', 0)} | Low Stock: {summary.get('low_stock_count', 0)} | Out of Stock: {summary.get('out_of_stock_count', 0)}",
            "-" * 60,
        ]

        # Near Expiry
        lines.append("\n[1] PRODUCTS NEARING EXPIRY:")
        near_expiry = summary_data.get("near_expiry", [])
        if near_expiry:
            for it in near_expiry[:10]:
                lines.append(f"  * {it['product_name']} ({it['sku']}) - Batch: {it['batch_number']}, Qty: {it['remaining_quantity']}, Expires: {it['expiry_date']} ({it['days_until_expiry']} days left). Action: {it['recommended_action']}")
        else:
            lines.append("  (None)")

        # Low Stock
        lines.append("\n[2] VERY LOW-STOCK PRODUCTS:")
        low_stock = summary_data.get("low_stock", [])
        if low_stock:
            for it in low_stock[:10]:
                lines.append(f"  * {it['product_name']} ({it['sku']}) - Current Stock: {it['current_stock']} (Threshold: {it['reorder_threshold']}), Suggested Reorder: +{it['suggested_reorder_qty']}. Action: {it['recommended_action']}")
        else:
            lines.append("  (None)")

        # Out of Stock
        lines.append("\n[3] OUT-OF-STOCK PRODUCTS:")
        out_of_stock = summary_data.get("out_of_stock", [])
        if out_of_stock:
            for it in out_of_stock[:10]:
                lines.append(f"  * {it['product_name']} ({it['sku']}) - Available: 0. Last Movement: {it['last_stock_movement']}. Action: {it['recommended_action']}")
        else:
            lines.append("  (None)")

        lines.extend([
            "\n" + "-" * 60,
            f"Access Live Dashboard: {settings.APP_PUBLIC_URL}/alerts",
            "=" * 60,
        ])
        return "\n".join(lines)

    @classmethod
    def send_scheduled_inventory_email(
        cls,
        db: Session,
        summary_data: Dict[str, Any],
        reporting_date: date,
        report_type: str = "daily_inventory",
        job_run_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Sends the scheduled inventory summary email to all configured recipients
        with idempotency check to prevent duplicate emails for the same reporting date.
        """
        notif = db.query(NotificationSettings).filter(NotificationSettings.shop_id == "default_shop").first()
        if not notif or not notif.enabled or not notif.recipient_emails.strip():
            logger.info("Notification settings disabled or no recipients configured.")
            return []

        recipients = [e.strip() for e in notif.recipient_emails.split(",") if e.strip() and "@" in e]
        if not recipients:
            return []

        # Check empty report rule
        summary = summary_data.get("summary", {})
        total_alerts = summary.get("near_expiry_count", 0) + summary.get("low_stock_count", 0) + summary.get("out_of_stock_count", 0)
        if total_alerts == 0 and not notif.include_empty_reports:
            logger.info("Skipping email send: no active alerts and include_empty_reports is False.")
            return []

        subject = f"StockSense Alert: {summary.get('near_expiry_count', 0)} Near Expiry, {summary.get('low_stock_count', 0)} Low Stock, {summary.get('out_of_stock_count', 0)} Out of Stock [{reporting_date.strftime('%d %b')}]"
        html_body = cls.generate_html_template(summary_data, reporting_date, notif)
        text_body = cls.generate_plain_text(summary_data, reporting_date, notif)

        results = []
        for recipient in recipients:
            idempotency_key = f"{report_type}:{reporting_date.isoformat()}:{recipient}"

            # Idempotency check: has this email already been successfully dispatched for today?
            existing_log = db.query(EmailDeliveryLog).filter(
                EmailDeliveryLog.idempotency_key == idempotency_key,
                EmailDeliveryLog.status == "accepted"
            ).first()

            if existing_log:
                logger.info(f"Duplicate email prevented for {recipient} via idempotency key: {idempotency_key}")
                results.append({
                    "recipient": recipient,
                    "status": "skipped_duplicate",
                    "idempotency_key": idempotency_key
                })
                continue

            delivery_result = cls._dispatch_email(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                report_type=report_type,
                idempotency_key=idempotency_key,
                scheduled_run_id=job_run_id,
                db=db
            )
            results.append(delivery_result)

        db.commit()
        return results

    @classmethod
    def send_test_email(cls, db: Session, recipient_email: str) -> Dict[str, Any]:
        """
        Dispatches a dedicated test email to verify SMTP host, port, authentication, and TLS.
        """
        recipient = recipient_email.strip()
        if not recipient or "@" not in recipient:
            return {"success": False, "message": "Invalid recipient email address."}

        test_date = datetime.now(KOLKATA_TZ).date()
        idempotency_key = f"test:{test_date.isoformat()}:{recipient}:{uuid.uuid4().hex[:8]}"

        subject = "StockSense Test Email — SMTP Configuration Verified"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 24px; border: 1px solid #E5E7EB; border-radius: 8px;">
            <h2 style="color: #2563EB; margin-top: 0;">StockSense SMTP Configuration Test</h2>
            <p>Congratulations! Your email notification settings have been successfully verified.</p>
            <p><strong>Configured Business Timezone:</strong> Asia/Kolkata</p>
            <p><strong>Generated At:</strong> {datetime.now(KOLKATA_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
            <p style="color: #4B5563; font-size: 13px;">This test confirms that your server can transmit daily inventory snapshots and near-expiry alerts directly to your inbox.</p>
        </div>
        """
        text_body = "StockSense SMTP Configuration Test\nCongratulations! Your email notification settings have been verified."

        res = cls._dispatch_email(
            recipient=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            report_type="test_email",
            idempotency_key=idempotency_key,
            scheduled_run_id=None,
            db=db
        )
        return res

    @classmethod
    def _dispatch_email(
        cls,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        report_type: str,
        idempotency_key: str,
        scheduled_run_id: Optional[int],
        db: Session
    ) -> Dict[str, Any]:
        now_dt = datetime.now(KOLKATA_TZ)

        # Find existing log entry by idempotency_key or initialize new one
        log_entry = db.query(EmailDeliveryLog).filter(
            EmailDeliveryLog.idempotency_key == idempotency_key
        ).first()

        if not log_entry:
            log_entry = EmailDeliveryLog(
                report_type=report_type,
                recipient=recipient,
                scheduled_run_id=scheduled_run_id,
                idempotency_key=idempotency_key,
                attempt_count=0,
                status="queued",
                created_at=now_dt
            )
            db.add(log_entry)

        # Check if email is enabled and credentials exist
        if not settings.EMAIL_ENABLED or not settings.SMTP_HOST:
            logger.warning("SMTP disabled or SMTP_HOST unconfigured. Recording log as disabled.")
            log_entry.scheduled_run_id = scheduled_run_id or log_entry.scheduled_run_id
            log_entry.attempt_count = (log_entry.attempt_count or 0) + 1
            log_entry.status = "disabled"
            log_entry.last_attempt_at = now_dt
            log_entry.failure_reason = "Email disabled in configuration (EMAIL_ENABLED=false or SMTP_HOST unset)"
            db.commit()
            return {
                "success": False,
                "status": "disabled",
                "recipient": recipient,
                "message": "Email delivery is disabled in application configuration (SMTP_HOST unset).",
                "log_id": log_entry.id
            }

        # Compose MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = recipient
        msg["Date"] = now_dt.strftime("%a, %d %b %Y %H:%M:%S +0530")
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        max_retries = 3
        last_error = ""

        for attempt in range(1, max_retries + 1):
            try:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

                server.sendmail(settings.SMTP_FROM_EMAIL, [recipient], msg.as_string())
                server.quit()

                provider_msg_id = f"smtp-{uuid.uuid4().hex[:12]}"
                log_entry.scheduled_run_id = scheduled_run_id or log_entry.scheduled_run_id
                log_entry.attempt_count = attempt
                log_entry.status = "accepted"
                log_entry.provider_message_id = provider_msg_id
                log_entry.last_attempt_at = now_dt
                log_entry.accepted_at = now_dt
                log_entry.failure_reason = None
                db.commit()
                return {
                    "success": True,
                    "status": "accepted",
                    "recipient": recipient,
                    "provider_message_id": provider_msg_id,
                    "message": "Email successfully accepted by SMTP provider.",
                    "log_id": log_entry.id
                }
            except Exception as e:
                last_error = str(e)
                logger.error(f"SMTP send attempt {attempt} failed: {e}")

        # If all retries fail
        log_entry.scheduled_run_id = scheduled_run_id or log_entry.scheduled_run_id
        log_entry.attempt_count = max_retries
        log_entry.status = "failed"
        log_entry.last_attempt_at = now_dt
        log_entry.failure_reason = last_error
        db.commit()
        return {
            "success": False,
            "status": "failed",
            "recipient": recipient,
            "message": f"SMTP delivery failed after {max_retries} attempts: {last_error}",
            "log_id": log_entry.id
        }
