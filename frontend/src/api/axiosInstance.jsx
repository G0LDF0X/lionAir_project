import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://100.27.31.137:8080',
});

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosInstance;
