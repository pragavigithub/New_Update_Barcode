"""
Inventory Transfer Routes
All routes related to inventory transfers between warehouses/bins
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import InventoryTransfer, InventoryTransferItem
from models import User
import logging
from datetime import datetime

transfer_bp = Blueprint('inventory_transfer', __name__, url_prefix='/inventory_transfer', template_folder='templates')

@transfer_bp.route('/')
@login_required
def index():
    """Inventory Transfer main page - list all transfers for current user"""
    if not current_user.has_permission('inventory_transfer'):
        flash('Access denied - Inventory Transfer permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    transfers = InventoryTransfer.query.filter_by(user_id=current_user.id).order_by(InventoryTransfer.created_at.desc()).all()
    return render_template('inventory_transfer/inventory_transfer.html', transfers=transfers)

@transfer_bp.route('/detail/<int:transfer_id>')
@login_required
def detail(transfer_id):
    """Inventory Transfer detail page"""
    transfer = InventoryTransfer.query.get_or_404(transfer_id)
    
    # Check permissions
    if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own transfers', 'error')
        return redirect(url_for('inventory_transfer.index'))
    
    return render_template('inventory_transfer/inventory_transfer_detail.html', transfer=transfer)

@transfer_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new inventory transfer"""
    if not current_user.has_permission('inventory_transfer'):
        flash('Access denied - Inventory Transfer permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        transfer_request_number = request.form.get('transfer_request_number')
        from_warehouse = request.form.get('from_warehouse')
        to_warehouse = request.form.get('to_warehouse')
        
        if not transfer_request_number:
            flash('Transfer request number is required', 'error')
            return redirect(url_for('inventory_transfer.create'))
        
        # Check if transfer already exists
        existing_transfer = InventoryTransfer.query.filter_by(
            transfer_request_number=transfer_request_number, 
            user_id=current_user.id
        ).first()
        
        if existing_transfer:
            flash(f'Transfer already exists for request {transfer_request_number}', 'warning')
            return redirect(url_for('inventory_transfer.detail', transfer_id=existing_transfer.id))
        
        # Create new transfer
        transfer = InventoryTransfer(
            transfer_request_number=transfer_request_number,
            user_id=current_user.id,
            from_warehouse=from_warehouse,
            to_warehouse=to_warehouse,
            status='draft'
        )
        
        db.session.add(transfer)
        db.session.commit()
        
        # Log status change
        log_status_change(transfer.id, None, 'draft', current_user.id, 'Transfer created')
        
        logging.info(f"✅ Inventory Transfer created for request {transfer_request_number} by user {current_user.username}")
        flash(f'Inventory Transfer created for request {transfer_request_number}', 'success')
        return redirect(url_for('inventory_transfer.detail', transfer_id=transfer.id))
    
    return render_template('inventory_transfer/create_transfer.html')

@transfer_bp.route('/<int:transfer_id>/submit', methods=['POST'])
@login_required
def submit(transfer_id):
    """Submit transfer for QC approval"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check permissions
        if transfer.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Only draft transfers can be submitted'}), 400
        
        if not transfer.items:
            return jsonify({'success': False, 'error': 'Cannot submit transfer without items'}), 400
        
        # Update status
        old_status = transfer.status
        transfer.status = 'submitted'
        transfer.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log status change
        log_status_change(transfer_id, old_status, 'submitted', current_user.id, 'Transfer submitted for QC approval')
        
        logging.info(f"📤 Inventory Transfer {transfer_id} submitted for QC approval")
        return jsonify({
            'success': True,
            'message': 'Transfer submitted for QC approval',
            'status': 'submitted'
        })
        
    except Exception as e:
        logging.error(f"Error submitting transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_bp.route('/<int:transfer_id>/qc_approve', methods=['POST'])
@login_required
def qc_approve(transfer_id):
    """QC approve transfer and post to SAP B1"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if transfer.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted transfers can be approved'}), 400
        
        # Get QC notes
        qc_notes = request.json.get('qc_notes', '') if request.is_json else request.form.get('qc_notes', '')
        
        # Mark items as approved
        for item in transfer.items:
            item.qc_status = 'approved'
        
        # Update transfer status
        old_status = transfer.status
        transfer.status = 'qc_approved'
        transfer.qc_approver_id = current_user.id
        transfer.qc_approved_at = datetime.utcnow()
        transfer.qc_notes = qc_notes
        
        # Here you would integrate with SAP B1 to create Stock Transfer
        # For now, we'll simulate success
        transfer.sap_document_number = f"ST-{transfer_id}-{datetime.now().strftime('%Y%m%d')}"
        
        db.session.commit()
        
        # Log status change
        log_status_change(transfer_id, old_status, 'qc_approved', current_user.id, f'Transfer QC approved and posted to SAP B1 as {transfer.sap_document_number}')
        
        logging.info(f"✅ Inventory Transfer {transfer_id} QC approved and posted to SAP B1")
        return jsonify({
            'success': True,
            'message': f'Transfer QC approved and posted to SAP B1 as {transfer.sap_document_number}',
            'sap_document_number': transfer.sap_document_number
        })
        
    except Exception as e:
        logging.error(f"Error approving transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_bp.route('/<int:transfer_id>/qc_reject', methods=['POST'])
@login_required
def qc_reject(transfer_id):
    """QC reject transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if transfer.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted transfers can be rejected'}), 400
        
        # Get rejection reason
        qc_notes = request.json.get('qc_notes', '') if request.is_json else request.form.get('qc_notes', '')
        
        if not qc_notes:
            return jsonify({'success': False, 'error': 'Rejection reason is required'}), 400
        
        # Mark items as rejected
        for item in transfer.items:
            item.qc_status = 'rejected'
        
        # Update transfer status
        old_status = transfer.status
        transfer.status = 'rejected'
        transfer.qc_approver_id = current_user.id
        transfer.qc_approved_at = datetime.utcnow()
        transfer.qc_notes = qc_notes
        
        db.session.commit()
        
        # Log status change
        log_status_change(transfer_id, old_status, 'rejected', current_user.id, f'Transfer rejected by QC: {qc_notes}')
        
        logging.info(f"❌ Inventory Transfer {transfer_id} rejected by QC")
        return jsonify({
            'success': True,
            'message': 'Transfer rejected by QC',
            'status': 'rejected'
        })
        
    except Exception as e:
        logging.error(f"Error rejecting transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_bp.route('/<int:transfer_id>/reopen', methods=['POST'])
@login_required
def reopen(transfer_id):
    """Reopen a rejected transfer"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check permissions
        if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied - You can only reopen your own transfers'}), 403
        
        if transfer.status != 'rejected':
            return jsonify({'success': False, 'error': 'Only rejected transfers can be reopened'}), 400
        
        # Reset transfer to draft status
        old_status = transfer.status
        transfer.status = 'draft'
        transfer.qc_approver_id = None
        transfer.qc_approved_at = None
        transfer.qc_notes = None
        transfer.updated_at = datetime.utcnow()
        
        # Reset all items to pending
        for item in transfer.items:
            item.qc_status = 'pending'
        
        db.session.commit()
        
        # Log status change
        log_status_change(transfer_id, old_status, 'draft', current_user.id, 'Transfer reopened and reset to draft status')
        
        logging.info(f"🔄 Inventory Transfer {transfer_id} reopened and reset to draft status")
        return jsonify({
            'success': True,
            'message': 'Transfer reopened successfully. You can now edit and resubmit it.',
            'status': 'draft'
        })
        
    except Exception as e:
        logging.error(f"Error reopening transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_bp.route('/<int:transfer_id>/add_item', methods=['POST'])
@login_required
def add_transfer_item(transfer_id):
    """Add item to inventory transfer with duplicate prevention"""
    try:
        transfer = InventoryTransfer.query.get_or_404(transfer_id)
        
        # Check permissions
        if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            flash('Access denied - You can only modify your own transfers', 'error')
            return redirect(url_for('inventory_transfer.detail', transfer_id=transfer_id))
        
        if transfer.status != 'draft':
            flash('Cannot add items to non-draft transfer', 'error')
            return redirect(url_for('inventory_transfer.detail', transfer_id=transfer_id))
        
        # Get form data
        item_code = request.form.get('item_code')
        item_name = request.form.get('item_name')
        quantity = float(request.form.get('quantity', 0))
        unit_of_measure = request.form.get('unit_of_measure')
        from_warehouse_code = request.form.get('from_warehouse_code')
        to_warehouse_code = request.form.get('to_warehouse_code')
        from_bin = request.form.get('from_bin')
        to_bin = request.form.get('to_bin')
        batch_number = request.form.get('batch_number')
        
        if not all([item_code, item_name, quantity > 0]):
            flash('Item Code, Item Name, and Quantity are required', 'error')
            return redirect(url_for('inventory_transfer.detail', transfer_id=transfer_id))
        
        # **DUPLICATE PREVENTION LOGIC FOR INVENTORY TRANSFERS**
        # Check if this item_code already exists in this transfer
        existing_item = InventoryTransferItem.query.filter_by(
            transfer_id=transfer_id,
            item_code=item_code
        ).first()
        
        if existing_item:
            flash(f'Item {item_code} has already been added to this inventory transfer. Each item can only be transferred once per transfer request to avoid duplication.', 'error')
            return redirect(url_for('inventory_transfer.detail', transfer_id=transfer_id))
        
        # Create new transfer item
        transfer_item = InventoryTransferItem(
            transfer_id=transfer_id,
            item_code=item_code,
            item_name=item_name,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            from_warehouse_code=from_warehouse_code,
            to_warehouse_code=to_warehouse_code,
            from_bin=from_bin,
            to_bin=to_bin,
            batch_number=batch_number,
            qc_status='pending'
        )
        
        db.session.add(transfer_item)
        db.session.commit()
        
        logging.info(f"✅ Item {item_code} added to inventory transfer {transfer_id} with duplicate prevention")
        flash(f'Item {item_code} successfully added to inventory transfer', 'success')
        
    except Exception as e:
        logging.error(f"Error adding item to inventory transfer: {str(e)}")
        flash(f'Error adding item: {str(e)}', 'error')
    
    return redirect(url_for('inventory_transfer.detail', transfer_id=transfer_id))

@transfer_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_transfer_item(item_id):
    """Delete transfer item"""
    try:
        item = InventoryTransferItem.query.get_or_404(item_id)
        transfer = item.transfer
        
        # Check permissions
        if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot delete items from non-draft transfer'}), 400
        
        transfer_id = transfer.id
        item_code = item.item_code
        
        db.session.delete(item)
        db.session.commit()
        
        logging.info(f"🗑️ Item {item_code} deleted from inventory transfer {transfer_id}")
        return jsonify({'success': True, 'message': f'Item {item_code} deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting inventory transfer item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def log_status_change(transfer_id, previous_status, new_status, changed_by_id, notes=None):
    """Log status change to history table"""
    try:
        # TODO: Add TransferStatusHistory model to main models.py if needed
        # history = TransferStatusHistory(
        #     transfer_id=transfer_id,
        #     previous_status=previous_status,
        #     new_status=new_status,
        #     changed_by_id=changed_by_id,
        #     notes=notes
        # )
        # db.session.add(history)
        # db.session.commit()
        logging.info(f"Status changed from {previous_status} to {new_status} by user {changed_by_id}")
    except Exception as e:
        logging.error(f"Error logging status change: {str(e)}")

# ==========================
# Serial Number Transfer Routes
# ==========================

@transfer_bp.route('/serial')
@login_required
def serial_index():
    """Serial Number Transfer main page"""
    if not current_user.has_permission('inventory_transfer'):
        flash('Access denied - Inventory Transfer permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    from .models import SerialNumberTransfer
    transfers = SerialNumberTransfer.query.filter_by(user_id=current_user.id).order_by(SerialNumberTransfer.created_at.desc()).all()
    return render_template('inventory_transfer/serial_transfer_index.html', transfers=transfers)

@transfer_bp.route('/serial/create', methods=['GET', 'POST'])
@login_required
def serial_create():
    """Create new Serial Number Transfer"""
    if not current_user.has_permission('inventory_transfer'):
        flash('Access denied - Inventory Transfer permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        from .models import SerialNumberTransfer
        
        transfer_number = request.form.get('transfer_number')
        from_warehouse = request.form.get('from_warehouse')
        to_warehouse = request.form.get('to_warehouse')
        notes = request.form.get('notes', '')
        
        if not all([transfer_number, from_warehouse, to_warehouse]):
            flash('Transfer Number, From Warehouse, and To Warehouse are required', 'error')
            return render_template('inventory_transfer/serial_create_transfer.html')
        
        # Check if transfer already exists
        existing = SerialNumberTransfer.query.filter_by(transfer_number=transfer_number).first()
        if existing:
            flash(f'Transfer number {transfer_number} already exists', 'error')
            return render_template('inventory_transfer/serial_create_transfer.html')
        
        # Create new transfer
        transfer = SerialNumberTransfer(
            transfer_number=transfer_number,
            user_id=current_user.id,
            from_warehouse=from_warehouse,
            to_warehouse=to_warehouse,
            notes=notes,
            status='draft'
        )
        
        db.session.add(transfer)
        db.session.commit()
        
        logging.info(f"✅ Serial Number Transfer {transfer_number} created by user {current_user.username}")
        flash(f'Serial Number Transfer {transfer_number} created successfully', 'success')
        return redirect(url_for('inventory_transfer.serial_detail', transfer_id=transfer.id))
    
    return render_template('inventory_transfer/serial_create_transfer.html')

@transfer_bp.route('/serial/<int:transfer_id>')
@login_required
def serial_detail(transfer_id):
    """Serial Number Transfer detail page"""
    from .models import SerialNumberTransfer
    
    transfer = SerialNumberTransfer.query.get_or_404(transfer_id)
    
    # Check permissions
    if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own transfers', 'error')
        return redirect(url_for('inventory_transfer.serial_index'))
    
    return render_template('inventory_transfer/serial_transfer_detail.html', transfer=transfer)

@transfer_bp.route('/serial/<int:transfer_id>/add_item', methods=['POST'])
@login_required
def serial_add_item(transfer_id):
    """Add item to Serial Number Transfer"""
    from .models import SerialNumberTransfer, SerialNumberTransferItem, SerialNumberTransferSerial
    
    try:
        transfer = SerialNumberTransfer.query.get_or_404(transfer_id)
        
        # Check permissions
        if transfer.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot add items to non-draft transfer'}), 400
        
        # Get form data
        item_code = request.form.get('item_code')
        item_name = request.form.get('item_name')
        serial_numbers_text = request.form.get('serial_numbers', '')
        
        if not all([item_code, item_name, serial_numbers_text]):
            return jsonify({'success': False, 'error': 'Item Code, Item Name, and Serial Numbers are required'}), 400
        
        # Parse serial numbers (split by newlines, commas, or spaces)
        import re
        serial_numbers = re.split(r'[,\n\r\s]+', serial_numbers_text.strip())
        serial_numbers = [sn.strip() for sn in serial_numbers if sn.strip()]
        
        if not serial_numbers:
            return jsonify({'success': False, 'error': 'At least one serial number is required'}), 400
        
        # Check if this item already exists in this transfer
        existing_item = SerialNumberTransferItem.query.filter_by(
            serial_transfer_id=transfer_id,
            item_code=item_code
        ).first()
        
        if existing_item:
            return jsonify({'success': False, 'error': f'Item {item_code} already exists in this transfer'}), 400
        
        # Create transfer item
        transfer_item = SerialNumberTransferItem(
            serial_transfer_id=transfer_id,
            item_code=item_code,
            item_name=item_name,
            from_warehouse_code=transfer.from_warehouse,
            to_warehouse_code=transfer.to_warehouse
        )
        
        db.session.add(transfer_item)
        db.session.flush()  # Get the ID
        
        # Validate serial numbers against SAP and add them
        validated_count = 0
        for serial_number in serial_numbers:
            try:
                # Validate serial number against SAP
                validation_result = validate_serial_number_with_sap(serial_number, item_code)
                
                serial_record = SerialNumberTransferSerial(
                    transfer_item_id=transfer_item.id,
                    serial_number=serial_number,
                    internal_serial_number=validation_result.get('SerialNumber', serial_number),
                    system_serial_number=validation_result.get('SystemNumber'),
                    is_validated=validation_result.get('valid', False),
                    validation_error=validation_result.get('error')
                )
                
                if validation_result.get('valid'):
                    validated_count += 1
                
                db.session.add(serial_record)
                
            except Exception as e:
                logging.error(f"Error validating serial number {serial_number}: {str(e)}")
                # Add as unvalidated
                serial_record = SerialNumberTransferSerial(
                    transfer_item_id=transfer_item.id,
                    serial_number=serial_number,
                    internal_serial_number=serial_number,
                    is_validated=False,
                    validation_error=str(e)
                )
                db.session.add(serial_record)
        
        db.session.commit()
        
        logging.info(f"✅ Item {item_code} with {len(serial_numbers)} serial numbers added to transfer {transfer_id}")
        
        return jsonify({
            'success': True, 
            'message': f'Item {item_code} added with {len(serial_numbers)} serial numbers ({validated_count} validated)',
            'validated_count': validated_count,
            'total_count': len(serial_numbers)
        })
        
    except Exception as e:
        logging.error(f"Error adding item to serial transfer: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_bp.route('/serial/<int:transfer_id>/submit', methods=['POST'])
@login_required
def serial_submit(transfer_id):
    """Submit Serial Number Transfer for QC approval"""
    from .models import SerialNumberTransfer
    
    try:
        transfer = SerialNumberTransfer.query.get_or_404(transfer_id)
        
        # Check permissions
        if transfer.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if transfer.status != 'draft':
            return jsonify({'success': False, 'error': 'Only draft transfers can be submitted'}), 400
        
        if not transfer.items:
            return jsonify({'success': False, 'error': 'Cannot submit transfer without items'}), 400
        
        # Check if all serial numbers are validated
        unvalidated_count = 0
        for item in transfer.items:
            for serial in item.serial_numbers:
                if not serial.is_validated:
                    unvalidated_count += 1
        
        if unvalidated_count > 0:
            return jsonify({
                'success': False, 
                'error': f'{unvalidated_count} serial numbers are not validated. Please validate all serial numbers before submitting.'
            }), 400
        
        # Update status
        transfer.status = 'submitted'
        transfer.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"📤 Serial Number Transfer {transfer_id} submitted for QC approval")
        return jsonify({
            'success': True,
            'message': 'Serial Number Transfer submitted for QC approval',
            'status': 'submitted'
        })
        
    except Exception as e:
        logging.error(f"Error submitting serial transfer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def validate_serial_number_with_sap(serial_number, item_code):
    """Validate serial number against SAP B1 API"""
    try:
        import requests
        from flask import current_app
        
        # SAP B1 API endpoint
        base_url = current_app.config.get('SAP_B1_SERVER', 'https://192.168.1.5:50000')
        api_url = f"{base_url}/b1s/v1/SerialNumberDetails"
        
        # Add filter for serial number
        params = {
            '$filter': f"SerialNumber eq '{serial_number}'"
        }
        
        # Make API call (you'll need to handle authentication)
        response = requests.get(api_url, params=params, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('value') and len(data['value']) > 0:
                serial_data = data['value'][0]
                
                # Check if item code matches
                if serial_data.get('ItemCode') == item_code:
                    return {
                        'valid': True,
                        'SerialNumber': serial_data.get('SerialNumber'),
                        'SystemNumber': serial_data.get('SystemNumber'),
                        'ItemCode': serial_data.get('ItemCode'),
                        'ItemDescription': serial_data.get('ItemDescription')
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'Serial number belongs to item {serial_data.get("ItemCode")}, not {item_code}'
                    }
            else:
                return {
                    'valid': False,
                    'error': f'Serial number {serial_number} not found in SAP B1'
                }
        else:
            return {
                'valid': False,
                'error': f'SAP API error: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        logging.error(f"Error validating serial number with SAP: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }