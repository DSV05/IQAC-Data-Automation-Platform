import apiClient from "./api";

export const dashboardService = {
  getSummary: async (academicYear: string) => {
    const res = await apiClient.get("/dashboard/summary", {
      params: { academic_year: academicYear },
    });
    return res.data;
  },
};
