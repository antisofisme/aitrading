import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Performance monitoring
const startTime = performance.now();

// Global error handling
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  // In production, send to monitoring service
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // In production, send to monitoring service
});

// Initialize React app
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Log app initialization time
const endTime = performance.now();
console.log(`App initialized in ${(endTime - startTime).toFixed(2)}ms`);

// Performance monitoring
if (process.env.NODE_ENV === 'production') {
  // Report Core Web Vitals
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    getCLS(console.log);
    getFID(console.log);
    getFCP(console.log);
    getLCP(console.log);
    getTTFB(console.log);
  });
}