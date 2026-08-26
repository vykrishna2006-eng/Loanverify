import React from 'react';

export function SeverityBadge({ severity }) {
  const s = (severity || '').toLowerCase();
  return <span className={`badge badge-${s}`}>{severity}</span>;
}

export function StatusBadge({ status }) {
  const s = (status || '').toLowerCase().replace(' ', '_');
  return <span className={`badge badge-${s}`}>{status?.replace('_', ' ')}</span>;
}

export function RoleBadge({ role }) {
  const colors = {
    DATA_OPERATOR: 'badge-blue',
    REVIEWER: 'badge-purple',
    DATA_CONSUMER: 'badge-low',
  };
  return <span className={`badge ${colors[role] || 'badge-blue'}`}>{role?.replace('_', ' ')}</span>;
}
