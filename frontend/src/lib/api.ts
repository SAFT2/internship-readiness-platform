import axios from "axios";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8100";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
});

export function getErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as
      | {
          error?: {
            message?: string;
            details?: Array<{ loc?: Array<string | number>; msg?: string }>;
          };
          detail?: string | Array<{ loc?: Array<string | number>; msg?: string }>;
        }
      | undefined;

    const validationDetail = data?.error?.details?.[0] ??
      (Array.isArray(data?.detail) ? data?.detail[0] : undefined);

    if (validationDetail?.msg) {
      const rawField = validationDetail.loc?.[validationDetail.loc.length - 1];
      const field = typeof rawField === "string" ? rawField.replaceAll("_", " ") : "field";
      return `${field}: ${validationDetail.msg}`;
    }

    return data?.error?.message || (typeof data?.detail === "string" ? data.detail : undefined) || fallback;
  }

  return fallback;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    const originalRequest = error?.config;

    if (status !== 401 || !originalRequest || originalRequest.__isRetryRequest) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken || refreshing) {
      clearTokens();
      return Promise.reject(error);
    }

    try {
      refreshing = true;
      const refreshRes = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token } = refreshRes.data;
      setTokens(access_token, refresh_token);

      originalRequest.__isRetryRequest = true;
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return api(originalRequest);
    } catch (refreshError) {
      clearTokens();
      return Promise.reject(refreshError);
    } finally {
      refreshing = false;
    }
  },
);
