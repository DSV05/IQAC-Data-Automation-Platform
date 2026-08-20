import { useEffect, useState } from "react";
import {
  ClipboardCheck, Filter, ChevronDown, ChevronRight, ChevronLeft,
  Pencil, Plus, Trash2, Upload, User as UserIcon, X, Search,
} from "lucide-react";
import { auditService, type AuditLogEntry } from "@/services/audit.service";

// Friendly labels for raw DB table names (audit entity_type is always the
// actual __tablename__, which doesn't always match the route/URL name
// used elsewhere — e.g. "research_publications" not "research").
const ENTITY_LABELS: Record<string, string> = {
  faculty: "Faculty",
  students: "Students",
  programs: "Programs",
  research_publications: "Research Publications",
  patents: "Patents",
  funded_projects: "Funded Projects",
  placements: "Placements",
  higher_studies: "Higher Studies",
  mous: "MoUs",
  events: "Events",
  energy_consumption: "Energy",
  water_consumption: "Water",
  waste_management: "Waste",
  awards: "Awards",
  consultancies: "Consultancy",
  sdg_activities: "SDG Activities",
  infrastructure: "Infrastructure",
  budgets: "Budgets",
  accreditations: "Accreditations",
};

const ACTION_META: Record<string, { icon: any; color: string; label: string }> = {
  create: { icon: Plus, color: "text-green-600 bg-green-50", label: "Created" },
  update: { icon: Pencil, color: "text-blue-600 bg-blue-50", label: "Updated" },
  delete: { icon: Trash2, color: "text-red-600 bg-red-50", label: "Deleted" },
};

function formatValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  return String(v);
}

function formatFieldName(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function timeAgo(iso: string): string {
  const d = new Date(iso);
  const diffMs = Date.now() - d.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const SIZE = 25;

  const [filters, setFilters] = useState({
    entity_type: "", action: "", source: "", q: "",
    date_from: "", date_to: "",
  });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    auditService.entityTypes().then(setEntityTypes).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    auditService
      .list({
        page, size: SIZE,
        entity_type: filters.entity_type || undefined,
        action: filters.action || undefined,
        source: filters.source || undefined,
        q: filters.q || undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
      })
      .then((res) => {
        setLogs(res.items);
        setTotal(res.total);
        setPages(res.pages || 1);
      })
      .catch(() => setError("Failed to load audit logs. Ensure the backend is running."))
      .finally(() => setLoading(false));
  }, [page, filters]);

  useEffect(() => { setPage(1); }, [filters]);

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <ClipboardCheck className="w-6 h-6 text-[#003087]" />
            Audit Logs
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Every create, update, and delete across master data — who, what changed, and when.
          </p>
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-medium transition ${
            activeFilterCount > 0
              ? "border-[#003087] text-[#003087] bg-[#003087]/5"
              : "border-input text-muted-foreground hover:bg-muted"
          }`}
        >
          <Filter className="w-3.5 h-3.5" />
          Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
        </button>
      </div>

      {showFilters && (
        <div className="rounded-xl border border-border bg-card p-4 grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Entity</label>
            <select
              value={filters.entity_type}
              onChange={(e) => setFilters((f) => ({ ...f, entity_type: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2"
            >
              <option value="">All entities</option>
              {entityTypes.map((t) => (
                <option key={t} value={t}>{ENTITY_LABELS[t] ?? t}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Action</label>
            <select
              value={filters.action}
              onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2"
            >
              <option value="">All actions</option>
              <option value="create">Created</option>
              <option value="update">Updated</option>
              <option value="delete">Deleted</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Source</label>
            <select
              value={filters.source}
              onChange={(e) => setFilters((f) => ({ ...f, source: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2"
            >
              <option value="">Manual edits &amp; uploads</option>
              <option value="manual_edit">Manual edit only</option>
              <option value="upload">Upload only</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">From</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">To</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Record name</label>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                value={filters.q}
                onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
                placeholder="e.g. Chavvi Banik"
                className="w-full rounded-lg border border-input bg-background text-sm pl-8 pr-3 py-2"
              />
            </div>
          </div>
          {activeFilterCount > 0 && (
            <div className="col-span-full">
              <button
                onClick={() => setFilters({ entity_type: "", action: "", source: "", q: "", date_from: "", date_to: "" })}
                className="text-xs text-muted-foreground hover:text-destructive flex items-center gap-1"
              >
                <X className="w-3 h-3" /> Clear filters
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center text-sm text-destructive">
          {error}
        </div>
      )}

      {!error && (
        <div className="rounded-xl border border-border overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-sm text-muted-foreground">Loading…</div>
          ) : logs.length === 0 ? (
            <div className="p-12 text-center text-sm text-muted-foreground">
              No audit entries match these filters.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {logs.map((log) => {
                const meta = ACTION_META[log.action] ?? ACTION_META.update;
                const ActionIcon = meta.icon;
                const isOpen = !!expanded[log.id];
                const fieldCount = Object.keys(log.changes || {}).length;
                return (
                  <div key={log.id}>
                    <button
                      onClick={() => setExpanded((e) => ({ ...e, [log.id]: !e[log.id] }))}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/30 transition"
                    >
                      {isOpen ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      )}
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${meta.color}`}>
                        <ActionIcon className="w-3 h-3" />
                        {meta.label}
                      </span>
                      <span className="text-xs font-medium text-muted-foreground flex-shrink-0">
                        {ENTITY_LABELS[log.entity_type] ?? log.entity_type}
                      </span>
                      <span className="text-sm font-medium text-foreground truncate flex-1">
                        {log.entity_label ?? log.entity_id}
                      </span>
                      <span className="text-xs text-muted-foreground flex-shrink-0 hidden sm:inline">
                        {fieldCount} field{fieldCount !== 1 ? "s" : ""} changed
                      </span>
                      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground flex-shrink-0">
                        {log.source === "upload" ? <Upload className="w-3 h-3" /> : <UserIcon className="w-3 h-3" />}
                        {log.changed_by_name ?? "System"}
                      </span>
                      <span className="text-xs text-muted-foreground flex-shrink-0 w-20 text-right" title={new Date(log.created_at).toLocaleString("en-IN")}>
                        {timeAgo(log.created_at)}
                      </span>
                    </button>

                    {isOpen && (
                      <div className="px-4 pb-4 pl-11">
                        <div className="rounded-lg border border-border overflow-hidden">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="bg-muted/40 text-muted-foreground">
                                <th className="text-left px-3 py-2 font-medium">Field</th>
                                <th className="text-left px-3 py-2 font-medium">Before</th>
                                <th className="text-left px-3 py-2 font-medium">After</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(log.changes || {}).map(([field, diff]) => (
                                <tr key={field} className="border-t border-border">
                                  <td className="px-3 py-2 font-medium text-foreground whitespace-nowrap">
                                    {formatFieldName(field)}
                                  </td>
                                  <td className="px-3 py-2 text-muted-foreground">
                                    {log.action === "create" ? "—" : formatValue(diff.old)}
                                  </td>
                                  <td className="px-3 py-2 text-foreground">
                                    {log.action === "delete" ? (
                                      <span className="text-destructive">deleted</span>
                                    ) : (
                                      formatValue(diff.new)
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="mt-2 text-[11px] text-muted-foreground">
                          {new Date(log.created_at).toLocaleString("en-IN", {
                            dateStyle: "medium", timeStyle: "medium",
                          })}
                          {log.academic_year && <> · {log.academic_year}</>}
                          <> · via {log.source === "upload" ? "bulk upload" : "manual edit"}</>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {!error && !loading && pages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{total} total entries</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border hover:bg-muted disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <span className="text-muted-foreground px-2">{page} / {pages}</span>
            <button
              disabled={page === pages}
              onClick={() => setPage((p) => p + 1)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border hover:bg-muted disabled:opacity-40 transition"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
