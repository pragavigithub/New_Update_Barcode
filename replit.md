# Warehouse Management System (WMS)

## Overview
A Flask-based warehouse management system with SAP integration for barcode scanning, inventory management, goods receipt, pick lists, and inventory transfers.

## Project Architecture
- **Backend**: Flask web application
- **Database**: SQLite (fallback from MySQL configuration)
- **Frontend**: Server-side rendering with Jinja2 templates
- **Integration**: SAP API integration for warehouse operations
- **Authentication**: Flask-Login for user management

## Key Features
- User authentication and role-based access control
- Goods Receipt Purchase Order (GRPO) management
- Inventory transfer requests
- Pick list management
- Barcode scanning integration
- Branch management
- Quality control dashboard

## Recent Changes
- **2025-08-12**: Successfully migrated from Replit Agent to Replit environment
- Database connection configured to fallback to SQLite when MySQL unavailable
- Security configurations updated for production readiness
- MySQL migration file completely updated to align with current models
- All schema mismatches between models and MySQL migration file resolved
- Added missing tables: inventory_counts, inventory_count_items, barcode_labels, bin_locations
- Fixed GRPO and inventory transfer table schemas to match current implementation
- **2025-08-13**: Fixed QR code generation issue by adding missing column detection
- Added comprehensive column migration for `qr_code_labels` table including `item_name`, `po_number`, `bin_code`
- Migration file now handles existing databases with missing columns automatically
- Fixed legacy MySQL fields `label_number` and `qr_code_data` that were causing NOT NULL constraint errors
- Updated migration to handle all legacy QR code table schemas from previous implementations
- Enhanced GRPO module: "+Add Item" buttons are now disabled for closed PO lines and enabled for open lines
- Added status-based button management for better user experience and data integrity
- **2025-08-14**: Enhanced Picklist module with Sales Order integration
- Added SalesOrder and SalesOrderLine models to enable enhanced picklist functionality
- Implemented SAP B1 Sales Order API integration functions for fetching and syncing sales orders
- Updated picklist routes to enhance lines with Sales Order data including ItemCode, Customer details, and quantities
- Added Sales Order tables to MySQL migration file with proper indexing and foreign keys
- Enhanced picklist lines now display item details from matching Sales Orders based on OrderEntry and LineNum
- **2025-08-14**: Successfully migrated from Replit Agent to Replit environment
- Configured PostgreSQL database for Replit cloud environment
- **Enhanced Picklist module**: Fixed ItemCode display issue in Pick List Items table
- Updated template to show ItemCode instead of OrderEntry number for better user experience
- Added ItemDescription and Customer details in enhanced picklist lines
- Improved bin allocation display to show warehouse details even when no bin allocations exist
- Confirmed picklist enhancement displays ItemCode by matching OrderEntry to Sales Order DocEntry and OrderRowID to LineNum

## User Preferences
- None specified yet

## Environment Variables
- `SESSION_SECRET`: Flask session secret key
- `DATABASE_URL`: Database connection URL
- `MYSQL_*`: MySQL configuration variables (optional)
- SAP integration variables (as needed)

## Security Notes
- Client/server separation maintained
- No hardcoded secrets in code
- Environment variable based configuration
- Proper password hashing implemented