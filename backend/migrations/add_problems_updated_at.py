#!/usr/bin/env python3
# backend/migrations/add_problems_updated_at.py
"""
Migration: Add updated_at column to problems table

This migration adds the missing updated_at column to the problems table
which is required by the problem generation code.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)


def migrate():
    """Add updated_at column to problems table if it doesn't exist"""
    try:
        with postgres_connection() as pg:
            logger.info("Checking if updated_at column exists in problems table...")
            
            # Check if column exists
            check_df = pg.fetch_df("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'problems' 
                AND column_name = 'updated_at'
            """)
            
            if len(check_df) > 0:
                logger.info("✓ updated_at column already exists. No migration needed.")
                return True
            
            # Add the column
            logger.info("Adding updated_at column to problems table...")
            pg.execute("""
                ALTER TABLE public.problems 
                ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
            """)
            
            logger.info("✅ Successfully added updated_at column to problems table!")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
