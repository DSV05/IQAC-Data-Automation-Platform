import apiClient from "./api";

export const uploadService = {
  uploadFile: async (
    file: File,
    entityType: string,
    academicYear: string,
    departmentId?: string,
    onProgress?: (pct: number) => void,
    mode: "insert" | "update" = "insert",
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("entity_type", entityType);
    form.append("academic_year", academicYear);
    if (departmentId) form.append("department_id", departmentId);
    form.append("mode", mode);

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

  downloadTemplate: async (entityType: string) => {
    const res = await apiClient.get(`/uploads/templates/${entityType}`, {
      responseType: "blob",
    });
    downloadBlob(res, `template_${entityType}.xlsx`);
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