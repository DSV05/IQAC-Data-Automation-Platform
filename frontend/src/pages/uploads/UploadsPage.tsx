import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Upload, Download, FileSpreadsheet, CheckCircle,
  XCircle, AlertTriangle, Clock, RefreshCw, X, Trash2,
} from "lucide-react";
import { uploadService } from "@/services/upload.service";
import { FileDropzone } from "@/components/uploads/FileDropzone";
import { UploadResultPanel } from "@/components/uploads/UploadResultPanel";

const ACADEMIC_YEARS = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];

const ENTITY_TYPES = [
  { value: "faculty",        label: "Faculty",          template: true },
  { value: "students",       label: "Students",          template: true },
  { value: "research",       label: "Research Publications", template: true },
  { value: "patents",        label: "Patents",           template: true },
  { value: "placements",     label: "Placements",        template: true },
  { value: "higher_studies", label: "Higher Studies",    template: false },
  { value: "funded_projects",label: "Funded Projects",   template: false },
  { value: "mous",           label: "MoUs",              template: true },
  { value: "events",         label: "Events",            template: true },
  { value: "energy",         label: "Energy Consumption",template: true },
  { value: "water",          label: "Water Consumption", template: true },
  { value: "waste",          label: "Waste Management",  template: true },
  { value: "awards",         label: "Awards",            template: true },
  { value: "consultancy",    label: "Consultancy",       template: false },
  { value: "sdg_activities", label: "SDG Activities",    template: true },
];

const STATUS_ICONS = {
  completed: <CheckCircle className="w-4 h-4 text-green-600" />,
  partial:   <AlertTriangle className="w-4 h-4 text-amber-500" />,
  failed:    <XCircle className="w-4 h-4 text-destructive" />,
  processing:<RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />,
  pending:   <Clock className="w-4 h-4 text-muted-foreground" />,
};

const STATUS_COLORS = {
  completed: "bg-green-100 text-green-700",
  partial:   "bg-amber-100 text-amber-700",
  failed:    "bg-red-100 text-red-700",
  processing:"bg-blue-100 text-blue-700",
  pending:   "bg-gray-100 text-gray-600",
};

export default function UploadsPage() {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [entityType, setEntityType] = useState("faculty");
  const [academicYear, setAcademicYear] = useState("2024-25");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);

  const [clearing, setClearing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["upload-jobs"],
    queryFn: () => uploadService.listJobs({ size: 20 }),
    refetchInterval: 5000,
  });

  const stuckCount = jobsData?.items?.filter((j: any) =>
    ["failed", "processing"].includes(j.status)
  ).length ?? 0;

  const handleClearStuck = async () => {
    setClearing(true);
    try {
      await uploadService.clearJobs(["failed", "processing"]);
      qc.invalidateQueries({ queryKey: ["upload-jobs"] });
    } finally {
      setClearing(false);
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Clear all upload history? This cannot be undone.")) return;
    setClearing(true);
    try {
      await uploadService.clearJobs();
      qc.invalidateQueries({ queryKey: ["upload-jobs"] });
    } finally {
      setClearing(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    setDeletingId(jobId);
    try {
      await uploadService.deleteJob(jobId);
      qc.invalidateQueries({ queryKey: ["upload-jobs"] });
    } finally {
      setDeletingId(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setResult(null);
    try {
      const res = await uploadService.uploadFile(
        file, entityType, academicYear,
        (pct) => setProgress(pct),
      );
      setResult(res);
      setFile(null);
      qc.invalidateQueries({ queryKey: ["upload-jobs"] });
    } catch (e: any) {
      setResult({
        job_id: "error",
        status: "failed",
        total_rows: 0, inserted_rows: 0, updated_rows: 0,
        error_rows: 0, skipped_rows: 0,
        errors: [{ row: 0, field: "", value: "", error: e?.response?.data?.detail || e.message }],
        has_more_errors: false,
      });
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const selectedEntity = ENTITY_TYPES.find((e) => e.value === entityType);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Data Upload</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Download current data (or a blank template), edit it, and upload it back —
          changes update existing records, new rows get added, nothing else is touched.
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Left — upload form */}
        <div className="lg:col-span-3 space-y-4">
          <div className="rounded-xl border border-border bg-card p-5 space-y-5">
            <h2 className="font-semibold text-foreground flex items-center gap-2">
              <Upload className="w-4 h-4 text-[#003087]" />
              Upload File
            </h2>

            {/* Entity + Year selectors */}
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Data Type</label>
                <select
                  value={entityType}
                  onChange={(e) => {
                    setEntityType(e.target.value);
                  }}
                  className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
                  disabled={uploading}
                >
                  {ENTITY_TYPES.map((et) => (
                    <option key={et.value} value={et.value}>{et.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Academic Year</label>
                <select
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
                  disabled={uploading}
                >
                  {ACADEMIC_YEARS.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Template / current-data download */}
            {selectedEntity?.template && (
              <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-4 py-3 text-sm">
                <FileSpreadsheet className="w-4 h-4 text-[#003087] flex-shrink-0" />
                <span className="text-muted-foreground flex-1">
                  Downloads all current {academicYear} records (or a blank template if there are
                  none yet). Edit, add, or leave rows as-is, then upload the same file back —
                  changed cells update, new rows insert, everything else stays untouched.
                </span>
                <button
                  onClick={() => uploadService.downloadTemplate(entityType, academicYear)}
                  className="flex items-center gap-1.5 text-[#003087] font-medium hover:underline whitespace-nowrap"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </button>
              </div>
            )}

            {/* Drop zone */}
            <FileDropzone
              onFile={setFile}
              disabled={uploading}
              currentFile={file}
              onClear={() => setFile(null)}
            />

            {/* Progress bar */}
            {uploading && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Uploading and validating…</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-[#003087] rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Upload button */}
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium py-2.5 text-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Processing…</>
              ) : (
                <><Upload className="w-4 h-4" /> Upload & Validate</>
              )}
            </button>
          </div>

          {/* Result panel */}
          {result && (
            <UploadResultPanel result={result} onClose={() => setResult(null)} />
          )}
        </div>

        {/* Right — upload history */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-border bg-card p-5 space-y-4">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <h2 className="font-semibold text-foreground">Recent Uploads</h2>
              {!!jobsData?.items?.length && (
                <div className="flex items-center gap-3">
                  {stuckCount > 0 && (
                    <button
                      onClick={handleClearStuck}
                      disabled={clearing}
                      className="text-xs font-medium text-destructive hover:underline disabled:opacity-50"
                    >
                      Clear failed/processing ({stuckCount})
                    </button>
                  )}
                  <button
                    onClick={handleClearAll}
                    disabled={clearing}
                    className="text-xs font-medium text-muted-foreground hover:text-destructive hover:underline disabled:opacity-50 flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" /> Clear all
                  </button>
                </div>
              )}
            </div>

            {jobsLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-16 rounded-lg bg-muted/30 animate-pulse" />
                ))}
              </div>
            ) : jobsData?.items?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No uploads yet
              </p>
            ) : (
              <div className="space-y-2">
                {jobsData?.items?.map((job: any) => (
                  <div
                    key={job.id}
                    className="rounded-lg border border-border p-3 space-y-2 hover:bg-muted/20 transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {job.original_filename}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {ENTITY_TYPES.find((e) => e.value === job.entity_type)?.label} · {job.academic_year}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${STATUS_COLORS[job.status as keyof typeof STATUS_COLORS]}`}>
                          {STATUS_ICONS[job.status as keyof typeof STATUS_ICONS]}
                          {job.status}
                        </span>
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          disabled={deletingId === job.id}
                          title="Remove from history"
                          className="p-0.5 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition disabled:opacity-50"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="text-green-600">{job.inserted_rows} inserted</span>
                      {job.updated_rows > 0 && <span className="text-blue-600">{job.updated_rows} updated</span>}
                      {job.error_rows > 0 && (
                        <>
                          <span className="text-destructive">{job.error_rows} errors</span>
                          <button
                            onClick={() => uploadService.downloadErrorReport(job.id)}
                            className="text-[#003087] hover:underline flex items-center gap-0.5"
                          >
                            <Download className="w-3 h-3" /> Report
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
