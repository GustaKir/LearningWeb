import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 60000, // Increased to 60 seconds for RAG operations which can be resource intensive
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Add a request interceptor
api.interceptors.request.use(
  config => {
    // Log outgoing requests in development
    if (import.meta.env.DEV) {
      console.log(`API Request: ${config.method.toUpperCase()} ${config.baseURL}${config.url}`, config.data || '');
    }
    // You can add auth tokens here if needed
    return config;
  },
  error => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor
api.interceptors.response.use(
  response => {
    // Log API responses in development
    if (import.meta.env.DEV) {
      console.log(`API Response: ${response.status} ${response.config.method.toUpperCase()} ${response.config.url}`);
    }
    return response;
  },
  error => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
      // Check if the error is due to a quiz generation issue
      if (error.config.url.includes('/quiz/generate')) {
        console.error('Quiz generation failed. Details:', error.response.data);
      }
    } else if (error.request) {
      console.error('No response received:', error.request);
      if (error.code === 'ECONNABORTED') {
        console.error('Request timed out. This could be due to the quiz generation taking too long.');
      }
    } else {
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api; 