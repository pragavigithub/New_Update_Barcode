/**
 * Serial Number Transfer JavaScript Module
 * Handles all UI interactions for serial transfers
 */

class SerialTransferManager {
    constructor() {
        this.currentTransfers = [];
        this.currentPagination = {};
        this.currentFilters = {
            page: 1,
            per_page: 10,
            search: '',
            user_based: 'true'
        };
        this.currentUser = null;
    }

    async init() {
        // Get current user info
        try {
            this.currentUser = await wmsApi.getCurrentUser();
        } catch (error) {
            console.error('Failed to get current user:', error);
        }

        // Load initial data
        this.loadTransfers();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Search form
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearch();
            });
        }

        // Per page selector
        const perPageSelect = document.getElementById('per_page');
        if (perPageSelect) {
            perPageSelect.addEventListener('change', () => {
                this.currentFilters.per_page = parseInt(perPageSelect.value);
                this.currentFilters.page = 1;
                this.loadTransfers();
            });
        }

        // User filter selector
        const userBasedSelect = document.getElementById('user_based');
        if (userBasedSelect) {
            userBasedSelect.addEventListener('change', () => {
                this.currentFilters.user_based = userBasedSelect.value;
                this.currentFilters.page = 1;
                this.loadTransfers();
            });
        }

        // Clear button
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }

        // Create transfer button
        const createBtn = document.getElementById('create-transfer-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.showCreateModal();
            });
        }
    }

    async loadTransfers() {
        showLoading('transfers-container');
        
        try {
            const response = await wmsApi.getSerialTransfers(this.currentFilters);
            this.currentTransfers = response.transfers;
            this.currentPagination = response.pagination;
            
            this.renderTransfers();
            this.renderPagination();
            this.updateFilterInputs();
        } catch (error) {
            console.error('Failed to load transfers:', error);
            showAlert('Failed to load transfers: ' + error.message, 'error');
        }
    }

    renderTransfers() {
        const container = document.getElementById('transfers-container');
        
        if (!this.currentTransfers || this.currentTransfers.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }

        const transfersHtml = this.currentTransfers.map(transfer => 
            this.renderTransferCard(transfer)
        ).join('');

        container.innerHTML = `
            <div class="row">
                ${transfersHtml}
            </div>
        `;

        // Re-initialize feather icons
        if (window.feather) {
            feather.replace();
        }
    }

    renderTransferCard(transfer) {
        const statusBadge = getStatusBadge(transfer.status);
        const canEdit = transfer.status === 'draft' && 
                       (this.currentUser?.role === 'admin' || 
                        this.currentUser?.role === 'manager' || 
                        transfer.user_id === this.currentUser?.id);

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${transfer.transfer_number}</h6>
                        ${statusBadge}
                    </div>
                    <div class="card-body">
                        <div class="row mb-2">
                            <div class="col-sm-6">
                                <small class="text-muted">From:</small><br>
                                <strong>${transfer.from_warehouse}</strong>
                            </div>
                            <div class="col-sm-6">
                                <small class="text-muted">To:</small><br>
                                <strong>${transfer.to_warehouse}</strong>
                            </div>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Created:</small><br>
                            ${formatDate(transfer.created_at)}
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">Items:</small>
                            <span class="badge bg-light text-dark">${transfer.items_count || 0}</span>
                        </div>
                        ${transfer.notes ? `
                            <div class="mb-2">
                                <small class="text-muted">Notes:</small><br>
                                <small>${transfer.notes}</small>
                            </div>
                        ` : ''}
                    </div>
                    <div class="card-footer">
                        <div class="btn-group btn-group-sm w-100">
                            <button class="btn btn-outline-primary" onclick="serialTransferManager.viewTransfer(${transfer.id})">
                                <i data-feather="eye"></i> View
                            </button>
                            ${canEdit ? `
                                <button class="btn btn-outline-success" onclick="serialTransferManager.editTransfer(${transfer.id})">
                                    <i data-feather="edit"></i> Edit
                                </button>
                            ` : ''}
                            ${transfer.status === 'rejected' && canEdit ? `
                                <button class="btn btn-outline-warning" onclick="serialTransferManager.reopenTransfer(${transfer.id})">
                                    <i data-feather="refresh-cw"></i> Reopen
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderEmptyState() {
        const isSearching = this.currentFilters.search;
        return `
            <div class="text-center py-5">
                <i data-feather="package" style="width: 64px; height: 64px;" class="text-muted mb-3"></i>
                <h5>${isSearching ? 'No transfers found' : 'No Serial Number Transfers'}</h5>
                <p class="text-muted">
                    ${isSearching ? 'No transfers match your search criteria. Try adjusting your filters.' : 'Create your first serial number transfer to get started.'}
                </p>
                <button class="btn btn-primary" onclick="serialTransferManager.showCreateModal()">
                    <i data-feather="plus"></i> Create Serial Transfer
                </button>
            </div>
        `;
    }

    renderPagination() {
        const container = document.getElementById('pagination-container');
        if (!container || !this.currentPagination || this.currentPagination.pages <= 1) {
            if (container) container.innerHTML = '';
            return;
        }

        const pagination = this.currentPagination;
        let paginationHtml = '<nav aria-label="Transfer pagination"><ul class="pagination justify-content-center">';

        // Previous button
        if (pagination.has_prev) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="serialTransferManager.changePage(${pagination.prev_num})">
                        <i data-feather="chevron-left"></i> Previous
                    </a>
                </li>
            `;
        } else {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link"><i data-feather="chevron-left"></i> Previous</span>
                </li>
            `;
        }

        // Page numbers
        for (let page = 1; page <= pagination.pages; page++) {
            if (page === pagination.page) {
                paginationHtml += `<li class="page-item active"><span class="page-link">${page}</span></li>`;
            } else {
                paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="serialTransferManager.changePage(${page})">${page}</a></li>`;
            }
        }

        // Next button
        if (pagination.has_next) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="serialTransferManager.changePage(${pagination.next_num})">
                        Next <i data-feather="chevron-right"></i>
                    </a>
                </li>
            `;
        } else {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link">Next <i data-feather="chevron-right"></i></span>
                </li>
            `;
        }

        paginationHtml += '</ul></nav>';
        container.innerHTML = paginationHtml;

        // Re-initialize feather icons
        if (window.feather) {
            feather.replace();
        }
    }

    updateFilterInputs() {
        const searchInput = document.getElementById('search');
        const perPageSelect = document.getElementById('per_page');
        const userBasedSelect = document.getElementById('user_based');

        if (searchInput) searchInput.value = this.currentFilters.search;
        if (perPageSelect) perPageSelect.value = this.currentFilters.per_page;
        if (userBasedSelect) userBasedSelect.value = this.currentFilters.user_based;

        // Update result count
        const resultCount = document.getElementById('result-count');
        if (resultCount && this.currentPagination) {
            const start = (this.currentPagination.page - 1) * this.currentPagination.per_page + 1;
            const end = Math.min(start + this.currentTransfers.length - 1, this.currentPagination.total);
            resultCount.textContent = `Showing ${start} to ${end} of ${this.currentPagination.total} transfers`;
        }
    }

    handleSearch() {
        const searchInput = document.getElementById('search');
        this.currentFilters.search = searchInput ? searchInput.value : '';
        this.currentFilters.page = 1;
        this.loadTransfers();
    }

    clearFilters() {
        this.currentFilters = {
            page: 1,
            per_page: 10,
            search: '',
            user_based: 'true'
        };
        this.loadTransfers();
    }

    changePage(page) {
        this.currentFilters.page = page;
        this.loadTransfers();
    }

    showCreateModal() {
        const modal = document.getElementById('createTransferModal');
        if (modal) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        }
    }

    async createTransfer() {
        const form = document.getElementById('create-transfer-form');
        const formData = new FormData(form);
        
        const transferData = {
            from_warehouse: formData.get('from_warehouse'),
            to_warehouse: formData.get('to_warehouse'),
            notes: formData.get('notes') || ''
        };

        try {
            const response = await wmsApi.createSerialTransfer(transferData);
            
            showAlert('Transfer created successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('createTransferModal'));
            modal.hide();
            
            // Reset form
            form.reset();
            
            // Reload transfers
            this.loadTransfers();
            
            // Navigate to the new transfer detail page
            this.viewTransfer(response.transfer.id);
            
        } catch (error) {
            console.error('Failed to create transfer:', error);
            showAlert('Failed to create transfer: ' + error.message, 'error');
        }
    }

    viewTransfer(id) {
        // Navigate directly to the serial transfer detail page
        window.location.href = `/inventory_transfer/serial/${id}`;
    }

    editTransfer(id) {
        this.viewTransfer(id);
    }

    async reopenTransfer(id) {
        if (!showConfirm('Are you sure you want to reopen this rejected transfer? It will be changed back to Draft status and you can make modifications.')) {
            return;
        }

        try {
            await wmsApi.reopenTransfer(id);
            showAlert('Transfer reopened successfully!', 'success');
            this.loadTransfers();
        } catch (error) {
            console.error('Failed to reopen transfer:', error);
            showAlert('Failed to reopen transfer: ' + error.message, 'error');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.serialTransferManager = new SerialTransferManager();
    window.serialTransferManager.init();
});