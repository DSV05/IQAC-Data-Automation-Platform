import { CheckCircle, XCircle, AlertTriangle, Download } from "lucide-react";
import { uploadService } from "@/services/upload.service";

interface UploadResult {
  job_id: string;
  status: "completed" | "partial" | "failed";
  total_rows: number;
  inserted_rows: number;
  updated_rows: number;
  error_rows: number;
  skipped_rows: number;
  skipped_existing?: number;
  skipped_validation?: number;
  mode?: "insert" | "update";
  errors: { row: number; field: string; value: string; error: string }[];
  has_more_errors: boolean;
}

interface UploadResultPanelProps {
  result: UploadResult;
  onClose: () => void;
}

export function UploadResultPanel({ result, onClose }: UploadResultPanelProps) {
  const isSuccess  = result.status === "completed";
  const isPartial  = result.status === "partial";

  const Icon   = isSuccess ? CheckCircle : isPartial ? AlertTriangle : XCircle;
  const color  = isSuccess ? "text-green-600" : isPartial ? "text-amber-600" : "text-destructive";
  const bgColor = isSuccess ? "bg-green-50 border-green-200" : isPartial ? "bg-amber-50 border-amber-200" : "bg-destructive/5 border-destructive/20";
  const title  = isSuccess ? "Upload Successful!" : isPartial ? "Upload Partially Successful" : "Upload Failed";

  return (
    <div className={`rounded-xl border p-5 space-y-4 ${bgColor}`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Icon className={`w-6 h-6 ${color} flex-shrink-0`} />
          <div>
            <h3 className={`font-semibold ${color}`}>{title}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Job ID: {result.job_id.slice(0, 8)}…
            </p>
          </div>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: "Total Rows",   value: result.total_rows,    color: "text-foreground" },
          { label: "Inserted",     value: result.inserted_rows, color: "text-green-700" },
          { label: "Updated",      value: result.updated_rows,  color: "text-blue-700" },
          { label: "Skipped",      value: result.skipped_rows,  color: "text-amber-700" },
          { label: "Errors",       value: result.error_rows,    color: "text-destructive" },
        ].map((stat) => (
          <div key={stat.label} className="bg-background rounded-lg p-3 text-center border border-border/50">
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {typeof result.skipped_existing === "number" && result.skipped_existing > 0 && (
        <p className="text-xs text-muted-foreground bg-background rounded-lg border border-border/50 px-3 py-2">
          {result.mode === "update" ? (
            <>
              <strong>{result.skipped_existing}</strong> row{result.skipped_existing === 1 ? "" : "s"} skipped
              because no existing record matched — Update Mode only updates records that already exist.
            </>
          ) : (
            <>
              <strong>{result.skipped_existing}</strong> row{result.skipped_existing === 1 ? "" : "s"} skipped
              (already existed and had nothing new to change, or were missing required data for a new record).
            </>
          )}
        </p>
      )}

      {/* Errors table */}
      {result.errors.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-foreground">
              Validation Errors {result.has_more_errors ? `(showing first ${result.errors.length})` : ""}
            </h4>
            <button
              onClick={() => uploadService.downloadErrorReport(result.job_id)}
              className="flex items-center gap-1.5 text-xs text-[#003087] hover:underline"
            >
              <Download className="w-3.5 h-3.5" />
              Download Full Report
            </button>
          </div>
          <div className="rounded-lg border border-border overflow-hidden text-xs">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground">Row</th>
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground">Field</th>
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground">Value</th>
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground">Error</th>
                </tr>
              </thead>
              <tbody>
                {result.errors.map((err, i) => (
                  <tr key={i} className="border-b border-border last:border-0 bg-destructive/3">
                    <td className="px-3 py-2 text-destructive font-medium">{err.row}</td>
                    <td className="px-3 py-2 font-mono text-foreground">{err.field}</td>
                    <td className="px-3 py-2 text-muted-foreground truncate max-w-[120px]">{err.value || "—"}</td>
                    <td className="px-3 py-2 text-destructive">{err.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
