#!/usr/bin/env python3
# backend/migrations/fix_api_usage_logs.py
"""
Migration: Fix api_usage_logs table schema

This migration updates the api_usage_logs table to match the actual usage in code:
- Adds 'purpose' column
- Adds 'timestamp' column
- Adds 'total_tokens' column
- Removes 'endpoint' and 'cost_usd' columns (not used)
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)


def migrate():
    """Fix api_usage_logs table schema"""
    try:
        with postgres_connection() as pg:
            logger.info("Updating api_usage_logs table schema...")
            
            # Check if purpose column exists
            check_df = pg.fetch_df("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'api_usage_logs'
            """)
            
            existing_columns = set(check_df['column_name'].tolist())
            logger.info(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            if 'purpose' not in existing_columns:
                logger.info("Adding 'purpose' column...")
                pg.execute("""
                    ALTER TABLE public.api_usage_logs 
                    ADD COLUMN purpose VARCHAR(100)
                """)
            
            if 'timestamp' not in existing_columns:
                logger.info("Adding 'timestamp' column...")
                pg.execute("""
                    ALTER TABLE public.api_usage_logs 
                    ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
            
            if 'total_tokens' not in existing_columns:
                logger.info("Adding 'total_tokens' column...")
                pg.execute("""
                    ALTER TABLE public.api_usage_logs 
                    ADD COLUMN total_tokens INTEGER DEFAULT 0
                """)
            
            # Remove legacy columns if they exist
            if 'endpoint' in existing_columns:
                logger.info("Dropping legacy 'endpoint' column...")
                pg.execute("ALTER TABLE public.api_usage_logs DROP COLUMN endpoint")
            
            if 'cost_usd' in existing_columns:
                logger.info("Dropping legacy 'cost_usd' column...")
                pg.execute("ALTER TABLE public.api_usage_logs DROP COLUMN cost_usd")
            
            # Change model type from TEXT to VARCHAR(50) if needed
            if 'model' in existing_columns:
                logger.info("Updating 'model' column type...")
                pg.execute("""
                    ALTER TABLE public.api_usage_logs 
                    ALTER COLUMN model TYPE VARCHAR(50)
                """)
            
            logger.info("✅ Successfully updated api_usage_logs table!")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
