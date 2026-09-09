import { useEffect, useState } from "react";
import { FileBarChart, FileSpreadsheet, FileText, Download, RefreshCw, History } from "lucide-react";
import { reportsService } from "@/services/reports.service";
import type { ReportFormat, ReportHistoryItem, ReportType, ReportTypeInfo } from "@/types";

export default function ReportsPage() {
  const [types, setTypes] = useState<ReportTypeInfo[]>([]);
  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [academicYear, setAcademicYear] = useState("2023-24");
  const [generating, setGenerating] = useState<string | null>(null); // `${type}-${format}`

  useEffect(() => {
    reportsService.getTypes().then(setTypes).catch(() => {});
    loadHistory();
  }, []);

  const loadHistory = () => reportsService.history(15).then(setHistory).catch(() => {});

  const handleGenerate = async (type: ReportType, format: ReportFormat) => {
    const key = `${type}-${format}`;
    setGenerating(key);
    try {
      await reportsService.generateAndDownload(type, format, academicYear.trim() || undefined);
      loadHistory();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Report generation failed. Please try again.");
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <FileBarChart className="w-6 h-6 text-[#003087]" />
          Report Generator
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate the official NIRF Excel workbook and NAAC SSR/AISHE reports directly from master data.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-4 flex items-center gap-3">
        <label className="text-sm font-medium text-foreground">Academic Year</label>
        <input
          value={academicYear}
          onChange={(e) => setAcademicYear(e.target.value)}
          placeholder="2023-24 (leave blank for all years)"
          className="w-56 rounded-lg border border-input bg-background text-sm px-3 py-2"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {types.map((t) => (
          <div key={t.value} className="rounded-xl border border-border bg-card p-5 flex flex-col">
            <h2 className="text-sm font-semibold text-foreground mb-1">{t.label}</h2>
            <p className="text-xs text-muted-foreground flex-1 mb-4">{t.description}</p>
            <div className="flex gap-2">
              <button
                onClick={() => handleGenerate(t.value, "xlsx")}
                disabled={generating === `${t.value}-xlsx`}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-[#003087] hover:bg-[#002266] text-white text-xs font-medium px-3 py-2 transition disabled:opacity-50"
              >
                {generating === `${t.value}-xlsx` ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                )}
                Excel
              </button>
              {t.value !== "nirf" && <button
                onClick={() => handleGenerate(t.value, "pdf")}
                disabled={generating === `${t.value}-pdf`}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-[#C9A227] hover:bg-[#B08F1E] text-white text-xs font-medium px-3 py-2 transition disabled:opacity-50"
              >
                {generating === `${t.value}-pdf` ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <FileText className="w-3.5 h-3.5" />
                )}
                PDF
              </button>}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-1.5">
          <History className="w-4 h-4 text-[#003087]" />
          <span className="text-sm font-semibold text-foreground">Recent Reports</span>
        </div>
        <div className="divide-y divide-border max-h-72 overflow-y-auto">
          {history.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No reports generated yet.</p>
          )}
          {history.map((h) => (
            <div key={h.id} className="px-4 py-2.5 flex items-center gap-3 text-sm">
              <Download className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
              <span className="font-medium text-foreground">{REPORT_LABELS[h.report_type] || h.report_type}</span>
              <span className="text-xs uppercase text-muted-foreground border border-border rounded px-1.5 py-0.5">
                {h.report_format}
              </span>
              <span className="text-xs text-muted-foreground">{h.academic_year || "All years"}</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {new Date(h.created_at).toLocaleString()}
              </span>
              {h.file_size_bytes != null && (
                <span className="text-xs text-muted-foreground">
                  {(h.file_size_bytes / 1024).toFixed(0)} KB
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const REPORT_LABELS: Record<string, string> = {
  nirf: "NIRF Data",
  naac_ssr: "NAAC SSR Data Summary",
  aishe: "AISHE Institutional Data",
};
