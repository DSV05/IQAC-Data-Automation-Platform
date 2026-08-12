import apiClient from "./api";
import type { DeadlineItem, NotificationItem } from "@/types";

export const notificationsService = {
  list: async (unreadOnly = false, limit = 30): Promise<NotificationItem[]> => {
    const res = await apiClient.get("/notifications", {
      params: { unread_only: unreadOnly, limit },
    });
    return res.data;
  },

  unreadCount: async (): Promise<number> => {
    const res = await apiClient.get("/notifications/unread-count");
    return res.data.count;
  },

  markRead: async (id: string): Promise<void> => {
    await apiClient.post(`/notifications/${id}/read`);
  },

  markAllRead: async (): Promise<void> => {
    await apiClient.post("/notifications/read-all");
  },

  listDeadlines: async (): Promise<DeadlineItem[]> => {
    const res = await apiClient.get("/notifications/deadlines");
    return res.data;
  },

  createDeadline: async (payload: {
    title: string;
    description?: string;
    academic_year?: string;
    due_date: string;
    department_id?: string;
    reminder_days_before?: number;
  }): Promise<DeadlineItem> => {
    const res = await apiClient.post("/notifications/deadlines", payload);
    return res.data;
  },

  deleteDeadline: async (id: string): Promise<void> => {
    await apiClient.delete(`/notifications/deadlines/${id}`);
  },

  runChecksNow: async (): Promise<{
    deadlines_triggered: number;
    departments_flagged_missing_data: number;
    academic_year_checked: string;
  }> => {
    const res = await apiClient.post("/notifications/run-checks");
    return res.data;
  },
};
