import axios from 'axios';
import { API_BASE_URL } from './config';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const apiWrapper = {
  get: async (endpoint) => {
    const response = await api.get(endpoint);
    return response.data;
  },
  post: async (endpoint, data) => {
    const response = await api.post(endpoint, data);
    return response.data;
  },
  patch: async (endpoint, data) => {
    const response = await api.patch(endpoint, data);
    return response.data;
  },
  delete: async (endpoint) => {
    const response = await api.delete(endpoint);
    return response.data;
  },
};

export default apiWrapper;
