import apiClient from "./api";

export const uploadService = {
  uploadFile: async (
    file: File,
    entityType: string,
    academicYear: string,
    onProgress?: (pct: number) => void,
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("entity_type", entityType);
    form.append("academic_year", academicYear);

    const res = await apiClient.post("/uploads", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
    return res.data;
  },

  listJobs: async (params?: {
    page?: number; size?: number;
    entity_type?: string; status?: string;
  }) => {
    const res = await apiClient.get("/uploads", { params });
    return res.data;
  },

  getJob: async (jobId: string) => {
    const res = await apiClient.get(`/uploads/${jobId}`);
    return res.data;
  },

  downloadErrorReport: async (jobId: string) => {
    const res = await apiClient.get(`/uploads/${jobId}/report`, {
      responseType: "blob",
    });
    downloadBlob(res, `error_report_${jobId}.xlsx`);
  },

  // academicYear: when given, the downloaded file is pre-filled with all
  // existing records for that year (plus a hidden Record ID column) so it
  // can be edited and uploaded straight back as an update. Omit for a
  // blank template.
  downloadTemplate: async (entityType: string, academicYear?: string) => {
    const res = await apiClient.get(`/uploads/templates/${entityType}`, {
      responseType: "blob",
      params: academicYear ? { academic_year: academicYear } : undefined,
    });
    downloadBlob(res, `${entityType}_${academicYear ?? "template"}.xlsx`);
  },

  deleteJob: async (jobId: string) => {
    await apiClient.delete(`/uploads/${jobId}`);
  },

  // statuses: e.g. ["failed", "processing"]. Omit/undefined clears everything.
  clearJobs: async (statuses?: string[]) => {
    const res = await apiClient.delete("/uploads/clear", {
      params: statuses?.length ? { status: statuses.join(",") } : undefined,
    });
    return res.data as { deleted: number };
  },
};

// Triggers a browser download from an authenticated axios blob response,
// preferring the server-provided filename (Content-Disposition) if present.
function downloadBlob(res: { data: Blob; headers: any }, fallbackName: string) {
  const disposition: string | undefined = res.headers?.["content-disposition"];
  const match = disposition?.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] ?? fallbackName;

  const url = window.URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
