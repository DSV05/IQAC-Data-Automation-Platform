import apiClient from "./api";

export const validationService = {
  run: async (academicYear?: string) => {
    const res = await apiClient.get("/validation/run", {
      params: academicYear ? { academic_year: academicYear } : {},
    });
    return res.data;
  },

  export: async (academicYear?: string) => {
    const res = await apiClient.get("/validation/export", {
      params: academicYear ? { academic_year: academicYear } : {},
      responseType: "blob",
    });
    const disposition: string | undefined = res.headers?.["content-disposition"];
    const match = disposition?.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] ?? `validation_report_${academicYear || "all"}.xlsx`;

    const url = window.URL.createObjectURL(res.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
