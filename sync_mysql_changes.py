#!/usr/bin/env python3
"""
MySQL Database Synchronization Utility for WMS
Syncs database changes between PostgreSQL (Replit) and MySQL (Local Development)
"""
import os
import sys
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import pymysql

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSyncManager:
    def __init__(self):
        """Initialize database sync manager with PostgreSQL and MySQL connections"""
        self.pg_engine = None
        self.mysql_engine = None
        self.setup_connections()
    
    def setup_connections(self):
        """Setup database connections"""
        try:
            # PostgreSQL connection (Replit)
            pg_url = os.environ.get("DATABASE_URL")
            if pg_url:
                self.pg_engine = create_engine(pg_url)
                logger.info("✅ PostgreSQL connection established")
            else:
                logger.error("❌ No DATABASE_URL found for PostgreSQL")
                return False
            
            # MySQL connection (Local development)
            mysql_config = {
                'host': os.environ.get('MYSQL_HOST', 'localhost'),
                'port': int(os.environ.get('MYSQL_PORT', '3306')),
                'user': os.environ.get('MYSQL_USER', 'root'),
                'password': os.environ.get('MYSQL_PASSWORD', 'root@123'),
                'database': os.environ.get('MYSQL_DATABASE', 'wms_db_dev')
            }
            
            mysql_url = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
            self.mysql_engine = create_engine(mysql_url, connect_args={'connect_timeout': 10})
            
            # Test MySQL connection
            with self.mysql_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ MySQL connection established")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ MySQL connection failed: {e}")
            logger.info("💡 Running in PostgreSQL-only mode")
            return False
    
    def sync_table_structure(self, table_name):
        """Sync table structure from PostgreSQL to MySQL"""
        if not self.mysql_engine:
            logger.info("MySQL not available, skipping structure sync")
            return
        
        try:
            # Get PostgreSQL table structure
            pg_metadata = MetaData()
            pg_metadata.bind = self.pg_engine
            pg_metadata.reflect(only=[table_name])
            
            if table_name not in pg_metadata.tables:
                logger.warning(f"Table {table_name} not found in PostgreSQL")
                return
            
            pg_table = pg_metadata.tables[table_name]
            
            # Generate MySQL CREATE TABLE statement
            mysql_ddl = self._generate_mysql_ddl(pg_table)
            
            # Execute on MySQL
            with self.mysql_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.execute(text(mysql_ddl))
                conn.commit()
            
            logger.info(f"✅ Table {table_name} structure synced to MySQL")
            
        except Exception as e:
            logger.error(f"❌ Error syncing table structure for {table_name}: {e}")
    
    def sync_table_data(self, table_name, limit=1000):
        """Sync table data from PostgreSQL to MySQL"""
        if not self.mysql_engine:
            logger.info("MySQL not available, skipping data sync")
            return
        
        try:
            # Get data from PostgreSQL
            with self.pg_engine.connect() as pg_conn:
                result = pg_conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                rows = result.fetchall()
                columns = result.keys()
            
            if not rows:
                logger.info(f"No data to sync for table {table_name}")
                return
            
            # Clear MySQL table and insert data
            with self.mysql_engine.connect() as mysql_conn:
                mysql_conn.execute(text(f"DELETE FROM {table_name}"))
                
                # Prepare insert statement
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Insert rows
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    mysql_conn.execute(text(insert_sql), row_dict)
                
                mysql_conn.commit()
            
            logger.info(f"✅ Synced {len(rows)} rows to MySQL table {table_name}")
            
        except Exception as e:
            logger.error(f"❌ Error syncing data for {table_name}: {e}")
    
    def _generate_mysql_ddl(self, pg_table):
        """Generate MySQL-compatible CREATE TABLE statement from PostgreSQL table"""
        columns = []
        
        for column in pg_table.columns:
            col_def = f"`{column.name}` "
            
            # Map PostgreSQL types to MySQL types
            pg_type = str(column.type).upper()
            
            if 'INTEGER' in pg_type:
                col_def += 'INT'
            elif 'VARCHAR' in pg_type:
                col_def += str(column.type)
            elif 'TEXT' in pg_type:
                col_def += 'TEXT'
            elif 'DATETIME' in pg_type:
                col_def += 'DATETIME'
            elif 'BOOLEAN' in pg_type:
                col_def += 'BOOLEAN'
            elif 'FLOAT' in pg_type:
                col_def += 'FLOAT'
            else:
                col_def += 'TEXT'  # Default fallback
            
            if not column.nullable:
                col_def += ' NOT NULL'
            
            if column.default is not None:
                if hasattr(column.default, 'arg'):
                    if callable(column.default.arg):
                        # Handle functions like datetime.utcnow
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    else:
                        col_def += f" DEFAULT '{column.default.arg}'"
            
            if column.primary_key:
                col_def += ' PRIMARY KEY'
                if 'INTEGER' in pg_type:
                    col_def += ' AUTO_INCREMENT'
            
            columns.append(col_def)
        
        return f"CREATE TABLE {pg_table.name} ({', '.join(columns)})"
    
    def sync_all_tables(self):
        """Sync all WMS tables"""
        tables_to_sync = [
            'users',
            'branches', 
            'grpo_documents',
            'grpo_items',
            'inventory_transfers',
            'inventory_transfer_items',
            'pick_lists',
            'pick_list_items',
            'inventory_counts',
            'inventory_count_items',
            'bin_scanning_logs',
            'barcode_labels',
            'qr_code_labels'
        ]
        
        logger.info("🔄 Starting full database sync...")
        
        for table in tables_to_sync:
            logger.info(f"Syncing table: {table}")
            self.sync_table_structure(table)
            self.sync_table_data(table)
        
        logger.info("✅ Database sync completed")
    
    def sync_recent_changes(self, hours=24):
        """Sync only recent changes from the last N hours"""
        if not self.mysql_engine:
            logger.info("MySQL not available, skipping recent changes sync")
            return
        
        tables_with_timestamps = [
            'grpo_documents',
            'grpo_items',
            'inventory_transfers',
            'inventory_transfer_items',
            'users'
        ]
        
        logger.info(f"🔄 Syncing changes from last {hours} hours...")
        
        for table in tables_with_timestamps:
            try:
                # Get recent records from PostgreSQL
                with self.pg_engine.connect() as pg_conn:
                    result = pg_conn.execute(text(f"""
                        SELECT * FROM {table} 
                        WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                        OR updated_at >= NOW() - INTERVAL '{hours} hours'
                    """))
                    rows = result.fetchall()
                    columns = result.keys()
                
                if rows:
                    # Update MySQL with recent changes
                    with self.mysql_engine.connect() as mysql_conn:
                        for row in rows:
                            row_dict = dict(zip(columns, row))
                            
                            # Use REPLACE INTO to handle updates
                            placeholders = ", ".join([f":{col}" for col in columns])
                            replace_sql = f"REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                            mysql_conn.execute(text(replace_sql), row_dict)
                        
                        mysql_conn.commit()
                    
                    logger.info(f"✅ Synced {len(rows)} recent changes for {table}")
                
            except Exception as e:
                logger.error(f"❌ Error syncing recent changes for {table}: {e}")

def main():
    """Main function to run database sync"""
    sync_manager = DatabaseSyncManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'full':
            sync_manager.sync_all_tables()
        elif command == 'recent':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            sync_manager.sync_recent_changes(hours)
        elif command == 'table':
            if len(sys.argv) > 2:
                table_name = sys.argv[2]
                sync_manager.sync_table_structure(table_name)
                sync_manager.sync_table_data(table_name)
            else:
                print("Usage: python sync_mysql_changes.py table <table_name>")
        else:
            print("Usage: python sync_mysql_changes.py [full|recent [hours]|table <name>]")
    else:
        # Default: sync recent changes
        sync_manager.sync_recent_changes()

if __name__ == "__main__":
    main()