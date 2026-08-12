import apiClient from "./api";
import type { User } from "@/types";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedUsers {
  items: User[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const authService = {
  login: async (data: LoginPayload): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>("/auth/login", data);
    return res.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  me: async (): Promise<User> => {
    const res = await apiClient.get<User>("/auth/me");
    return res.data;
  },

  changePassword: async (
    currentPassword: string,
    newPassword: string
  ): Promise<void> => {
    await apiClient.put("/auth/me/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post("/auth/forgot-password", { email });
  },

  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post("/auth/reset-password", {
      token,
      new_password: newPassword,
    });
  },

  listUsers: async (params?: {
    page?: number;
    size?: number;
    role?: string;
    search?: string;
    is_active?: boolean;
  }): Promise<PaginatedUsers> => {
    const res = await apiClient.get<PaginatedUsers>("/auth/users", { params });
    return res.data;
  },

  createUser: async (data: {
    email: string;
    full_name: string;
    password: string;
    role: string;
    department_id?: string;
  }): Promise<User> => {
    const res = await apiClient.post<User>("/auth/users", data);
    return res.data;
  },

  updateUser: async (
    userId: string,
    data: Partial<{
      full_name: string;
      role: string;
      department_id: string;
      is_active: boolean;
    }>
  ): Promise<User> => {
    const res = await apiClient.put<User>(`/auth/users/${userId}`, data);
    return res.data;
  },

  listDepartments: async () => {
    const res = await apiClient.get("/auth/departments");
    return res.data;
  },
};
