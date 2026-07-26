import axios from 'axios';

export const api = axios.create({ baseURL: '/api/v1', timeout: 30000 });

export const transactionsApi = {
  list: (params?: Record<string, any>) => api.get('/transactions', { params }),
  get: (id: number) => api.get(`/transactions/${id}`),
  create: (data: any) => api.post('/transactions', data),
  update: (id: number, data: any) => api.put(`/transactions/${id}`, data),
  delete: (id: number) => api.delete(`/transactions/${id}`),
};

export const categoriesApi = {
  list: () => api.get('/categories'),
  create: (data: any) => api.post('/categories', data),
  delete: (id: number) => api.delete(`/categories/${id}`),
};

export const importsApi = {
  upload: (file: File, sourceType: string) => {
    const fd = new FormData(); fd.append('file', file); fd.append('source_type', sourceType);
    return api.post('/imports/upload', fd);
  },
  list: () => api.get('/imports'),
};

export const detectionApi = {
  list: (params?: Record<string, any>) => api.get('/detection', { params }),
  get: (id: number) => api.get(`/detection/${id}`),
  markRead: (id: number) => api.patch(`/detection/${id}/read`),
  run: () => api.post('/detection/run'),
};

export const budgetApi = {
  list: () => api.get('/budgets'),
  create: (data: any) => api.post('/budgets', data),
  delete: (id: number) => api.delete(`/budgets/${id}`),
};
