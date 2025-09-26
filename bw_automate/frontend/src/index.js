import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Create root and render app
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring (Apple-style)
if (process.env.NODE_ENV === 'development') {
  // Report web vitals in development
  import('./utils/reportWebVitals').then(({ default: reportWebVitals }) => {
    reportWebVitals(console.log);
  });
}