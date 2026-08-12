import { useState } from "react";
import {
  ShieldCheck, RefreshCw, Download, AlertTriangle, XCircle,
  CheckCircle2, Filter,
} from "lucide-react";
import { validationService } from "@/services/validation.service";

const ACADEMIC_YEARS = ["All years", "2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];

interface ValidationIssue {
  entity: string;
  record_id: string | null;
  academic_year: string | null;
  severity: "error" | "warning";
  issue_type: string;
  field: string | null;
  message: string;
  identifier: string | null;
}

interface ValidationReport {
  academic_year: string | null;
  summary: {
    total_records_scanned: number;
    total_issues: number;
    error_count: number;
    warning_count: number;
    issues_by_entity: Record<string, number>;
    issues_by_type: Record<string, number>;
  };
  issues: ValidationIssue[];
}

const ENTITY_LABELS: Record<string, string> = {
  faculty: "Faculty",
  students: "Students",
  programs: "Programs",
  placements: "Placements",
  higher_studies: "Higher Studies",
  research_publications: "Research Publications",
  patents: "Patents",
  funded_projects: "Funded Projects",
};

export default function ValidationPage() {
  const [academicYear, setAcademicYear] = useState("All years");
  const [running, setRunning] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [severityFilter, setSeverityFilter] = useState<"all" | "error" | "warning">("all");
  const [entityFilter, setEntityFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  const yearParam = academicYear === "All years" ? undefined : academicYear;

  const runChecks = async () => {
    setRunning(true);
    setError(null);
    try {
      const data = await validationService.run(yearParam);
      setReport(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to run validation checks.");
    } finally {
      setRunning(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await validationService.export(yearParam);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to export report.");
    } finally {
      setExporting(false);
    }
  };

  const filteredIssues = (report?.issues || []).filter((i) => {
    if (severityFilter !== "all" && i.severity !== severityFilter) return false;
    if (entityFilter !== "all" && i.entity !== entityFilter) return false;
    return true;
  });

  const entityOptions = report ? Object.keys(report.summary.issues_by_entity) : [];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-[#003087]" />
          Data Validation
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Scans master data for duplicate records, orphaned references, and missing or
          inconsistent fields required for NIRF/NAAC/AISHE submissions.
        </p>
      </div>

      {/* Controls */}
      <div className="rounded-xl border border-border bg-card p-5 flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">Academic Year</label>
          <select
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            className="rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
            disabled={running}
          >
            {ACADEMIC_YEARS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <button
          onClick={runChecks}
          disabled={running}
          className="flex items-center gap-2 rounded-lg bg-[#003087] hover:bg-[#002266] text-white font-medium px-4 py-2 text-sm transition disabled:opacity-50"
        >
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
          {running ? "Running checks…" : "Run Validation"}
        </button>

        {report && (
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 rounded-lg border border-border hover:bg-muted/50 font-medium px-4 py-2 text-sm transition disabled:opacity-50"
          >
            {exporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Export Excel
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 text-red-700 text-sm px-4 py-3 border border-red-200">
          {error}
        </div>
      )}

      {!report && !running && !error && (
        <div className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
          Click "Run Validation" to scan your data for duplicates, orphan references,
          and missing fields.
        </div>
      )}

      {report && (
        <>
          {/* Summary cards */}
          <div className="grid sm:grid-cols-4 gap-4">
            <SummaryCard label="Records Scanned" value={report.summary.total_records_scanned} icon={<CheckCircle2 className="w-4 h-4 text-[#003087]" />} />
            <SummaryCard label="Total Issues" value={report.summary.total_issues} icon={<ShieldCheck className="w-4 h-4 text-[#003087]" />} />
            <SummaryCard label="Errors" value={report.summary.error_count} icon={<XCircle className="w-4 h-4 text-red-600" />} accent="text-red-600" />
            <SummaryCard label="Warnings" value={report.summary.warning_count} icon={<AlertTriangle className="w-4 h-4 text-amber-500" />} accent="text-amber-500" />
          </div>

          {report.summary.total_issues === 0 ? (
            <div className="rounded-xl border border-green-200 bg-green-50 p-6 text-center text-green-700 flex flex-col items-center gap-2">
              <CheckCircle2 className="w-8 h-8" />
              <p className="font-medium">No issues found — data looks clean for {academicYear}.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3 p-4 border-b border-border">
                <Filter className="w-4 h-4 text-muted-foreground" />
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value as any)}
                  className="rounded-lg border border-input bg-background text-sm px-3 py-1.5"
                >
                  <option value="all">All severities</option>
                  <option value="error">Errors only</option>
                  <option value="warning">Warnings only</option>
                </select>
                <select
                  value={entityFilter}
                  onChange={(e) => setEntityFilter(e.target.value)}
                  className="rounded-lg border border-input bg-background text-sm px-3 py-1.5"
                >
                  <option value="all">All entities</option>
                  {entityOptions.map((e) => (
                    <option key={e} value={e}>{ENTITY_LABELS[e] || e} ({report.summary.issues_by_entity[e]})</option>
                  ))}
                </select>
                <span className="text-xs text-muted-foreground ml-auto">
                  Showing {filteredIssues.length} of {report.summary.total_issues} issues
                </span>
              </div>

              {/* Issue list */}
              <div className="divide-y divide-border max-h-[600px] overflow-y-auto">
                {filteredIssues.map((issue, idx) => (
                  <div key={idx} className="p-4 flex items-start gap-3 hover:bg-muted/20">
                    {issue.severity === "error" ? (
                      <XCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap text-xs mb-1">
                        <span className="font-medium text-foreground">
                          {ENTITY_LABELS[issue.entity] || issue.entity}
                        </span>
                        {issue.identifier && (
                          <span className="text-muted-foreground">· {issue.identifier}</span>
                        )}
                        {issue.academic_year && (
                          <span className="text-muted-foreground">· {issue.academic_year}</span>
                        )}
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[10px] uppercase tracking-wide">
                          {issue.issue_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{issue.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SummaryCard({
  label, value, icon, accent,
}: { label: string; value: number; icon: React.ReactNode; accent?: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
        {icon}
        {label}
      </div>
      <p className={`text-2xl font-bold ${accent || "text-foreground"}`}>{value}</p>
    </div>
  );
}
