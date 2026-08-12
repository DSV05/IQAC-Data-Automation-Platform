import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Loader2, UserCheck, UserX, ChevronLeft, ChevronRight } from "lucide-react";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { RoleBadge } from "@/components/shared/RoleBadge";
import { ROLE_LABELS } from "@/utils/roles";
import type { User, UserRole } from "@/types";

const ALL_ROLES: UserRole[] = [
  "viewer",
  "data_entry_operator",
  "department_coordinator",
  "iqac_admin",
  "super_admin",
];

export default function UsersPage() {
  const qc = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "">("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users", page, search, roleFilter],
    queryFn: () =>
      authService.listUsers({
        page,
        size: 15,
        search: search || undefined,
        role: roleFilter || undefined,
      }),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      authService.updateUser(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">User Management</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manage platform access and roles
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white text-sm font-medium px-4 py-2.5 transition"
        >
          <Plus className="w-4 h-4" />
          Add User
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-[#003087]"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value as UserRole | ""); setPage(1); }}
          className="rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
        >
          <option value="">All Roles</option>
          {ALL_ROLES.map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Email</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Role</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Department</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Last Login</th>
              <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-muted-foreground">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                </td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-muted-foreground">
                  No users found
                </td>
              </tr>
            ) : (
              data?.items.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-border last:border-0 hover:bg-muted/20 transition"
                >
                  <td className="px-4 py-3 font-medium text-foreground">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-[#003087]/10 flex items-center justify-center text-[#003087] font-semibold text-xs">
                        {user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                      </div>
                      {user.full_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                  <td className="px-4 py-3">
                    <RoleBadge role={user.role} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {user.department?.code ?? <span className="text-muted-foreground/50">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium rounded-full px-2 py-0.5 ${
                      user.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}>
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleDateString("en-IN")
                      : "Never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingUser(user)}
                        className="text-xs text-[#003087] hover:underline"
                      >
                        Edit
                      </button>
                      {currentUser?.id !== user.id && (
                        <button
                          onClick={() =>
                            toggleActiveMutation.mutate({
                              id: user.id,
                              is_active: !user.is_active,
                            })
                          }
                          className={`text-xs hover:underline ${
                            user.is_active ? "text-destructive" : "text-green-600"
                          }`}
                        >
                          {user.is_active ? "Deactivate" : "Activate"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, data.total)} of {data.total} users
          </span>
          <div className="flex items-center gap-1">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3">
              {page} / {data.pages}
            </span>
            <button
              disabled={page === data.pages}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Create / Edit Modal */}
      {(showCreateModal || editingUser) && (
        <UserFormModal
          user={editingUser}
          onClose={() => { setShowCreateModal(false); setEditingUser(null); }}
          onSuccess={() => {
            qc.invalidateQueries({ queryKey: ["users"] });
            setShowCreateModal(false);
            setEditingUser(null);
          }}
        />
      )}
    </div>
  );
}

// ── User Form Modal ────────────────────────────────────────────────────────────

function UserFormModal({
  user,
  onClose,
  onSuccess,
}: {
  user: User | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const isEdit = !!user;
  const qc = useQueryClient();

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: authService.listDepartments,
  });

  const createMutation = useMutation({
    mutationFn: authService.createUser,
    onSuccess,
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => authService.updateUser(user!.id, data),
    onSuccess,
  });

  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm();

  const onSubmit = async (data: any) => {
    if (isEdit) {
      const payload: any = { full_name: data.full_name, role: data.role };
      if (data.department_id) payload.department_id = data.department_id;
      await updateMutation.mutateAsync(payload);
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  const serverError =
    (createMutation.error as any)?.response?.data?.detail ||
    (updateMutation.error as any)?.response?.data?.detail;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-background rounded-2xl shadow-2xl border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground">
            {isEdit ? "Edit User" : "Add New User"}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {serverError && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
              {serverError}
            </div>
          )}

          <Field label="Full Name" error={errors.full_name?.message as string}>
            <input
              defaultValue={user?.full_name}
              className="form-input"
              {...register("full_name", { required: "Required" })}
            />
          </Field>

          {!isEdit && (
            <Field label="Email" error={errors.email?.message as string}>
              <input
                type="email"
                className="form-input"
                {...register("email", { required: "Required" })}
              />
            </Field>
          )}

          {!isEdit && (
            <Field label="Password" error={errors.password?.message as string}>
              <input
                type="password"
                className="form-input"
                placeholder="Min 8 chars, 1 uppercase, 1 number"
                {...register("password", {
                  required: "Required",
                  minLength: { value: 8, message: "Min 8 chars" },
                  validate: {
                    upper: v => /[A-Z]/.test(v) || "Needs uppercase",
                    digit: v => /\d/.test(v) || "Needs a number",
                  },
                })}
              />
            </Field>
          )}

          <Field label="Role" error={errors.role?.message as string}>
            <select
              defaultValue={user?.role ?? "viewer"}
              className="form-input"
              {...register("role", { required: "Required" })}
            >
              {ALL_ROLES.map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
          </Field>

          <Field label="Department (optional)">
            <select
              defaultValue={user?.department_id ?? ""}
              className="form-input"
              {...register("department_id")}
            >
              <option value="">— None —</option>
              {departments?.map((d: any) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </Field>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-border py-2.5 text-sm font-medium hover:bg-muted transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white text-sm font-medium py-2.5 transition disabled:opacity-60"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEdit ? "Save changes" : "Create user"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-foreground">{label}</label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

// Missing import fix at top
import { useForm } from "react-hook-form";
