import apiClient from "./api";

export interface CustomColumnItem {
  id: string;
  entity_type: string;
  field_key: string;
  label: string;
  created_at: string;
}

export const customColumnsService = {
  list: async (entityType: string): Promise<CustomColumnItem[]> => {
    const res = await apiClient.get(`/custom-columns/${entityType}`);
    return res.data;
  },

  add: async (entityType: string, label: string): Promise<CustomColumnItem> => {
    const res = await apiClient.post(`/custom-columns/${entityType}`, { label });
    return res.data;
  },

  remove: async (entityType: string, columnId: string): Promise<void> => {
    await apiClient.delete(`/custom-columns/${entityType}/${columnId}`);
  },
};
