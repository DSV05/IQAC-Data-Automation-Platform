import type { UserRole } from "@/types";

const ROLE_LEVEL: Record<UserRole, number> = {
  viewer: 0,
  data_entry_operator: 1,
  department_coordinator: 2,
  iqac_admin: 3,
  super_admin: 4,
};

export const ROLE_LABELS: Record<UserRole, string> = {
  viewer: "Viewer",
  data_entry_operator: "Data Entry Operator",
  department_coordinator: "Department Coordinator",
  iqac_admin: "IQAC Admin",
  super_admin: "Super Admin",
};

export const ROLE_COLORS: Record<UserRole, string> = {
  viewer: "bg-gray-100 text-gray-700",
  data_entry_operator: "bg-blue-100 text-blue-700",
  department_coordinator: "bg-purple-100 text-purple-700",
  iqac_admin: "bg-amber-100 text-amber-700",
  super_admin: "bg-red-100 text-red-700",
};

export function hasMinimumRole(userRole: UserRole, minimum: UserRole): boolean {
  return ROLE_LEVEL[userRole] >= ROLE_LEVEL[minimum];
}

export function canManageUsers(role: UserRole): boolean {
  return hasMinimumRole(role, "iqac_admin");
}

export function canApproveWorkflow(role: UserRole): boolean {
  return hasMinimumRole(role, "iqac_admin");
}

export function isAdmin(role: UserRole): boolean {
  return hasMinimumRole(role, "iqac_admin");
}
