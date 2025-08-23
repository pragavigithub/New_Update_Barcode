/**
 * WMS API Client Instance
 * Provides global access to WMSApi functionality
 */

// This file should be loaded AFTER api.js
if (typeof WMSApi !== 'undefined') {
    // Initialize global wmsApi instance
    window.wmsApi = new WMSApi();
} else {
    console.error('WMSApi class not found. Make sure api.js is loaded before wms-api.js');
}