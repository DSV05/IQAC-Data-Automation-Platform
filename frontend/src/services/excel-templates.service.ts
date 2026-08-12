import apiClient from "./api";
import type { ExcelTemplateItem, FillHistoryItem, TokenInfo } from "@/types";

export const excelTemplatesService = {
  getTokens: async (academicYear?: string): Promise<TokenInfo[]> => {
    const res = await apiClient.get("/excel-templates/tokens", {
      params: academicYear ? { academic_year: academicYear } : {},
    });
    return res.data;
  },

  listTemplates: async (): Promise<ExcelTemplateItem[]> => {
    const res = await apiClient.get("/excel-templates");
    return res.data;
  },

  uploadTemplate: async (file: File, title: string): Promise<ExcelTemplateItem> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    const res = await apiClient.post("/excel-templates", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  deleteTemplate: async (id: string): Promise<void> => {
    await apiClient.delete(`/excel-templates/${id}`);
  },

  /** Fills the template with live data and triggers a browser download. */
  fillAndDownload: async (templateId: string, academicYear?: string): Promise<void> => {
    let res;
    try {
      res = await apiClient.post(
        `/excel-templates/${templateId}/fill`,
        { academic_year: academicYear || null },
        { responseType: "blob" }
      );
    } catch (e: any) {
      // With responseType: "blob", axios also returns error bodies as a Blob —
      // parse it back to JSON so the caller gets a normal error message.
      const blobData = e?.response?.data;
      if (blobData instanceof Blob && blobData.type.includes("json")) {
        const text = await blobData.text();
        try {
          const parsed = JSON.parse(text);
          e.response.data = parsed;
        } catch {
          // leave as-is if it wasn't valid JSON
        }
      }
      throw e;
    }

    const disposition: string = res.headers["content-disposition"] || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] || "filled_template.xlsx";

    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  fillHistory: async (limit = 20): Promise<FillHistoryItem[]> => {
    const res = await apiClient.get("/excel-templates/fill-history", { params: { limit } });
    return res.data;
  },
};
