import axios from 'axios';

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// Response interceptor to format error details
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      const errorCode = data?.detail?.code || data?.error?.code || 'UNKNOWN_ERROR';
      const message = data?.detail?.message || data?.error?.message || `Request failed with status ${status}`;
      return Promise.reject(new ApiError(status, errorCode, message));
    }
    
    return Promise.reject(
      new ApiError(
        500,
        'NETWORK_ERROR',
        error.message || 'Cannot reach the backend service. Please check your connection.'
      )
    );
  }
);

export default apiClient;
