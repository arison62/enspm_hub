// frontend/ts/stores/authStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { type UserComplete } from "@/types/user";

interface AuthState {
  user: UserComplete | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;

  // Actions
  setAuth: (
    user: UserComplete,
    accessToken: string,
    refreshToken: string,
  ) => void;
  logout: () => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: UserComplete) => void;
}

export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isAdmin: false,

      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isAdmin: ["admin_site", "super_admin"].includes("admin"),
        }),

      setTokens: (accessToken, refreshToken) =>
        set({
          accessToken,
          refreshToken,
        }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
      setUser: (user) => {
        set((state) => {
          return {
            ...state,
            isAdmin: ["admin_site", "super_admin"].includes(user.role_systeme),
            user,
          };
        });
      },
    }),
    {
      name: "enspm-auth-storage", // clé dans localStorage
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    },
  ),
);

export const useAuthStore = authStore;
