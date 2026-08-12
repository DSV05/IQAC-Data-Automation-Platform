import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";

export function useAuth() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, setAuth, clearAuth, refreshToken } =
    useAuthStore();

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate("/dashboard");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () =>
      refreshToken ? authService.logout(refreshToken) : Promise.resolve(),
    onSettled: () => {
      clearAuth();
      queryClient.clear();
      navigate("/login");
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string;
      newPassword: string;
    }) => authService.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      // All sessions revoked — force re-login
      clearAuth();
      navigate("/login");
    },
  });

  return {
    user,
    isAuthenticated,
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    logout: logoutMutation.mutate,
    changePassword: changePasswordMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    loginError: loginMutation.error,
  };
}

export function useCurrentUser() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authService.me,
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5,
  });
}
