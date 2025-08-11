#!/usr/bin/env python3
"""
Quick Runner for MySQL PickList Migration
This script sets up the environment and runs the migration
"""

import os
import sys
from mysql_picklist_migration import main as run_migration

def setup_environment():
    """Setup environment variables for MySQL connection"""
    print("🔧 Setting up MySQL environment...")
    
    # Default MySQL configuration for local development
    mysql_env = {
        'MYSQL_HOST': 'localhost',
        'MYSQL_PORT': '3306',
        'MYSQL_USER': 'root',
        'MYSQL_PASSWORD': '',  # Set your MySQL password
        'MYSQL_DATABASE': 'warehouse_db'  # Set your database name
    }
    
    # Override with existing environment variables if they exist
    for key, default_value in mysql_env.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    print(f"MySQL Host: {os.environ['MYSQL_HOST']}")
    print(f"MySQL Port: {os.environ['MYSQL_PORT']}")
    print(f"MySQL User: {os.environ['MYSQL_USER']}")
    print(f"MySQL Database: {os.environ['MYSQL_DATABASE']}")
    print()

def main():
    """Main function"""
    print("🚀 MySQL PickList Migration Runner")
    print("=" * 40)
    
    # Setup environment
    setup_environment()
    
    # Confirm before proceeding
    response = input("Continue with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled by user")
        return False
    
    # Run migration
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Your PickList tables are now SAP B1 compatible")
    else:
        print("\n❌ Migration failed!")
        print("Check the error messages above")
    
    return success

if __name__ == "__main__":
    main()