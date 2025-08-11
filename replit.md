# Warehouse Management System (WMS)

## Project Overview
A comprehensive warehouse management system with SAP B1 integration, built with Flask and PostgreSQL. This system handles goods receipt, inventory transfers, pick lists, inventory counting, bin scanning, QR code label printing, and quality control operations.

## Architecture
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (migrated from MySQL/SQLite for Replit compatibility)
- **Authentication**: Flask-Login with role-based permissions
- **External Integration**: SAP Business One via REST API
- **Frontend**: Jinja2 templates with Bootstrap UI
- **Deployment**: Gunicorn WSGI server on Replit

## Key Features
1. **User Management**: Role-based access control (admin, manager, user, qc)
2. **GRPO (Goods Receipt PO)**: Purchase order receipt processing
3. **Inventory Transfer**: Item movement between locations
4. **Pick List Management**: Order fulfillment operations
5. **Inventory Counting**: Stock count reconciliation
6. **Bin Scanning**: Barcode scanning for warehouse locations
7. **QR Code Labels**: Label generation and printing
8. **Quality Control Dashboard**: QC workflow management
9. **SAP B1 Integration**: Real-time data synchronization

## Database Schema
- **Users**: Authentication and role management
- **Branches**: Multi-location support
- **GRPO Documents**: Purchase receipt records
- **Inventory Transfers**: Stock movement tracking
- **Pick Lists**: Order picking workflows
- **Inventory Counts**: Stock counting operations
- **Bin Scanning Logs**: Location scanning history
- **QR Code Labels**: Label generation tracking

## Security Features
- Password hashing with Werkzeug
- Session-based authentication
- Role-based access control
- SQL injection protection via SQLAlchemy
- CSRF protection ready

## Replit Migration Status
- [x] PostgreSQL database provisioned
- [x] Database configuration updated for Replit
- [x] Gunicorn workflow configured
- [x] Environment variables structured
- [x] Application testing and validation
- [x] QR code library enhanced with qrcode[pil]
- [x] Dual database support maintained (MySQL priority, PostgreSQL fallback)

## User Preferences
- **Database Priority**: MySQL for local development, PostgreSQL for cloud deployment
- **Development Environment**: Dual database support to maintain local machine MySQL sync
- **Integration Focus**: SAP B1 integration with batch management and warehouse operations

## Recent Changes
- **2025-08-11**: Successfully migrated from Replit Agent to standard Replit environment
- **2025-08-11**: Updated PickList models to match SAP B1 API structure exactly (Absoluteentry, Name, OwnerCode, PickListsLines, DocumentLinesBinAllocations)
- **2025-08-11**: Added comprehensive SAP B1 PickList integration with get_pick_lists(), get_pick_list_by_id(), and update_pick_list_status()
- **2025-08-11**: Enhanced PickList routes with search, pagination, and SAP B1 synchronization
- **2025-08-11**: Added /api/sync-sap-pick-lists endpoint for real-time SAP B1 data synchronization
- **2025-08-11**: Implemented PickListLine and PickListBinAllocation models for full SAP B1 compatibility
- **2025-08-07**: Successfully completed migration from Replit Agent to standard Replit environment
- **2025-08-07**: Added comprehensive search and pagination functionality to GRN (GRPO) screen
- **2025-08-07**: Added comprehensive search and pagination functionality to Inventory Transfer screen
- **2025-08-07**: Enhanced UI with Bootstrap-styled search forms and pagination controls
- **2025-08-07**: Implemented 10 records per page pagination with navigation controls and result counters
- **2025-08-07**: Added search functionality for PO numbers, status, SAP documents, vendor names, and warehouse codes
- **2025-08-07**: PostgreSQL database fully configured and operational in Replit environment
- **2025-08-07**: Maintained MySQL database synchronization for local development environments
- **2025-08-04**: Enhanced QR code system with qrcode[pil] library for better compatibility
- **2025-08-04**: Added `/api/print-qr-label` endpoint with format "SO123456 | ItemCode: 98765 | Date: 2025-08-04"
- **2025-08-04**: Maintained MySQL priority configuration for local development
- **2025-08-04**: Configured PostgreSQL fallback for Replit cloud deployment
- **2025-08-04**: Fixed "Add Remaining" button functionality in inventory transfers
- **2025-08-04**: Implemented `/api/get-batch-numbers` endpoint for SAP B1 batch integration
- **2025-08-04**: Enhanced dual database support with improved connection testing
- **2025-08-04**: Created MySQL setup tools and comprehensive documentation
- **2025-08-04**: Fixed QR code generation issues and database model constructor compatibility
- **2025-08-03**: Fixed inventory transfer cascading dropdowns and manual entry
- **2025-08-03**: Implemented QR/barcode generation with C# ZXing.QRCode compatibility