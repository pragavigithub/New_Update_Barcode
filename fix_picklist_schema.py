#!/usr/bin/env python3
"""
SQLite Schema Migration Script for Pick List Tables
Adds missing columns to match the updated model definitions
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get the database URL from app configuration"""
    # Try to get from environment first
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fallback to SQLite for Replit environment
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'wms.db')
    return f"sqlite:///{sqlite_path}"

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        logger.warning(f"Could not inspect table {table_name}: {e}")
        return False

def migrate_pick_lists_table(engine):
    """Add missing columns to pick_lists table"""
    logger.info("🔄 Migrating pick_lists table...")
    
    # Check if table exists
    inspector = inspect(engine)
    if 'pick_lists' not in inspector.get_table_names():
        logger.info("❌ pick_lists table doesn't exist. Run db.create_all() first.")
        return False
    
    # List of columns to add
    columns_to_add = [
        ('absolute_entry', 'INTEGER'),
        ('name', 'VARCHAR(50)'),
        ('owner_code', 'INTEGER'),
        ('owner_name', 'VARCHAR(100)'),
        ('pick_date', 'DATETIME'),
        ('remarks', 'TEXT'),
        ('object_type', 'VARCHAR(10)'),
        ('use_base_units', 'VARCHAR(5)'),
        ('priority', 'VARCHAR(10)'),
        ('warehouse_code', 'VARCHAR(10)'),
        ('customer_code', 'VARCHAR(20)'),
        ('customer_name', 'VARCHAR(100)'),
        ('total_items', 'INTEGER'),
        ('picked_items', 'INTEGER'),
        ('notes', 'TEXT')
    ]
    
    added_columns = 0
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            if not check_column_exists(engine, 'pick_lists', column_name):
                try:
                    conn.execute(text(f"ALTER TABLE pick_lists ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {column_name} to pick_lists")
                    added_columns += 1
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
            else:
                logger.info(f"⏭️ Column {column_name} already exists in pick_lists")
    
    return added_columns > 0

def migrate_pick_list_lines_table(engine):
    """Add missing columns to pick_list_lines table"""
    logger.info("🔄 Migrating pick_list_lines table...")
    
    # Check if table exists
    inspector = inspect(engine)
    if 'pick_list_lines' not in inspector.get_table_names():
        logger.info("❌ pick_list_lines table doesn't exist. Run db.create_all() first.")
        return False
    
    # List of columns to add
    columns_to_add = [
        ('absolute_entry', 'INTEGER'),
        ('order_entry', 'INTEGER'),
        ('order_row_id', 'INTEGER'),
        ('pick_status', 'VARCHAR(20)'),
        ('released_quantity', 'REAL'),
        ('previously_released_quantity', 'REAL'),
        ('base_object_type', 'INTEGER'),
        ('serial_numbers', 'TEXT'),
        ('batch_numbers', 'TEXT')
    ]
    
    added_columns = 0
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            if not check_column_exists(engine, 'pick_list_lines', column_name):
                try:
                    conn.execute(text(f"ALTER TABLE pick_list_lines ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {column_name} to pick_list_lines")
                    added_columns += 1
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
            else:
                logger.info(f"⏭️ Column {column_name} already exists in pick_list_lines")
    
    return added_columns > 0

def main():
    """Main migration function"""
    logger.info("🚀 Starting Pick List schema migration...")
    
    database_url = get_database_url()
    logger.info(f"Using database: {database_url}")
    
    try:
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("✅ Database connection successful")
        
        # Run migrations
        pick_lists_migrated = migrate_pick_lists_table(engine)
        pick_list_lines_migrated = migrate_pick_list_lines_table(engine)
        
        if pick_lists_migrated or pick_list_lines_migrated:
            logger.info("✅ Schema migration completed successfully!")
        else:
            logger.info("ℹ️ No schema changes needed - all columns already exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)