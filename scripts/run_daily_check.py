#!/usr/bin/env python3
"""
Manual Daily Inventory Check CLI Runner for StockSense
Usage: python scripts/run_daily_check.py [--force]
"""

import sys
import os
import argparse

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import create_db_engine
from sqlalchemy.orm import sessionmaker
from app.services.daily_scheduler_service import DailySchedulerService


def main():
    parser = argparse.ArgumentParser(description="StockSense Manual Daily Inventory Audit & Notification Runner")
    parser.add_argument("--force", action="store_true", help="Force execution even if already completed today")
    args = parser.parse_args()

    print("=" * 70)
    print("StockSense — Triggering Scheduled Daily Inventory Check")
    print("=" * 70)

    engine = create_db_engine()
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        res = DailySchedulerService.execute_daily_inventory_check(db=db, force_run=args.force)
        print(f"Status: {res.get('status')}")
        print(f"Details: {res}")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    main()
