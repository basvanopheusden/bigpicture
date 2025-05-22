// config.js

export const API_BASE_URL = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL 
  : window.location.hostname === 'localhost' 
    ? 'http://localhost:5001' 
    : 'https://bigpicture-backend.fly.dev';

export const config = {
    apiBaseUrl: API_BASE_URL,
    apiEndpoints: {
        areas: '/api/areas',
        objectives: '/api/objectives',
        tasks: '/api/tasks',
        undo: '/api/undo'
    }
};
    
export default config;
