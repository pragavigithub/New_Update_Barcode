#!/usr/bin/env python3
"""
MySQL PickList Migration Script - August 2025 Update
Complete migration for SAP B1 compatible PickList structure with bin allocations

Based on SAP B1 API structure:
- PickLists with Absoluteentry, Name, OwnerCode, PickListsLines
- DocumentLinesBinAllocations with detailed bin tracking

Run this script to update your MySQL database schema to match the current WMS models.
"""

import os
import sys
import logging
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MySQLPickListMigration:
    def __init__(self):
        self.connection = None
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.port = int(os.getenv('MYSQL_PORT', 3306))
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.database = os.getenv('MYSQL_DATABASE', 'wms_db_dev')

    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor,
                autocommit=False
            )
            logger.info(f"✅ Connected to MySQL database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MySQL: {e}")
            return False

    def execute_query(self, query, params=None):
        """Execute a query with proper error handling"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            logger.error(f"Query: {query}")
            raise

    def column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        query = """
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """
        result = self.execute_query(query, [self.database, table_name, column_name])
        return result[0]['count'] > 0

    def table_exists(self, table_name):
        """Check if a table exists"""
        query = """
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        result = self.execute_query(query, [self.database, table_name])
        return result[0]['count'] > 0

    def migrate_pick_lists_table(self):
        """Migrate pick_lists table with SAP B1 compatible structure"""
        logger.info("🔄 Migrating pick_lists table...")
        
        # List of columns to add with their definitions
        new_columns = [
            ('absolute_entry', 'INT NULL COMMENT "SAP B1 Absoluteentry"'),
            ('name', 'VARCHAR(50) NOT NULL DEFAULT "" COMMENT "SAP B1 Name field"'),
            ('owner_code', 'INT NULL COMMENT "SAP B1 OwnerCode"'),
            ('owner_name', 'VARCHAR(100) NULL COMMENT "SAP B1 OwnerName"'),
            ('pick_date', 'DATETIME NULL COMMENT "SAP B1 PickDate"'),
            ('remarks', 'TEXT NULL COMMENT "SAP B1 Remarks"'),
            ('object_type', 'VARCHAR(10) NULL DEFAULT "156" COMMENT "SAP B1 ObjectType"'),
            ('use_base_units', 'VARCHAR(5) NULL DEFAULT "tNO" COMMENT "SAP B1 UseBaseUnits"'),
            ('priority', 'VARCHAR(10) NULL DEFAULT "normal" COMMENT "Pick list priority"'),
            ('warehouse_code', 'VARCHAR(10) NULL COMMENT "Warehouse code"'),
            ('customer_code', 'VARCHAR(20) NULL COMMENT "Customer code"'),
            ('customer_name', 'VARCHAR(100) NULL COMMENT "Customer name"'),
            ('total_items', 'INT NULL DEFAULT 0 COMMENT "Total items count"'),
            ('picked_items', 'INT NULL DEFAULT 0 COMMENT "Picked items count"'),
            ('notes', 'TEXT NULL COMMENT "Additional notes"')
        ]
        
        # Add missing columns
        for column_name, column_def in new_columns:
            if not self.column_exists('pick_lists', column_name):
                query = f"ALTER TABLE pick_lists ADD COLUMN {column_name} {column_def}"
                self.execute_query(query)
                logger.info(f"  ✅ Added column: {column_name}")
            else:
                logger.info(f"  ⏭️  Column exists: {column_name}")

        # Make legacy columns nullable for SAP B1 compatibility
        nullable_columns = [
            ('sales_order_number', 'VARCHAR(20) NULL'),
            ('pick_list_number', 'VARCHAR(20) NULL')
        ]
        
        for column_name, column_def in nullable_columns:
            if self.column_exists('pick_lists', column_name):
                query = f"ALTER TABLE pick_lists MODIFY COLUMN {column_name} {column_def}"
                self.execute_query(query)
                logger.info(f"  ✅ Modified column to nullable: {column_name}")

    def create_pick_list_lines_table(self):
        """Create pick_list_lines table based on SAP B1 PickListsLines structure"""
        logger.info("🔄 Creating pick_list_lines table...")
        
        if self.table_exists('pick_list_lines'):
            logger.info("  ⏭️  Table already exists: pick_list_lines")
            return

        create_query = """
        CREATE TABLE pick_list_lines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_id INT NOT NULL,
            
            -- SAP B1 PickListsLines fields
            absolute_entry INT NULL COMMENT 'SAP B1 AbsoluteEntry',
            line_number INT NOT NULL COMMENT 'SAP B1 LineNumber',
            order_entry INT NULL COMMENT 'SAP B1 OrderEntry',
            order_row_id INT NULL COMMENT 'SAP B1 OrderRowID',
            picked_quantity DECIMAL(18,6) NULL DEFAULT 0 COMMENT 'SAP B1 PickedQuantity',
            pick_status VARCHAR(20) NULL DEFAULT 'ps_Open' COMMENT 'SAP B1 PickStatus',
            released_quantity DECIMAL(18,6) NULL DEFAULT 0 COMMENT 'SAP B1 ReleasedQuantity',
            previously_released_quantity DECIMAL(18,6) NULL DEFAULT 0 COMMENT 'SAP B1 PreviouslyReleasedQuantity',
            base_object_type INT NULL DEFAULT 17 COMMENT 'SAP B1 BaseObjectType',
            
            -- WMS specific fields
            item_code VARCHAR(50) NULL COMMENT 'Item code',
            item_name VARCHAR(200) NULL COMMENT 'Item description',
            unit_of_measure VARCHAR(10) NULL COMMENT 'Unit of measure',
            serial_numbers TEXT NULL COMMENT 'JSON array of serial numbers',
            batch_numbers TEXT NULL COMMENT 'JSON array of batch numbers',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign key constraint
            FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE,
            
            -- Indexes for performance
            INDEX idx_pick_list_lines_pick_list_id (pick_list_id),
            INDEX idx_pick_list_lines_absolute_entry (absolute_entry),
            INDEX idx_pick_list_lines_line_number (line_number),
            INDEX idx_pick_list_lines_item_code (item_code),
            INDEX idx_pick_list_lines_pick_status (pick_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='SAP B1 compatible pick list lines based on PickListsLines structure'
        """
        
        self.execute_query(create_query)
        logger.info("  ✅ Created table: pick_list_lines")

    def create_pick_list_bin_allocations_table(self):
        """Create pick_list_bin_allocations table based on SAP B1 DocumentLinesBinAllocations"""
        logger.info("🔄 Creating pick_list_bin_allocations table...")
        
        if self.table_exists('pick_list_bin_allocations'):
            logger.info("  ⏭️  Table already exists: pick_list_bin_allocations")
            return

        create_query = """
        CREATE TABLE pick_list_bin_allocations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pick_list_line_id INT NOT NULL,
            
            -- SAP B1 DocumentLinesBinAllocations fields
            bin_abs_entry INT NULL COMMENT 'SAP B1 BinAbsEntry',
            quantity DECIMAL(18,6) NOT NULL COMMENT 'SAP B1 Quantity',
            allow_negative_quantity VARCHAR(5) NULL DEFAULT 'tNO' COMMENT 'SAP B1 AllowNegativeQuantity',
            serial_and_batch_numbers_base_line INT NULL DEFAULT 0 COMMENT 'SAP B1 SerialAndBatchNumbersBaseLine',
            base_line_number INT NULL COMMENT 'SAP B1 BaseLineNumber',
            
            -- WMS specific fields
            bin_code VARCHAR(20) NULL COMMENT 'Bin code',
            bin_location VARCHAR(50) NULL COMMENT 'Bin location description',
            warehouse_code VARCHAR(10) NULL COMMENT 'Warehouse code',
            picked_quantity DECIMAL(18,6) NULL DEFAULT 0 COMMENT 'Actually picked quantity',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign key constraint
            FOREIGN KEY (pick_list_line_id) REFERENCES pick_list_lines(id) ON DELETE CASCADE,
            
            -- Indexes for performance
            INDEX idx_pick_list_bin_allocations_line_id (pick_list_line_id),
            INDEX idx_pick_list_bin_allocations_bin_abs_entry (bin_abs_entry),
            INDEX idx_pick_list_bin_allocations_bin_code (bin_code),
            INDEX idx_pick_list_bin_allocations_warehouse_code (warehouse_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='SAP B1 compatible bin allocations based on DocumentLinesBinAllocations'
        """
        
        self.execute_query(create_query)
        logger.info("  ✅ Created table: pick_list_bin_allocations")

    def create_indexes_and_constraints(self):
        """Create additional indexes and constraints for performance"""
        logger.info("🔄 Creating indexes and constraints...")
        
        indexes = [
            # Pick lists indexes
            ("pick_lists", "idx_pick_lists_absolute_entry", "absolute_entry", True),
            ("pick_lists", "idx_pick_lists_name", "name", False),
            ("pick_lists", "idx_pick_lists_owner_code", "owner_code", False),
            ("pick_lists", "idx_pick_lists_status", "status", False),
            ("pick_lists", "idx_pick_lists_pick_date", "pick_date", False),
            ("pick_lists", "idx_pick_lists_warehouse_code", "warehouse_code", False),
            ("pick_lists", "idx_pick_lists_customer_code", "customer_code", False),
        ]
        
        for table, index_name, column, is_unique in indexes:
            try:
                unique_clause = "UNIQUE" if is_unique else ""
                query = f"CREATE {unique_clause} INDEX {index_name} ON {table} ({column})"
                self.execute_query(query)
                logger.info(f"  ✅ Created index: {index_name}")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    logger.info(f"  ⏭️  Index exists: {index_name}")
                else:
                    logger.error(f"  ❌ Failed to create index {index_name}: {e}")

    def create_views(self):
        """Create useful views for SAP B1 integration"""
        logger.info("🔄 Creating integration views...")
        
        # View for complete pick list data with line aggregations
        view_query = """
        CREATE OR REPLACE VIEW vw_sap_pick_lists AS
        SELECT 
            pl.id,
            pl.absolute_entry,
            pl.name,
            pl.owner_code,
            pl.owner_name,
            pl.pick_date,
            pl.status,
            pl.warehouse_code,
            pl.customer_code,
            pl.customer_name,
            pl.total_items,
            pl.picked_items,
            pl.created_at,
            pl.updated_at,
            COUNT(pll.id) as line_count,
            SUM(pll.picked_quantity) as total_picked_quantity,
            SUM(pll.released_quantity) as total_released_quantity,
            CASE 
                WHEN COUNT(pll.id) = 0 THEN 0
                ELSE (SUM(CASE WHEN pll.pick_status = 'ps_Closed' THEN 1 ELSE 0 END) * 100.0 / COUNT(pll.id))
            END as completion_percentage
        FROM pick_lists pl
        LEFT JOIN pick_list_lines pll ON pl.id = pll.pick_list_id
        GROUP BY pl.id, pl.absolute_entry, pl.name, pl.owner_code, pl.owner_name, 
                 pl.pick_date, pl.status, pl.warehouse_code, pl.customer_code, 
                 pl.customer_name, pl.total_items, pl.picked_items, 
                 pl.created_at, pl.updated_at
        """
        
        try:
            self.execute_query(view_query)
            logger.info("  ✅ Created view: vw_sap_pick_lists")
        except Exception as e:
            logger.error(f"  ❌ Failed to create view: {e}")

        # View for pick list metrics
        metrics_view_query = """
        CREATE OR REPLACE VIEW vw_pick_list_metrics AS
        SELECT 
            DATE(pl.pick_date) as pick_date,
            pl.warehouse_code,
            pl.status,
            COUNT(*) as pick_list_count,
            SUM(pl.total_items) as total_items,
            SUM(pl.picked_items) as total_picked_items,
            AVG(CASE WHEN pl.total_items > 0 THEN (pl.picked_items * 100.0 / pl.total_items) ELSE 0 END) as avg_completion_rate,
            SUM(CASE WHEN pl.status = 'ps_Closed' THEN 1 ELSE 0 END) as completed_pick_lists,
            SUM(CASE WHEN pl.status = 'ps_Open' THEN 1 ELSE 0 END) as open_pick_lists
        FROM pick_lists pl
        WHERE pl.pick_date IS NOT NULL
        GROUP BY DATE(pl.pick_date), pl.warehouse_code, pl.status
        ORDER BY pick_date DESC, warehouse_code
        """
        
        try:
            self.execute_query(metrics_view_query)
            logger.info("  ✅ Created view: vw_pick_list_metrics")
        except Exception as e:
            logger.error(f"  ❌ Failed to create metrics view: {e}")

    def run_migration(self):
        """Execute the complete migration process"""
        logger.info("🚀 Starting MySQL PickList Migration - August 2025")
        logger.info(f"Target Database: {self.database} on {self.host}:{self.port}")
        
        if not self.connect():
            return False
        
        try:
            # Start transaction
            logger.info("📄 Starting database transaction...")
            
            # Execute migration steps
            self.migrate_pick_lists_table()
            self.create_pick_list_lines_table()
            self.create_pick_list_bin_allocations_table()
            self.create_indexes_and_constraints()
            self.create_views()
            
            # Commit transaction
            self.connection.commit()
            logger.info("✅ Migration completed successfully!")
            
            # Show summary
            self.show_migration_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            self.connection.rollback()
            logger.info("🔄 Database rolled back to previous state")
            return False
            
        finally:
            if self.connection:
                self.connection.close()
                logger.info("🔌 Database connection closed")

    def show_migration_summary(self):
        """Display migration results summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("="*60)
        
        try:
            # Count records in each table
            tables = ['pick_lists', 'pick_list_lines', 'pick_list_bin_allocations']
            for table in tables:
                if self.table_exists(table):
                    count_result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                    count = count_result[0]['count']
                    logger.info(f"📋 {table}: {count} records")
                else:
                    logger.info(f"❌ {table}: Table not found")
            
            # Show pick list structure
            if self.table_exists('pick_lists'):
                columns = self.execute_query("DESCRIBE pick_lists")
                logger.info(f"\n📄 pick_lists table structure: {len(columns)} columns")
                sap_columns = [col['Field'] for col in columns if col['Field'] in 
                             ['absolute_entry', 'name', 'owner_code', 'pick_date', 'status']]
                logger.info(f"🔗 SAP B1 compatible columns: {len(sap_columns)}")
            
            logger.info("\n✅ Your database is now ready for SAP B1 PickList integration!")
            logger.info("🔄 Next steps:")
            logger.info("   1. Test the /pick_list page in your web application")
            logger.info("   2. Try the /api/sync-sap-pick-lists endpoint")
            logger.info("   3. Create test pick lists with line items and bin allocations")
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")

def main():
    """Main migration function"""
    print("🏗️  MySQL PickList Migration Tool - August 2025")
    print("=" * 60)
    
    # Check if we have required environment variables
    required_env = ['MYSQL_PASSWORD']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print("⚠️  Missing required environment variables:")
        for var in missing_env:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        print("Example:")
        print("export MYSQL_PASSWORD=your_password")
        print("export MYSQL_DATABASE=your_database")
        return
    
    # Run migration
    migration = MySQLPickListMigration()
    success = migration.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Your MySQL database now supports full SAP B1 PickList integration.")
    else:
        print("\n❌ Migration failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()