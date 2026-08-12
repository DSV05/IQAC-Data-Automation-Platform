import type { UserRole } from "@/types";
import { ROLE_COLORS, ROLE_LABELS } from "@/utils/roles";

interface RoleBadgeProps {
  role: UserRole;
  size?: "sm" | "md";
}

export function RoleBadge({ role, size = "md" }: RoleBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${ROLE_COLORS[role]} ${
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs"
      }`}
    >
      {ROLE_LABELS[role]}
    </span>
  );
}
