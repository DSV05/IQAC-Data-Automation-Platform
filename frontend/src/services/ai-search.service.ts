import apiClient from "./api";
import type { AIQueryHistoryItem, AISchemaInfo, NLQueryResponse } from "@/types";

export const aiSearchService = {
  getInfo: async (): Promise<AISchemaInfo> => {
    const res = await apiClient.get("/ai-search/info");
    return res.data;
  },

  ask: async (question: string, academicYear?: string): Promise<NLQueryResponse> => {
    const res = await apiClient.post("/ai-search/query", {
      question,
      academic_year: academicYear || null,
    });
    return res.data;
  },

  history: async (limit = 20): Promise<AIQueryHistoryItem[]> => {
    const res = await apiClient.get("/ai-search/history", { params: { limit } });
    return res.data;
  },
};
