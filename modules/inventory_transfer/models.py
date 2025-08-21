"""
Inventory Transfer Models
Contains all models related to inventory transfers between warehouses/bins
"""
from app import db
from datetime import datetime
from modules.shared.models import User

class InventoryTransfer(db.Model):
    """Main inventory transfer document header"""
    __tablename__ = 'inventory_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_request_number = db.Column(db.String(50), nullable=False)
    sap_document_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='draft')  # draft, submitted, qc_approved, posted, rejected, reopened
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    qc_approver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    qc_approved_at = db.Column(db.DateTime)
    qc_notes = db.Column(db.Text)
    from_warehouse = db.Column(db.String(10))
    to_warehouse = db.Column(db.String(10))
    transfer_type = db.Column(db.String(20), default='warehouse')  # warehouse, bin, emergency
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    reason_code = db.Column(db.String(20))  # adjustment, relocation, damaged, expired
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='inventory_transfers')
    qc_approver = db.relationship('User', foreign_keys=[qc_approver_id])
    items = db.relationship('InventoryTransferItem', backref='transfer', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('TransferStatusHistory', backref='transfer', lazy=True, cascade='all, delete-orphan')

class InventoryTransferItem(db.Model):
    """Inventory transfer line items"""
    __tablename__ = 'inventory_transfer_items'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('inventory_transfers.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200))
    quantity = db.Column(db.Numeric(15, 3), nullable=False)
    unit_of_measure = db.Column(db.String(10))
    from_warehouse_code = db.Column(db.String(10))
    to_warehouse_code = db.Column(db.String(10))
    from_bin = db.Column(db.String(20))
    to_bin = db.Column(db.String(20))
    batch_number = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    unit_price = db.Column(db.Numeric(15, 4))
    total_value = db.Column(db.Numeric(15, 2))
    qc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    base_entry = db.Column(db.Integer)  # SAP Transfer Request DocEntry
    base_line = db.Column(db.Integer)   # SAP Transfer Request Line Number
    sap_line_number = db.Column(db.Integer)  # Line number in posted SAP document
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TransferStatusHistory(db.Model):
    """Track status changes for inventory transfers"""
    __tablename__ = 'transfer_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('inventory_transfers.id'), nullable=False)
    previous_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    changed_by = db.relationship('User', backref='status_changes')

class SerialNumberTransfer(db.Model):
    """Serial Number-wise Stock Transfer Document Header"""
    __tablename__ = 'serial_number_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), nullable=False, unique=True)
    sap_document_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='draft')  # draft, submitted, qc_approved, posted, rejected
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    qc_approver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    qc_approved_at = db.Column(db.DateTime)
    qc_notes = db.Column(db.Text)
    from_warehouse = db.Column(db.String(10), nullable=False)
    to_warehouse = db.Column(db.String(10), nullable=False)
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='serial_transfers')
    qc_approver = db.relationship('User', foreign_keys=[qc_approver_id])
    items = db.relationship('SerialNumberTransferItem', backref='serial_transfer', lazy=True, cascade='all, delete-orphan')

class SerialNumberTransferItem(db.Model):
    """Serial Number Transfer Line Items"""
    __tablename__ = 'serial_number_transfer_items'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_transfer_id = db.Column(db.Integer, db.ForeignKey('serial_number_transfers.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200))
    unit_of_measure = db.Column(db.String(10), default='EA')
    from_warehouse_code = db.Column(db.String(10), nullable=False)
    to_warehouse_code = db.Column(db.String(10), nullable=False)
    qc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    serial_numbers = db.relationship('SerialNumberTransferSerial', backref='transfer_item', lazy=True, cascade='all, delete-orphan')

class SerialNumberTransferSerial(db.Model):
    """Individual Serial Numbers for Transfer Items"""
    __tablename__ = 'serial_number_transfer_serials'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_item_id = db.Column(db.Integer, db.ForeignKey('serial_number_transfer_items.id'), nullable=False)
    serial_number = db.Column(db.String(100), nullable=False)
    internal_serial_number = db.Column(db.String(100), nullable=False)  # From SAP SerialNumberDetails
    system_serial_number = db.Column(db.Integer)  # SystemNumber from SAP
    is_validated = db.Column(db.Boolean, default=False)  # Validated against SAP
    validation_error = db.Column(db.Text)  # Error message if validation fails
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    admission_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique serial numbers per item
    __table_args__ = (db.UniqueConstraint('transfer_item_id', 'serial_number', name='unique_serial_per_item'),)

class TransferRequest(db.Model):
    """SAP B1 Transfer Requests (for reference)"""
    __tablename__ = 'transfer_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    sap_doc_entry = db.Column(db.Integer, unique=True, nullable=False)
    request_number = db.Column(db.String(50), nullable=False)
    from_warehouse = db.Column(db.String(10))
    to_warehouse = db.Column(db.String(10))
    document_status = db.Column(db.String(20))  # Open, Closed
    total_lines = db.Column(db.Integer)
    total_quantity = db.Column(db.Numeric(15, 3))
    created_by = db.Column(db.String(50))
    document_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    comments = db.Column(db.Text)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_processed = db.Column(db.Boolean, default=False)