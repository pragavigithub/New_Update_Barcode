/**
 * Serial Number Transfer Management JavaScript
 * Handles all client-side functionality for serial transfer operations
 */

class SerialTransferManager {
    constructor() {
        this.currentFilters = {
            page: 1,
            per_page: 10,
            search: '',
            user_based: 'true'
        };
        this.currentUser = null;
    }

    async init() {
        try {
            // Initialize API and get current user
            this.currentUser = await wmsApi.getCurrentUser();
            
            // Load initial transfers
            await this.loadTransfers();
            
            // Setup event listeners
            this.setupEventListeners();
            
            console.log('Serial Transfer Manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Serial Transfer Manager:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Create transfer button
        const createBtn = document.getElementById('create-transfer-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateModal());
        }

        // Search form
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearch();
            });
        }

        // Clear filters
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFilters());
        }

        // Create transfer form
        const createForm = document.getElementById('create-transfer-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createTransfer();
            });
        }
    }

    async loadTransfers() {
        try {
            const container = document.getElementById('transfers-container');
            if (!container) return;

            // Show loading spinner
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;

            const response = await wmsApi.getSerialTransfers(this.currentFilters);
            
            if (response.success) {
                this.renderTransfers(response.transfers, response.pagination);
            } else {
                throw new Error(response.error || 'Failed to load transfers');
            }
        } catch (error) {
            console.error('Error loading transfers:', error);
            this.showError('Failed to load transfers: ' + error.message);
        }
    }

    renderTransfers(transfers, pagination) {
        const container = document.getElementById('transfers-container');
        
        if (transfers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-muted">No transfers found.</p>
                    <button class="btn btn-primary" onclick="serialManager.showCreateModal()">
                        <i data-feather="plus"></i> Create First Transfer
                    </button>
                </div>
            `;
            feather.replace();
            return;
        }

        let html = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Transfer #</th>
                            <th>From → To</th>
                            <th>Status</th>
                            <th>Items</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        transfers.forEach(transfer => {
            const statusBadge = this.getStatusBadge(transfer.status);
            html += `
                <tr>
                    <td><strong>${transfer.transfer_number}</strong></td>
                    <td>${transfer.from_warehouse} → ${transfer.to_warehouse}</td>
                    <td>${statusBadge}</td>
                    <td><span class="badge bg-info">${transfer.items_count || 0} items</span></td>
                    <td>${new Date(transfer.created_at).toLocaleDateString()}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewTransfer('${transfer.id}')">
                                <i data-feather="eye"></i>
                            </button>
                            ${transfer.status === 'rejected' ? `
                                <button class="btn btn-sm btn-warning" onclick="reopenTransfer('${transfer.id}')">
                                    <i data-feather="refresh-cw"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
        
        // Update pagination
        this.renderPagination(pagination);
        
        // Replace feather icons
        feather.replace();
    }

    getStatusBadge(status) {
        const badges = {
            'draft': '<span class="badge bg-secondary">Draft</span>',
            'submitted': '<span class="badge bg-warning text-dark">Submitted</span>',
            'qc_approved': '<span class="badge bg-success">QC Approved</span>',
            'posted': '<span class="badge bg-primary">Posted</span>',
            'rejected': '<span class="badge bg-danger">Rejected</span>'
        };
        return badges[status] || `<span class="badge bg-light text-dark">${status}</span>`;
    }

    renderPagination(pagination) {
        const container = document.getElementById('pagination-container');
        const list = document.getElementById('pagination-list');
        
        if (!pagination || pagination.pages <= 1) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        
        let html = '';
        
        // Previous button
        if (pagination.has_prev) {
            html += `<li class="page-item">
                <a class="page-link" href="#" onclick="serialManager.goToPage(${pagination.prev_num})">Previous</a>
            </li>`;
        }
        
        // Page numbers
        for (let i = 1; i <= pagination.pages; i++) {
            const active = i === pagination.page ? 'active' : '';
            html += `<li class="page-item ${active}">
                <a class="page-link" href="#" onclick="serialManager.goToPage(${i})">${i}</a>
            </li>`;
        }
        
        // Next button
        if (pagination.has_next) {
            html += `<li class="page-item">
                <a class="page-link" href="#" onclick="serialManager.goToPage(${pagination.next_num})">Next</a>
            </li>`;
        }
        
        list.innerHTML = html;
    }

    goToPage(page) {
        this.currentFilters.page = page;
        this.loadTransfers();
    }

    handleSearch() {
        const formData = new FormData(document.getElementById('search-form'));
        this.currentFilters.search = formData.get('search') || '';
        this.currentFilters.per_page = parseInt(formData.get('per_page')) || 10;
        this.currentFilters.user_based = formData.get('user_based') || 'true';
        this.currentFilters.page = 1; // Reset to first page
        this.loadTransfers();
    }

    clearFilters() {
        document.getElementById('search').value = '';
        document.getElementById('per_page').value = '10';
        document.getElementById('user_based').value = 'true';
        
        this.currentFilters = {
            page: 1,
            per_page: 10,
            search: '',
            user_based: 'true'
        };
        this.loadTransfers();
    }

    showCreateModal() {
        const modal = new bootstrap.Modal(document.getElementById('createTransferModal'));
        modal.show();
    }

    async createTransfer() {
        try {
            const formData = new FormData(document.getElementById('create-transfer-form'));
            
            const transferData = {
                from_warehouse: formData.get('from_warehouse'),
                to_warehouse: formData.get('to_warehouse'),
                notes: formData.get('notes') || ''
            };

            if (!transferData.from_warehouse || !transferData.to_warehouse) {
                throw new Error('From and To warehouses are required');
            }

            if (transferData.from_warehouse === transferData.to_warehouse) {
                throw new Error('From and To warehouses must be different');
            }

            const response = await wmsApi.createSerialTransfer(transferData);
            
            if (response.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('createTransferModal'));
                modal.hide();
                
                // Reset form
                document.getElementById('create-transfer-form').reset();
                
                // Show success message
                this.showSuccess('Transfer created successfully!');
                
                // Reload transfers list
                await this.loadTransfers();
                
                // Navigate to transfer detail page
                if (response.transfer && response.transfer.id) {
                    setTimeout(() => {
                        viewTransfer(response.transfer.id);
                    }, 1000);
                }
            } else {
                throw new Error(response.error || 'Failed to create transfer');
            }
        } catch (error) {
            console.error('Error creating transfer:', error);
            this.showError('Failed to create transfer: ' + error.message);
        }
    }

    showError(message) {
        // Create and show error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    showSuccess(message) {
        // Create and show success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// Global functions for template onclick handlers
function viewTransfer(id) {
    window.location.href = `/inventory_transfer/serial/${id}`;
}

function viewItemDetails(itemId) {
    // Implementation for viewing item details
    console.log('View item details for:', itemId);
}

function submitTransfer(id) {
    if (confirm('Are you sure you want to submit this transfer for QC approval?')) {
        wmsApi.submitSerialTransfer(id)
            .then(response => {
                if (response.success) {
                    serialManager.showSuccess('Transfer submitted successfully!');
                    location.reload();
                } else {
                    serialManager.showError('Failed to submit transfer: ' + response.error);
                }
            })
            .catch(error => {
                serialManager.showError('Failed to submit transfer: ' + error.message);
            });
    }
}

function deleteTransfer(id) {
    if (confirm('Are you sure you want to delete this transfer? This action cannot be undone.')) {
        wmsApi.deleteSerialTransfer(id)
            .then(response => {
                if (response.success) {
                    serialManager.showSuccess('Transfer deleted successfully!');
                    window.location.href = '/inventory_transfer/serial';
                } else {
                    serialManager.showError('Failed to delete transfer: ' + response.error);
                }
            })
            .catch(error => {
                serialManager.showError('Failed to delete transfer: ' + error.message);
            });
    }
}

function approveTransfer(id) {
    if (confirm('Are you sure you want to approve this transfer?')) {
        wmsApi.qcApproveTransfer(id)
            .then(response => {
                if (response.success) {
                    serialManager.showSuccess('Transfer approved successfully!');
                    location.reload();
                } else {
                    serialManager.showError('Failed to approve transfer: ' + response.error);
                }
            })
            .catch(error => {
                serialManager.showError('Failed to approve transfer: ' + error.message);
            });
    }
}

function rejectTransfer(id) {
    const reason = prompt('Please enter the reason for rejection:');
    if (reason && reason.trim()) {
        wmsApi.qcRejectTransfer(id, reason.trim())
            .then(response => {
                if (response.success) {
                    serialManager.showSuccess('Transfer rejected successfully!');
                    location.reload();
                } else {
                    serialManager.showError('Failed to reject transfer: ' + response.error);
                }
            })
            .catch(error => {
                serialManager.showError('Failed to reject transfer: ' + error.message);
            });
    }
}

function reopenTransfer(id) {
    if (confirm('Are you sure you want to reopen this rejected transfer?')) {
        wmsApi.reopenTransfer(id)
            .then(response => {
                if (response.success) {
                    serialManager.showSuccess('Transfer reopened successfully!');
                    location.reload();
                } else {
                    serialManager.showError('Failed to reopen transfer: ' + response.error);
                }
            })
            .catch(error => {
                serialManager.showError('Failed to reopen transfer: ' + error.message);
            });
    }
}

function removeItem(itemId) {
    if (confirm('Are you sure you want to remove this item from the transfer?')) {
        // Implementation for removing item
        console.log('Remove item:', itemId);
    }
}

function showAddItemModal() {
    const modal = new bootstrap.Modal(document.getElementById('addItemModal'));
    modal.show();
}

// Initialize when page loads
let serialManager;

document.addEventListener('DOMContentLoaded', function() {
    serialManager = new SerialTransferManager();
    serialManager.init();
});