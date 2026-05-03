import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10s timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: inject Authorization: Bearer {token}
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't already retried with a refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh/`, {
            refresh: refreshToken,
          });

          const newAccessToken = res.data.access;
          localStorage.setItem('access_token', newAccessToken);

          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed — clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token — redirect to login
        localStorage.removeItem('access_token');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth-specific API calls
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login/', { email, password }),

  register: (data: {
    name: string;
    email: string;
    mobile: string;
    password: string;
    nationality: string;
  }) => api.post('/api/v1/auth/register/', data),

  refresh: (refreshToken: string) =>
    api.post('/api/v1/auth/refresh/', { refresh: refreshToken }),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  },
};
