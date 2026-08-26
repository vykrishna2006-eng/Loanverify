import React from 'react';
import Sidebar from './Sidebar';
import { Toaster } from 'react-hot-toast';

export default function Layout({ children, title }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        {title && (
          <div className="topbar">
            <span className="topbar-title">{title}</span>
          </div>
        )}
        <div className="page-content">
          {children}
        </div>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            fontSize: '13px',
          },
        }}
      />
    </div>
  );
}
