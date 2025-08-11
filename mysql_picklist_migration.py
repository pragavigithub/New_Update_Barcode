#!/usr/bin/env python3
"""
MySQL PickList Migration Script
Updates the PickList tables to match SAP B1 API structure
Run this script to migrate your MySQL database schema
"""

import pymysql
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PickListMigration:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect_mysql(self):
        """Connect to MySQL database"""
        try:
            mysql_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'warehouse_db'),
                'charset': 'utf8mb4'
            }
            
            logger.info(f"Connecting to MySQL at {mysql_config['host']}:{mysql_config['port']}")
            self.connection = pymysql.connect(**mysql_config)
            self.cursor = self.connection.cursor()
            logger.info("✅ MySQL connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ MySQL connection failed: {str(e)}")
            return False
    
    def column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        try:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}' 
                AND column_name = '{column_name}'
            """)
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking column {column_name}: {str(e)}")
            return False
    
    def table_exists(self, table_name):
        """Check if a table exists"""
        try:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}'
            """)
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {str(e)}")
            return False
    
    def migrate_pick_lists_table(self):
        """Migrate the pick_lists table with new SAP B1 compatible columns"""
        logger.info("🔄 Migrating pick_lists table...")
        
        migrations = [
            ("absolute_entry", "ADD COLUMN absolute_entry INT"),
            ("name", "ADD COLUMN name VARCHAR(100)"),
            ("owner_code", "ADD COLUMN owner_code INT"),
            ("owner_name", "ADD COLUMN owner_name VARCHAR(100)"),
            ("pick_date", "ADD COLUMN pick_date DATETIME"),
            ("remarks", "ADD COLUMN remarks TEXT"),
            ("object_type", "ADD COLUMN object_type VARCHAR(10)"),
            ("use_base_units", "ADD COLUMN use_base_units VARCHAR(5) DEFAULT 'tNO'"),
            ("priority", "ADD COLUMN priority VARCHAR(20) DEFAULT 'normal'"),
            ("warehouse_code", "ADD COLUMN warehouse_code VARCHAR(10)"),
            ("customer_code", "ADD COLUMN customer_code VARCHAR(50)"),
            ("customer_name", "ADD COLUMN customer_name VARCHAR(200)"),
            ("total_items", "ADD COLUMN total_items INT DEFAULT 0"),
            ("picked_items", "ADD COLUMN picked_items INT DEFAULT 0"),
            ("notes", "ADD COLUMN notes TEXT")
        ]
        
        for column_name, alter_statement in migrations:
            if not self.column_exists('pick_lists', column_name):
                try:
                    sql = f"ALTER TABLE pick_lists {alter_statement}"
                    self.cursor.execute(sql)
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Error adding column {column_name}: {str(e)}")
            else:
                logger.info(f"⏭️ Column {column_name} already exists")
        
        # Add index on absolute_entry for SAP B1 sync
        try:
            self.cursor.execute("SHOW INDEX FROM pick_lists WHERE Key_name = 'idx_absolute_entry'")
            if not self.cursor.fetchone():
                self.cursor.execute("CREATE INDEX idx_absolute_entry ON pick_lists(absolute_entry)")
                logger.info("✅ Added index on absolute_entry")
        except Exception as e:
            logger.error(f"❌ Error creating index: {str(e)}")
    
    def create_pick_list_lines_table(self):
        """Create the pick_list_lines table for SAP B1 compatibility"""
        logger.info("🔄 Creating pick_list_lines table...")
        
        if self.table_exists('pick_list_lines'):
            logger.info("⏭️ pick_list_lines table already exists")
            return
        
        create_sql = """
        CREATE TABLE pick_list_lines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_id INT NOT NULL,
            absolute_entry INT,
            line_number INT,
            order_entry INT,
            order_row_id INT DEFAULT 0,
            picked_quantity DECIMAL(15,4) DEFAULT 0.0,
            pick_status VARCHAR(20) DEFAULT 'ps_Open',
            released_quantity DECIMAL(15,4) DEFAULT 0.0,
            previously_released_quantity DECIMAL(15,4) DEFAULT 0.0,
            base_object_type INT,
            item_code VARCHAR(50),
            item_name VARCHAR(200),
            quantity DECIMAL(15,4),
            unit_of_measure VARCHAR(10),
            warehouse_code VARCHAR(10),
            bin_location VARCHAR(20),
            batch_number VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE,
            INDEX idx_pick_list_id (pick_list_id),
            INDEX idx_absolute_entry (absolute_entry),
            INDEX idx_item_code (item_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(create_sql)
            logger.info("✅ Created pick_list_lines table")
        except Exception as e:
            logger.error(f"❌ Error creating pick_list_lines table: {str(e)}")
    
    def create_pick_list_bin_allocations_table(self):
        """Create the pick_list_bin_allocations table for SAP B1 bin management"""
        logger.info("🔄 Creating pick_list_bin_allocations table...")
        
        if self.table_exists('pick_list_bin_allocations'):
            logger.info("⏭️ pick_list_bin_allocations table already exists")
            return
        
        create_sql = """
        CREATE TABLE pick_list_bin_allocations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_line_id INT NOT NULL,
            bin_abs_entry INT,
            quantity DECIMAL(15,4) NOT NULL,
            allow_negative_quantity VARCHAR(5) DEFAULT 'tNO',
            serial_and_batch_numbers_base_line INT DEFAULT 0,
            base_line_number INT,
            bin_code VARCHAR(20),
            bin_location VARCHAR(50),
            warehouse_code VARCHAR(10),
            picked_quantity DECIMAL(15,4) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_line_id) REFERENCES pick_list_lines(id) ON DELETE CASCADE,
            INDEX idx_pick_list_line_id (pick_list_line_id),
            INDEX idx_bin_code (bin_code),
            INDEX idx_warehouse_code (warehouse_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(create_sql)
            logger.info("✅ Created pick_list_bin_allocations table")
        except Exception as e:
            logger.error(f"❌ Error creating pick_list_bin_allocations table: {str(e)}")
    
    def update_existing_data(self):
        """Update existing pick list data with default values"""
        logger.info("🔄 Updating existing pick list data...")
        
        try:
            # Update existing records with default values
            update_sql = """
            UPDATE pick_lists 
            SET 
                name = COALESCE(name, CONCAT('PL-', id)),
                status = COALESCE(status, 'pending'),
                priority = COALESCE(priority, 'normal'),
                use_base_units = COALESCE(use_base_units, 'tNO'),
                total_items = COALESCE(total_items, 0),
                picked_items = COALESCE(picked_items, 0),
                object_type = COALESCE(object_type, '156')
            WHERE name IS NULL OR status IS NULL
            """
            
            self.cursor.execute(update_sql)
            affected_rows = self.cursor.rowcount
            if affected_rows > 0:
                logger.info(f"✅ Updated {affected_rows} existing pick list records")
            else:
                logger.info("⏭️ No existing records needed updating")
                
        except Exception as e:
            logger.error(f"❌ Error updating existing data: {str(e)}")
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting PickList MySQL Migration")
        logger.info("="*50)
        
        if not self.connect_mysql():
            logger.error("❌ Cannot proceed without MySQL connection")
            return False
        
        try:
            # Start transaction
            self.connection.begin()
            
            # Run migrations
            self.migrate_pick_lists_table()
            self.create_pick_list_lines_table()
            self.create_pick_list_bin_allocations_table()
            self.update_existing_data()
            
            # Commit transaction
            self.connection.commit()
            logger.info("✅ Migration completed successfully!")
            logger.info("="*50)
            
            # Show summary
            self.show_migration_summary()
            
            return True
            
        except Exception as e:
            # Rollback on error
            self.connection.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            logger.error("🔄 All changes have been rolled back")
            return False
        
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("🔌 MySQL connection closed")
    
    def show_migration_summary(self):
        """Show a summary of the migration results"""
        logger.info("📊 Migration Summary:")
        
        # Check pick_lists table structure
        self.cursor.execute("DESCRIBE pick_lists")
        columns = [row[0] for row in self.cursor.fetchall()]
        logger.info(f"   pick_lists table: {len(columns)} columns")
        
        # Check pick_list_lines table
        if self.table_exists('pick_list_lines'):
            self.cursor.execute("SELECT COUNT(*) FROM pick_list_lines")
            count = self.cursor.fetchone()[0]
            logger.info(f"   pick_list_lines table: {count} records")
        
        # Check pick_list_bin_allocations table
        if self.table_exists('pick_list_bin_allocations'):
            self.cursor.execute("SELECT COUNT(*) FROM pick_list_bin_allocations")
            count = self.cursor.fetchone()[0]
            logger.info(f"   pick_list_bin_allocations table: {count} records")
        
        # Check total pick lists
        self.cursor.execute("SELECT COUNT(*) FROM pick_lists")
        total_pick_lists = self.cursor.fetchone()[0]
        logger.info(f"   Total pick lists: {total_pick_lists}")

def main():
    """Main function to run the migration"""
    print("=" * 60)
    print("  MYSQL PICKLIST MIGRATION SCRIPT")
    print("  Updates PickList tables for SAP B1 compatibility")
    print("=" * 60)
    
    migration = PickListMigration()
    
    # Run migration
    success = migration.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Your MySQL database is now ready for SAP B1 PickList integration")
    else:
        print("\n❌ Migration failed!")
        print("Please check the logs above for error details")
    
    return success

if __name__ == "__main__":
    main()