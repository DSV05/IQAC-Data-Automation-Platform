import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";
import { hasMinimumRole } from "@/utils/roles";

interface ProtectedRouteProps {
  children: React.ReactNode;
  minimumRole?: UserRole;
}

export function ProtectedRoute({ children, minimumRole }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (minimumRole && user && !hasMinimumRole(user.role, minimumRole)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3 max-w-md">
          <div className="text-4xl">🔒</div>
          <h2 className="text-xl font-bold text-foreground">Access Denied</h2>
          <p className="text-muted-foreground text-sm">
            You don't have permission to view this page.
            Contact your IQAC administrator.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
