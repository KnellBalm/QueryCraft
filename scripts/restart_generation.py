import os
import sys
from datetime import date
from backend.common.date_utils import get_today_kst
from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv
from backend.generator.data_generator_advanced import generate_data
from problems.generator import generate
from backend.common.logging import get_logger

logger = get_logger("restart_script")

def run_restart():
    today = get_today_kst()
    print(f"Starting generation for {today} with new limits...")
    
    # 1. Data generation
    try:
        generate_data(modes=("pa", "stream"))
        print("✓ Data generation completed")
    except Exception as e:
        print(f"✗ Data generation failed: {e}")
        return

    # 2. Problem generation
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        for mode in ["pa", "stream"]:
            print(f"Generating {mode.upper()} problems...")
            path = generate(today, pg, mode=mode)
            if path:
                print(f"✓ {mode.upper()} problems generated: {path}")
            else:
                print(f"✗ {mode.upper()} problems generation failed")
    except Exception as e:
        print(f"✗ Problem generation error: {e}")
    finally:
        pg.close()

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.append(os.getcwd())
    run_restart()
