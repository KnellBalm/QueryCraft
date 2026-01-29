"""
Migration: Convert pa_users.signup_at from TIMESTAMP to DATE
Author: Claude Code
Date: 2026-01-29
Reason: Fix schema mismatch - generator creates DATE, but old table has TIMESTAMP
"""

import sys
import os

def migrate():
    """Execute the migration"""
    sys.path.insert(0, '/app')
    from backend.services.database import postgres_connection
    from backend.common.logging import get_logger
    
    logger = get_logger(__name__)
    
    try:
        with postgres_connection() as pg:
            # Check current type
            result = pg.fetch_df("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'pa_users' 
                AND column_name = 'signup_at'
            """)
            
            if len(result) == 0:
                logger.info("pa_users table does not exist yet. Skipping migration.")
                return
            
            current_type = result.iloc[0]['data_type']
            logger.info(f"Current signup_at type: {current_type}")
            
            if current_type == 'date':
                logger.info("signup_at is already DATE type. No migration needed.")
                return
            
            # Alter column type
            logger.info("Converting signup_at from TIMESTAMP to DATE...")
            pg.execute("ALTER TABLE public.pa_users ALTER COLUMN signup_at TYPE DATE")
            logger.info("✓ Migration completed successfully!")
            
            # Verify
            result = pg.fetch_df("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'pa_users' 
                AND column_name = 'signup_at'
            """)
            new_type = result.iloc[0]['data_type']
            logger.info(f"New signup_at type: {new_type}")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
