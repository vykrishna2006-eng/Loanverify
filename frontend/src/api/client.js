import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('lv_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('lv_token');
      localStorage.removeItem('lv_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default client;

// ── Auth ──────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return client.post('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => client.get('/auth/me'),
  register: (data) => client.post('/auth/register', data),
};

// ── Uploads ───────────────────────────────────────────
export const uploadsAPI = {
  list: (params) => client.get('/uploads', { params }),
  get: (id) => client.get(`/uploads/${id}`),
  upload: (formData) => client.post('/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  validate: (id) => client.post(`/uploads/${id}/validate`),
  qualityScore: (id) => client.get(`/uploads/${id}/quality-score`),
};

// ── Loans ─────────────────────────────────────────────
export const loansAPI = {
  list: (params) => client.get('/loans', { params }),
  get: (loanId, includeExceptions = false) =>
    client.get(`/loans/${loanId}`, { params: { include_exceptions: includeExceptions } }),
  editField: (loanId, fieldName, newValue, reason) =>
    client.patch(`/loans/${loanId}`, null, {
      params: { field_name: fieldName, new_value: newValue, reason },
    }),
};

// ── Exceptions ────────────────────────────────────────
export const exceptionsAPI = {
  list: (params) => client.get('/exceptions', { params }),
  listTypes: () => client.get('/exceptions/types'),
  get: (id) => client.get(`/exceptions/${id}`),
  addComment: (id, comment) => client.post(`/exceptions/${id}/comment`, { comment }),
  generateAIReview: (id) => client.post(`/exceptions/${id}/ai-review`),
  submitDecision: (id, data) => client.post(`/exceptions/${id}/decision`, data),
  assign: (id, assigneeId) => client.post(`/exceptions/${id}/assign?assignee_id=${assigneeId}`),
};

// ── AI Assistant ──────────────────────────────────────
export const aiAPI = {
  getRecommendation: (exceptionId) => client.get(`/ai/recommendation/${exceptionId}`),
  suggestCorrection: (exceptionId) => client.get(`/ai/recommendation/${exceptionId}`), // Feature 2
  compareSources: (exceptionId) => client.post(`/ai/compare-sources/${exceptionId}`),
  generateNote: (exceptionId) => client.post(`/ai/generate-note/${exceptionId}`),
  classifySeverity: (exceptionId) => client.post(`/ai/classify-severity/${exceptionId}`),
  batchSummary: (uploadId) => client.post(`/ai/batch-summary?upload_id=${uploadId}`),
  generateRule: (description) => client.post('/ai/generate-rule', { description }),
};

// ── Verified Loans ────────────────────────────────────
export const verifiedLoansAPI = {
  list: (params) => client.get('/verified-loans', { params }),
  get: (loanId) => client.get(`/verified-loans/${loanId}`),
  verify: (loanId, reviewerNote) =>
    client.post('/verified-loans', null, { params: { loan_id: loanId, reviewer_note: reviewerNote } }),
  verifyHash: (loanId) => client.get(`/verified-loans/${loanId}/verify-hash`),
  export: (loanId) => client.post(`/verified-loans/${loanId}/export`),
};

// ── Audit ─────────────────────────────────────────────
export const auditAPI = {
  list: (params) => client.get('/audit', { params }),
  byLoan: (loanId) => client.get(`/audit/loan/${loanId}`),
  eventTypes: () => client.get('/audit/event-types'),
};

// ── Dashboard ─────────────────────────────────────────
export const dashboardAPI = {
  operator: () => client.get('/dashboard/operator'),
  reviewer: () => client.get('/dashboard/reviewer'),
  consumer: () => client.get('/dashboard/consumer'),
  summary: () => client.get('/summary'),               // Module H spec path
};

// ── Rules ─────────────────────────────────────────────
export const rulesAPI = {
  list: () => client.get('/rules'),
  activate: (ruleId) => client.post(`/rules/${ruleId}/activate`),
  deactivate: (ruleId) => client.post(`/rules/${ruleId}/deactivate`),
  activateAiRule: (name, description, ruleExpression, severity) =>
    client.post('/rules/activate-ai-rule', null, {
      params: { name, description, rule_expression: ruleExpression, severity },
    }),
};

// ── Exports ───────────────────────────────────────────
export const exportsAPI = {
  verifiedLoansCSV: () => `${API_BASE}/api/exports/verified-loans/csv`,
  auditCSV: (loanId) => `${API_BASE}/api/exports/audit/csv${loanId ? `?loan_id=${loanId}` : ''}`,
};
