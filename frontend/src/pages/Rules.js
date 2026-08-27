import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { rulesAPI } from '../api/client';
import { SeverityBadge } from '../components/SeverityBadge';
import toast from 'react-hot-toast';
import { Power } from 'lucide-react';

export default function Rules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await rulesAPI.list();
      setRules(Array.isArray(r.data) ? r.data : []);
    } catch (e) {
      setRules([]);
      setError(e.response?.data?.detail || 'Could not load validation rules.');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const toggle = async (rule) => {
    try {
      if (rule.is_active) await rulesAPI.deactivate(rule.rule_id);
      else await rulesAPI.activate(rule.rule_id);
      toast.success(`Rule ${rule.rule_id} ${rule.is_active ? 'deactivated' : 'activated'}`);
      load();
    } catch { toast.error('Failed to update rule'); }
  };

  return (
    <Layout title="Validation Rules">
      <div className="page-header">
        <h2>Validation Rules</h2>
        <p>Configurable rule engine. 15+ built-in rules. AI-generated rules require human review before activation.</p>
      </div>
      <div className="card">
        {loading ? <div style={{ textAlign: 'center', padding: 40 }}><span className="spinner" /></div> : error ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--danger)' }}>{error}</div>
        ) : rules.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
            No validation rules found.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>ID</th><th>Name</th><th>Category</th><th>Severity</th><th>Expression</th><th>Source</th><th>Active</th><th></th>
              </tr></thead>
              <tbody>
                {rules.map(r => (
                  <tr key={r.rule_id}>
                    <td className="font-mono" style={{ fontSize: 11 }}>{r.rule_id}</td>
                    <td style={{ fontWeight: 500, fontSize: 13 }}>{r.name}</td>
                    <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{r.category}</span></td>
                    <td><SeverityBadge severity={r.severity} /></td>
                    <td className="font-mono" style={{ fontSize: 10, color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.rule_expression}</td>
                    <td><span className={`badge ${r.source === 'AI_GENERATED' ? 'badge-purple' : 'badge-low'}`}>{r.source}</span></td>
                    <td>
                      <span style={{ color: r.is_active ? 'var(--success)' : 'var(--text-muted)', fontWeight: 600, fontSize: 12 }}>
                        {r.is_active ? '● Active' : '○ Inactive'}
                      </span>
                    </td>
                    <td>
                      <button className={`btn btn-sm ${r.is_active ? 'btn-secondary' : 'btn-success'}`} onClick={() => toggle(r)}>
                        <Power size={12} /> {r.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
