import apiClient from "./api";
import type { ReportFormat, ReportHistoryItem, ReportType, ReportTypeInfo } from "@/types";

export const reportsService = {
  getTypes: async (): Promise<ReportTypeInfo[]> => {
    const res = await apiClient.get("/reports/types");
    return res.data;
  },

  history: async (limit = 20): Promise<ReportHistoryItem[]> => {
    const res = await apiClient.get("/reports/history", { params: { limit } });
    return res.data;
  },

  /** Generates and triggers a browser download of the report file. */
  generateAndDownload: async (
    reportType: ReportType,
    reportFormat: ReportFormat,
    academicYear?: string
  ): Promise<void> => {
    const res = await apiClient.post(
      "/reports/generate",
      null,
      {
        params: {
          report_type: reportType,
          report_format: reportFormat,
          academic_year: academicYear || undefined,
        },
        responseType: "blob",
      }
    );

    const disposition: string = res.headers["content-disposition"] || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] || `${reportType}.${reportFormat}`;

    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
