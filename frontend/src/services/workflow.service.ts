import apiClient from "./api";
import type { SubmissionItem, WorkflowHistoryItem, WorkflowStatus } from "@/types";

export const workflowService = {
  submit: async (departmentId: string, academicYear: string, comments?: string): Promise<SubmissionItem> => {
    const res = await apiClient.post("/workflow/submissions/submit", {
      department_id: departmentId,
      academic_year: academicYear,
      comments: comments || null,
    });
    return res.data;
  },

  list: async (filters?: {
    departmentId?: string;
    academicYear?: string;
    status?: WorkflowStatus;
  }): Promise<SubmissionItem[]> => {
    const res = await apiClient.get("/workflow/submissions", {
      params: {
        department_id: filters?.departmentId,
        academic_year: filters?.academicYear,
        status: filters?.status,
      },
    });
    return res.data;
  },

  get: async (id: string): Promise<SubmissionItem> => {
    const res = await apiClient.get(`/workflow/submissions/${id}`);
    return res.data;
  },

  getHistory: async (id: string): Promise<WorkflowHistoryItem[]> => {
    const res = await apiClient.get(`/workflow/submissions/${id}/history`);
    return res.data;
  },

  review: async (id: string, decision: "approve" | "reject", comments?: string): Promise<SubmissionItem> => {
    const res = await apiClient.post(`/workflow/submissions/${id}/review`, {
      decision,
      comments: comments || null,
    });
    return res.data;
  },

  lock: async (id: string): Promise<SubmissionItem> => {
    const res = await apiClient.post(`/workflow/submissions/${id}/lock`);
    return res.data;
  },
};
