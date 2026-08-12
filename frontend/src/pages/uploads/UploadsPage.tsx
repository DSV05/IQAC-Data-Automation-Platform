import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Upload, Download, FileSpreadsheet, CheckCircle,
  XCircle, AlertTriangle, Clock, RefreshCw,
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
  { value: "water",          label: "Water Consumption", template: false },
  { value: "waste",          label: "Waste Management",  template: false },
  { value: "awards",         label: "Awards",            template: false },
  { value: "consultancy",    label: "Consultancy",       template: false },
  { value: "sdg_activities", label: "SDG Activities",    template: false },
];

// Entities whose natural key (enrollment_no, employee_id) lets Update Mode
// find and patch existing records instead of only inserting new ones.
const UPDATE_MODE_SUPPORTED = ["students", "faculty"];

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
  const [uploadMode, setUploadMode] = useState<"insert" | "update">("insert");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["upload-jobs"],
    queryFn: () => uploadService.listJobs({ size: 20 }),
    refetchInterval: 5000,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setResult(null);
    try {
      const res = await uploadService.uploadFile(
        file, entityType, academicYear, undefined,
        (pct) => setProgress(pct),
        supportsUpdateMode ? uploadMode : "insert",
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
  const supportsUpdateMode = UPDATE_MODE_SUPPORTED.includes(entityType);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Data Upload</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload Excel or CSV files to populate master data tables. Download templates to ensure correct format.
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
                    if (!UPDATE_MODE_SUPPORTED.includes(e.target.value)) setUploadMode("insert");
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

            {/* Update Mode toggle */}
            {supportsUpdateMode && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Upload Mode</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setUploadMode("insert")}
                    disabled={uploading}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                      uploadMode === "insert"
                        ? "border-[#003087] bg-[#003087]/5 text-[#003087]"
                        : "border-input text-muted-foreground hover:bg-muted/40"
                    }`}
                  >
                    Insert New Records
                  </button>
                  <button
                    type="button"
                    onClick={() => setUploadMode("update")}
                    disabled={uploading}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                      uploadMode === "update"
                        ? "border-[#003087] bg-[#003087]/5 text-[#003087]"
                        : "border-input text-muted-foreground hover:bg-muted/40"
                    }`}
                  >
                    Update Existing Records
                  </button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {uploadMode === "update" ? (
                    <>
                      Only the ID column ({entityType === "students" ? "Enrollment No" : "Employee ID"}) is required
                      — include just that plus whichever fields you want to change (e.g. CGPA). Rows with no
                      matching existing record are skipped, not inserted.
                    </>
                  ) : (
                    <>Creates new records. If a row matches an existing record, it updates that record instead of failing.</>
                  )}
                </p>
              </div>
            )}

            {/* Template download */}
            {selectedEntity?.template && (
              <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-4 py-3 text-sm">
                <FileSpreadsheet className="w-4 h-4 text-[#003087] flex-shrink-0" />
                <span className="text-muted-foreground flex-1">
                  Download the template to ensure correct column format
                </span>
                <button
                  onClick={() => uploadService.downloadTemplate(entityType)}
                  className="flex items-center gap-1.5 text-[#003087] font-medium hover:underline whitespace-nowrap"
                >
                  <Download className="w-3.5 h-3.5" />
                  Template
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
            <h2 className="font-semibold text-foreground">Recent Uploads</h2>

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
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${STATUS_COLORS[job.status as keyof typeof STATUS_COLORS]}`}>
                        {STATUS_ICONS[job.status as keyof typeof STATUS_ICONS]}
                        {job.status}
                      </span>
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
