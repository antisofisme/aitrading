const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Client status operations
  getStatus: () => ipcRenderer.invoke('get-status'),
  getPerformanceMetrics: () => ipcRenderer.invoke('get-performance-metrics'),

  // Configuration operations
  updateConfig: (updates) => ipcRenderer.invoke('update-config', updates),
  getConfig: () => ipcRenderer.invoke('get-config'),

  // Connection operations
  restartConnections: () => ipcRenderer.invoke('restart-connections'),

  // Event listeners
  onStatusUpdate: (callback) => {
    ipcRenderer.on('status-update', callback);
    return () => ipcRenderer.removeListener('status-update', callback);
  },

  onMetricsUpdate: (callback) => {
    ipcRenderer.on('metrics-update', callback);
    return () => ipcRenderer.removeListener('metrics-update', callback);
  },

  onAlert: (callback) => {
    ipcRenderer.on('performance-alert', callback);
    return () => ipcRenderer.removeListener('performance-alert', callback);
  },

  onError: (callback) => {
    ipcRenderer.on('error', callback);
    return () => ipcRenderer.removeListener('error', callback);
  },

  // Utility functions
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body)
});