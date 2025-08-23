/**
 * API Client for Warehouse Management System
 * Handles all REST API calls and provides utility functions
 */

class WMSApi {
    constructor() {
        this.baseUrl = '';
        this.headers = {
            'Content-Type': 'application/json',
        };
    }

    async fetchWithAuth(url, options = {}) {
        const config = {
            headers: this.headers,
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Serial Transfer APIs
    async getSerialTransfers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `/inventory_transfer/api/serial${queryString ? '?' + queryString : ''}`;
        return this.fetchWithAuth(url);
    }

    async getSerialTransfer(id) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}`);
    }

    async createSerialTransfer(data) {
        return this.fetchWithAuth(`/inventory_transfer/api/serial`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateSerialTransfer(id, data) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteSerialTransfer(id) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}`, {
            method: 'DELETE'
        });
    }

    async submitSerialTransfer(id) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}/submit`, {
            method: 'POST'
        });
    }

    async qcApproveTransfer(id) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}/qc_approve`, {
            method: 'POST'
        });
    }

    async qcRejectTransfer(id, notes) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${id}/qc_reject`, {
            method: 'POST',
            body: JSON.stringify({ qc_notes: notes })
        });
    }

    async reopenTransfer(id) {
        return this.fetchWithAuth(`/inventory_transfer/serial/${id}/reopen`, {
            method: 'POST'
        });
    }

    // Serial Transfer Items APIs
    async addTransferItem(transferId, data) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/${transferId}/items`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteTransferItem(itemId) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/items/${itemId}`, {
            method: 'DELETE'
        });
    }

    async getItemSerials(itemId) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/items/${itemId}/serials`);
    }

    async addItemSerial(itemId, serialNumber) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/items/${itemId}/serials`, {
            method: 'POST',
            body: JSON.stringify({ serial_number: serialNumber })
        });
    }

    async deleteItemSerial(serialId) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/serials/${serialId}`, {
            method: 'DELETE'
        });
    }

    async editItemSerial(serialId, newSerialNumber) {
        return this.fetchWithAuth(`/api/inventory_transfer/serial/serials/${serialId}`, {
            method: 'PUT',
            body: JSON.stringify({ new_serial_number: newSerialNumber })
        });
    }

    // SAP Integration APIs
    async getItemName(itemCode) {
        return this.fetchWithAuth(`/api/sap/item_name/${encodeURIComponent(itemCode)}`);
    }

    async validateSerial(serialNumber, itemCode, fromWarehouse) {
        const params = new URLSearchParams({
            serial_number: serialNumber,
            item_code: itemCode,
            from_warehouse: fromWarehouse
        });
        return this.fetchWithAuth(`/api/sap/validate_serial?${params}`);
    }

    // User APIs
    async getCurrentUser() {
        return this.fetchWithAuth('/api/auth/current_user');
    }

    // Dashboard APIs
    async getDashboardData() {
        return this.fetchWithAuth('/api/dashboard');
    }
}

// Create global API instance
window.wmsApi = new WMSApi();

// Utility functions
function showAlert(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i data-feather="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : type === 'warning' ? 'alert-triangle' : 'info'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const alertContainer = document.getElementById('alert-container') || document.body;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    alertContainer.insertBefore(tempDiv.firstElementChild, alertContainer.firstChild);

    // Re-initialize feather icons
    if (window.feather) {
        feather.replace();
    }

    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getStatusBadge(status) {
    const statusConfig = {
        'draft': { class: 'bg-secondary', text: 'Draft' },
        'submitted': { class: 'bg-warning text-dark', text: 'Submitted' },
        'qc_approved': { class: 'bg-success', text: 'QC Approved' },
        'posted': { class: 'bg-primary', text: 'Posted' },
        'rejected': { class: 'bg-danger', text: 'Rejected' }
    };

    const config = statusConfig[status] || { class: 'bg-light text-dark', text: status };
    return `<span class="badge ${config.class}">${config.text}</span>`;
}

function showConfirm(message) {
    return confirm(message);
}

function showPrompt(message, defaultValue = '') {
    return prompt(message, defaultValue);
}

// Loading state management
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="text-center p-4"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
}

function hideLoading() {
    // Remove any loading spinners
    const spinners = document.querySelectorAll('.spinner-border');
    spinners.forEach(spinner => {
        spinner.closest('.text-center')?.remove();
    });
}