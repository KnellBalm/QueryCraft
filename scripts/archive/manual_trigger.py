import os
import sys
from datetime import date

# Add project root to path
sys.path.append("/home/naca11/QueryCraft")

from backend.scheduler import run_weekday_generation
from backend.common.logging import get_logger

logger = get_logger("manual_trigger")

print(f"Starting manual trigger for {date.today()}...")
try:
    run_weekday_generation()
    print("Manual trigger finished successfully.")
except Exception as e:
    print(f"Manual trigger failed: {e}")
    import traceback
    traceback.print_exc()
