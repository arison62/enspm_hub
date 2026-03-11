// frontend/lib/axios.ts
import qs from "qs";
import Axios from "axios";
import { authStore } from "@/stores/authStore";

export interface ApiErrorResponse {
  detail: string;
}

const axios = Axios.create({
  baseURL: "/api/v1",
  paramsSerializer: params => qs.stringify(params, { arrayFormat: 'repeat' }),
  
});

axios.interceptors.request.use((config) => {
  const token = authStore.getState().accessToken;
  if (token) {

    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});


axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = authStore.getState().refreshToken;

      if (refreshToken) {
        try {
        /**
         * Response from the authentication refresh endpoint.
         * Contains the new access token and/or refresh token after successful refresh.
         * @type {AxiosResponse<{access_token: string; refresh_token?: string}>}
         */
          const res = await Axios.post("/auth/refresh", {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = res.data;

          authStore.getState().setTokens(access_token, refresh_token);

          // Réessayer la requête originale avec le nouveau token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return axios(originalRequest);
        } catch {
          authStore.getState().logout();
          
        }
      }
    }

    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const data = error.response?.data
    error.api = {
      message : data?.error_message || data?.detail || error.message,
      validationErrors: data?.errors || null,
      status: error.response?.status || 500
    }
    // overwrite message standard axios
    error.message = error.api.message;
    return Promise.reject(error);
  }
)

export default axios;
export const apiClient = axios
