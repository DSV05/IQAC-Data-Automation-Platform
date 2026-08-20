import apiClient from "./api";

export interface AuditLogEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  entity_label: string | null;
  action: "create" | "update" | "delete";
  changed_by: string | null;
  changed_by_name: string | null;
  academic_year: string | null;
  source: "manual_edit" | "upload";
  changes: Record<string, { old: unknown; new: unknown }>;
  created_at: string;
}

export interface AuditLogFilters {
  entity_type?: string;
  entity_id?: string;
  changed_by?: string;
  action?: string;
  source?: string;
  academic_year?: string;
  date_from?: string;
  date_to?: string;
  q?: string;
  page?: number;
  size?: number;
}

export const auditService = {
  list: async (filters: AuditLogFilters = {}) => {
    const res = await apiClient.get("/audit", { params: filters });
    return res.data as {
      items: AuditLogEntry[];
      total: number;
      page: number;
      size: number;
      pages: number;
    };
  },

  entityTypes: async () => {
    const res = await apiClient.get("/audit/entity-types");
    return res.data as string[];
  },

  entityHistory: async (entityType: string, entityId: string) => {
    const res = await apiClient.get(`/audit/entity/${entityType}/${entityId}`);
    return res.data as AuditLogEntry[];
  },
};
