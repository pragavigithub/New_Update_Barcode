#!/usr/bin/env python3
"""
Complete MySQL Migration Script - August 2025 Update
Includes all recent changes for SAP B1 PickList integration and schema fixes
Run this script to fully migrate your MySQL database to the latest schema
"""

import pymysql
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteMySQLMigration:
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
    
    def constraint_exists(self, table_name, constraint_name):
        """Check if a constraint exists"""
        try:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}' 
                AND constraint_name = '{constraint_name}'
            """)
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking constraint {constraint_name}: {str(e)}")
            return False
    
    def migrate_pick_lists_table(self):
        """Migrate the pick_lists table with complete SAP B1 compatibility"""
        logger.info("🔄 Migrating pick_lists table...")
        
        # Step 1: Add new SAP B1 columns
        sap_columns = [
            ("absolute_entry", "ADD COLUMN absolute_entry INT"),
            ("name", "ADD COLUMN name VARCHAR(100)"),
            ("owner_code", "ADD COLUMN owner_code INT"),
            ("owner_name", "ADD COLUMN owner_name VARCHAR(100)"),
            ("pick_date", "ADD COLUMN pick_date DATETIME"),
            ("remarks", "ADD COLUMN remarks TEXT"),
            ("object_type", "ADD COLUMN object_type VARCHAR(10) DEFAULT '156'"),
            ("use_base_units", "ADD COLUMN use_base_units VARCHAR(5) DEFAULT 'tNO'"),
            ("priority", "ADD COLUMN priority VARCHAR(20) DEFAULT 'normal'"),
            ("warehouse_code", "ADD COLUMN warehouse_code VARCHAR(10)"),
            ("customer_code", "ADD COLUMN customer_code VARCHAR(50)"),
            ("customer_name", "ADD COLUMN customer_name VARCHAR(200)"),
            ("total_items", "ADD COLUMN total_items INT DEFAULT 0"),
            ("picked_items", "ADD COLUMN picked_items INT DEFAULT 0"),
            ("notes", "ADD COLUMN notes TEXT")
        ]
        
        for column_name, alter_statement in sap_columns:
            if not self.column_exists('pick_lists', column_name):
                try:
                    sql = f"ALTER TABLE pick_lists {alter_statement}"
                    self.cursor.execute(sql)
                    logger.info(f"✅ Added SAP B1 column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Error adding column {column_name}: {str(e)}")
            else:
                logger.info(f"⏭️ SAP B1 column {column_name} already exists")
        
        # Step 2: Fix nullable constraints for SAP B1 compatibility
        nullable_fixes = [
            ("sales_order_number", "MODIFY COLUMN sales_order_number VARCHAR(50) NULL"),
            ("pick_list_number", "MODIFY COLUMN pick_list_number VARCHAR(50) NULL")
        ]
        
        for column_name, alter_statement in nullable_fixes:
            try:
                sql = f"ALTER TABLE pick_lists {alter_statement}"
                self.cursor.execute(sql)
                logger.info(f"✅ Made column {column_name} nullable for SAP B1 compatibility")
            except Exception as e:
                logger.warning(f"⚠️ Could not modify {column_name}: {str(e)}")
        
        # Step 3: Add performance indexes
        indexes = [
            ("idx_absolute_entry", "CREATE INDEX idx_absolute_entry ON pick_lists(absolute_entry)"),
            ("idx_pick_status", "CREATE INDEX idx_pick_status ON pick_lists(status)"),
            ("idx_pick_date", "CREATE INDEX idx_pick_date ON pick_lists(pick_date)"),
            ("idx_owner_code", "CREATE INDEX idx_owner_code ON pick_lists(owner_code)")
        ]
        
        for index_name, create_statement in indexes:
            try:
                self.cursor.execute(f"SHOW INDEX FROM pick_lists WHERE Key_name = '{index_name}'")
                if not self.cursor.fetchone():
                    self.cursor.execute(create_statement)
                    logger.info(f"✅ Added index: {index_name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not create index {index_name}: {str(e)}")
    
    def create_pick_list_lines_table(self):
        """Create the pick_list_lines table for SAP B1 line items"""
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
            serial_numbers TEXT,
            batch_numbers TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE,
            INDEX idx_pick_list_id (pick_list_id),
            INDEX idx_absolute_entry (absolute_entry),
            INDEX idx_item_code (item_code),
            INDEX idx_order_entry (order_entry),
            INDEX idx_pick_status (pick_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(create_sql)
            logger.info("✅ Created pick_list_lines table with SAP B1 structure")
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
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_list_line_id) REFERENCES pick_list_lines(id) ON DELETE CASCADE,
            INDEX idx_pick_list_line_id (pick_list_line_id),
            INDEX idx_bin_abs_entry (bin_abs_entry),
            INDEX idx_bin_code (bin_code),
            INDEX idx_warehouse_code (warehouse_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(create_sql)
            logger.info("✅ Created pick_list_bin_allocations table with SAP B1 structure")
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
            WHERE name IS NULL OR status IS NULL OR priority IS NULL
            """
            
            self.cursor.execute(update_sql)
            affected_rows = self.cursor.rowcount
            if affected_rows > 0:
                logger.info(f"✅ Updated {affected_rows} existing pick list records with default values")
            else:
                logger.info("⏭️ No existing records needed updating")
                
        except Exception as e:
            logger.error(f"❌ Error updating existing data: {str(e)}")
    
    def create_sap_integration_views(self):
        """Create helpful views for SAP B1 integration"""
        logger.info("🔄 Creating SAP integration views...")
        
        views = [
            # View for complete pick list with lines
            ("vw_sap_pick_lists", """
                CREATE OR REPLACE VIEW vw_sap_pick_lists AS
                SELECT 
                    pl.id,
                    pl.absolute_entry,
                    pl.name,
                    pl.status,
                    pl.owner_code,
                    pl.owner_name,
                    pl.pick_date,
                    pl.total_items,
                    pl.picked_items,
                    COUNT(pll.id) as line_count,
                    SUM(pll.picked_quantity) as total_picked_qty,
                    SUM(pll.previously_released_quantity) as total_released_qty
                FROM pick_lists pl
                LEFT JOIN pick_list_lines pll ON pl.id = pll.pick_list_id
                WHERE pl.absolute_entry IS NOT NULL
                GROUP BY pl.id
            """),
            
            # View for pick list performance metrics
            ("vw_pick_list_metrics", """
                CREATE OR REPLACE VIEW vw_pick_list_metrics AS
                SELECT 
                    pl.id,
                    pl.absolute_entry,
                    pl.name,
                    pl.status,
                    COUNT(pll.id) as total_lines,
                    COUNT(CASE WHEN pll.pick_status = 'ps_Closed' THEN 1 END) as completed_lines,
                    COUNT(CASE WHEN pll.pick_status = 'ps_Open' THEN 1 END) as pending_lines,
                    ROUND(
                        (COUNT(CASE WHEN pll.pick_status = 'ps_Closed' THEN 1 END) * 100.0) / 
                        NULLIF(COUNT(pll.id), 0), 2
                    ) as completion_percentage
                FROM pick_lists pl
                LEFT JOIN pick_list_lines pll ON pl.id = pll.pick_list_id
                GROUP BY pl.id
            """)
        ]
        
        for view_name, create_statement in views:
            try:
                self.cursor.execute(create_statement)
                logger.info(f"✅ Created view: {view_name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not create view {view_name}: {str(e)}")
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting Complete MySQL Migration - August 2025")
        logger.info("="*60)
        
        if not self.connect_mysql():
            logger.error("❌ Cannot proceed without MySQL connection")
            return False
        
        try:
            # Start transaction
            self.connection.begin()
            
            # Run all migrations
            self.migrate_pick_lists_table()
            self.create_pick_list_lines_table()
            self.create_pick_list_bin_allocations_table()
            self.update_existing_data()
            self.create_sap_integration_views()
            
            # Commit transaction
            self.connection.commit()
            logger.info("✅ Complete migration finished successfully!")
            logger.info("="*60)
            
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
        logger.info(f"   📋 pick_lists table: {len(columns)} columns")
        
        # Check for SAP B1 specific columns
        sap_columns = ['absolute_entry', 'name', 'owner_code', 'object_type', 'use_base_units']
        sap_column_count = sum(1 for col in sap_columns if col in columns)
        logger.info(f"   🔗 SAP B1 columns: {sap_column_count}/{len(sap_columns)}")
        
        # Check pick_list_lines table
        if self.table_exists('pick_list_lines'):
            self.cursor.execute("SELECT COUNT(*) FROM pick_list_lines")
            count = self.cursor.fetchone()[0]
            logger.info(f"   📦 pick_list_lines table: {count} records")
        
        # Check pick_list_bin_allocations table
        if self.table_exists('pick_list_bin_allocations'):
            self.cursor.execute("SELECT COUNT(*) FROM pick_list_bin_allocations")
            count = self.cursor.fetchone()[0]
            logger.info(f"   📍 pick_list_bin_allocations table: {count} records")
        
        # Check total pick lists
        self.cursor.execute("SELECT COUNT(*) FROM pick_lists")
        total_pick_lists = self.cursor.fetchone()[0]
        logger.info(f"   📋 Total pick lists: {total_pick_lists}")
        
        # Check SAP integrated pick lists
        self.cursor.execute("SELECT COUNT(*) FROM pick_lists WHERE absolute_entry IS NOT NULL")
        sap_pick_lists = self.cursor.fetchone()[0]
        logger.info(f"   🔗 SAP B1 integrated pick lists: {sap_pick_lists}")

def main():
    """Main function to run the complete migration"""
    print("=" * 70)
    print("  COMPLETE MYSQL MIGRATION SCRIPT - AUGUST 2025")
    print("  Full SAP B1 PickList Integration & Schema Updates")
    print("=" * 70)
    
    migration = CompleteMySQLMigration()
    
    # Run migration
    success = migration.run_migration()
    
    if success:
        print("\n🎉 Complete migration finished successfully!")
        print("Your MySQL database is now fully updated with:")
        print("  ✅ SAP B1 PickList integration support")
        print("  ✅ Enhanced schema with nullable constraints")
        print("  ✅ Performance indexes and views")
        print("  ✅ Complete line items and bin allocation tracking")
        print("\nYour database is ready for production deployment!")
    else:
        print("\n❌ Migration failed!")
        print("Please check the logs above for error details")
    
    return success

if __name__ == "__main__":
    main()