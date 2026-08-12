import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users, GraduationCap, BookOpen, Lightbulb, Briefcase,
  Zap, Droplets, Trash2, Award, Handshake,
  CalendarDays, Leaf, ChevronRight, Pencil, X, RefreshCw,
} from "lucide-react";
import apiClient from "@/services/api";

// ── Academic year selector ────────────────────────────────────────────────────

const YEARS = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];

// ── Tab definitions ───────────────────────────────────────────────────────────

const TABS = [
  { key: "faculty",    label: "Faculty",       icon: Users,        color: "text-blue-600  bg-blue-50" },
  { key: "students",   label: "Students",      icon: GraduationCap,color: "text-green-600 bg-green-50" },
  { key: "research",   label: "Research",      icon: BookOpen,     color: "text-purple-600 bg-purple-50" },
  { key: "patents",    label: "Patents",       icon: Lightbulb,    color: "text-amber-600 bg-amber-50" },
  { key: "placements", label: "Placements",    icon: Briefcase,    color: "text-teal-600  bg-teal-50" },
  { key: "mous",       label: "MoUs",          icon: Handshake,    color: "text-indigo-600 bg-indigo-50" },
  { key: "events",     label: "Events",        icon: CalendarDays, color: "text-pink-600  bg-pink-50" },
  { key: "energy",     label: "Energy",        icon: Zap,          color: "text-yellow-600 bg-yellow-50" },
  { key: "water",      label: "Water",         icon: Droplets,     color: "text-cyan-600  bg-cyan-50" },
  { key: "waste",      label: "Waste",         icon: Trash2,       color: "text-red-600   bg-red-50" },
  { key: "awards",     label: "Awards",        icon: Award,        color: "text-orange-600 bg-orange-50" },
  { key: "sdg",        label: "SDG",           icon: Leaf,         color: "text-emerald-600 bg-emerald-50" },
];

export default function MasterDataPage() {
  const [activeTab, setActiveTab] = useState("faculty");
  const [year, setYear] = useState("2024-25");

  const activeTabDef = TABS.find((t) => t.key === activeTab)!;
  const Icon = activeTabDef.icon;

  return (
    <div className="flex h-full">
      {/* Left sidebar — entity tabs */}
      <aside className="w-56 flex-shrink-0 border-r border-border bg-muted/20 p-3 space-y-0.5">
        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Data Categories
        </div>
        {TABS.map((tab) => {
          const TabIcon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-[#003087] text-white"
                  : "text-foreground hover:bg-muted"
              }`}
            >
              <TabIcon className="w-4 h-4 flex-shrink-0" />
              <span>{tab.label}</span>
              {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
            </button>
          );
        })}
      </aside>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${activeTabDef.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">{activeTabDef.label}</h1>
                <p className="text-xs text-muted-foreground">Master data — year-wise records</p>
              </div>
            </div>

            {/* Year selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Academic Year:</label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="rounded-lg border border-input bg-background text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#003087]"
              >
                {YEARS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Tab content */}
          <EntityTable entity={activeTab} year={year} />
        </div>
      </div>
    </div>
  );
}

// ── Column definitions per entity ─────────────────────────────────────────────

const COLUMNS: Record<string, { key: string; label: string; render?: (v: any, row: any) => React.ReactNode }[]> = {
  faculty: [
    { key: "employee_id", label: "Emp ID" },
    { key: "full_name", label: "Name" },
    { key: "designation", label: "Designation", render: (v) => <span className="capitalize">{v?.replace("_", " ")}</span> },
    { key: "qualification", label: "Qualification", render: (v) => <span className="uppercase">{v}</span> },
    { key: "employment_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "experience_teaching", label: "Exp (Yrs)", render: (v) => `${v}y` },
    { key: "phd_awarded", label: "PhD", render: (v) => v ? <span className="text-green-600 font-medium">Yes</span> : <span className="text-muted-foreground">No</span> },
    { key: "is_active", label: "Status", render: (v) => <StatusPill active={v} /> },
  ],
  students: [
    { key: "enrollment_no", label: "Enrollment No" },
    { key: "full_name", label: "Name" },
    { key: "gender", label: "Gender", render: (v) => <span className="capitalize">{v}</span> },
    { key: "category", label: "Category", render: (v) => <span className="uppercase text-xs">{v}</span> },
    { key: "current_year", label: "Year" },
    { key: "admission_type", label: "Admission", render: (v) => <Badge value={v} /> },
    { key: "cgpa", label: "CGPA", render: (v) => v ?? "—" },
    { key: "is_active", label: "Status", render: (v) => <StatusPill active={v} /> },
  ],
  research: [
    { key: "title", label: "Title", render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "category", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "publication_year", label: "Year" },
    { key: "indexing", label: "Index", render: (v) => <span className="uppercase text-xs font-medium">{v}</span> },
    { key: "impact_factor", label: "IF", render: (v) => v ?? "—" },
    { key: "citations", label: "Citations" },
    { key: "is_verified", label: "Verified", render: (v) => v ? <span className="text-green-600">✓</span> : <span className="text-muted-foreground">—</span> },
  ],
  patents: [
    { key: "title", label: "Title", render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "application_number", label: "App No" },
    { key: "status", label: "Status", render: (v) => <Badge value={v} /> },
    { key: "country", label: "Country" },
    { key: "filing_date", label: "Filed", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "grant_date", label: "Granted", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
  ],
  placements: [
    { key: "student_name", label: "Student" },
    { key: "company_name", label: "Company" },
    { key: "designation", label: "Role" },
    { key: "package_lpa", label: "Package (LPA)", render: (v) => v ? `₹${v}L` : "—" },
    { key: "placement_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "is_international", label: "International", render: (v) => v ? <span className="text-blue-600">✓</span> : "—" },
    { key: "is_verified", label: "Verified", render: (v) => v ? <span className="text-green-600">✓</span> : "—" },
  ],
  mous: [
    { key: "partner_name", label: "Partner" },
    { key: "partner_country", label: "Country" },
    { key: "partner_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "signed_date", label: "Signed", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "valid_until", label: "Valid Until", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "activities_conducted", label: "Activities" },
    { key: "is_active", label: "Active", render: (v) => <StatusPill active={v} /> },
  ],
  events: [
    { key: "title", label: "Title", render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "event_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "start_date", label: "Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "participants_count", label: "Participants" },
    { key: "is_organized", label: "Role", render: (v) => v ? "Organized" : "Attended" },
    { key: "is_international", label: "International", render: (v) => v ? <span className="text-blue-600">✓</span> : "—" },
  ],
  energy: [
    { key: "month", label: "Month", render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "electricity_kwh", label: "Grid (kWh)", render: (v) => v.toLocaleString() },
    { key: "solar_kwh", label: "Solar (kWh)", render: (v) => v.toLocaleString() },
    { key: "diesel_liters", label: "Diesel (L)", render: (v) => v.toLocaleString() },
    { key: "ghg_scope1_tco2e", label: "Scope 1 (tCO₂e)", render: (v) => v?.toFixed(2) ?? "—" },
    { key: "ghg_scope2_tco2e", label: "Scope 2 (tCO₂e)", render: (v) => v?.toFixed(2) ?? "—" },
  ],
  water: [
    { key: "month", label: "Month", render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "municipal_kl", label: "Municipal (kL)" },
    { key: "borewell_kl", label: "Borewell (kL)" },
    { key: "rainwater_harvested_kl", label: "Harvested (kL)" },
    { key: "recycled_treated_kl", label: "Recycled (kL)" },
  ],
  waste: [
    { key: "month", label: "Month", render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "waste_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "generated_kg", label: "Generated (kg)" },
    { key: "recycled_kg", label: "Recycled (kg)" },
    { key: "disposed_kg", label: "Disposed (kg)" },
    { key: "disposal_method", label: "Method" },
  ],
  awards: [
    { key: "recipient_name", label: "Recipient" },
    { key: "title", label: "Award", render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "awarding_body", label: "Given By" },
    { key: "recipient_type", label: "Type", render: (v) => <Badge value={v} /> },
    { key: "award_date", label: "Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "is_international", label: "International", render: (v) => v ? <span className="text-blue-600">✓</span> : "—" },
  ],
  sdg: [
    { key: "title", label: "Activity", render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "sdg_primary", label: "SDG", render: (v) => <SDGBadge goal={v} /> },
    { key: "activity_type", label: "Type", render: (v) => <span className="capitalize">{v}</span> },
    { key: "beneficiaries_count", label: "Beneficiaries", render: (v) => v ?? "—" },
    { key: "investment_inr", label: "Investment", render: (v) => v ? `₹${(v / 100000).toFixed(1)}L` : "—" },
  ],
};

// ── Inline-editable entities ───────────────────────────────────────────────────
// Only fields safe to bulk/inline-edit are listed here (mirrors what the
// backend's PUT endpoint actually accepts) — identity fields like enrollment_no,
// name, gender, etc. are intentionally not editable here to avoid accidental
// changes to a student's core record.
type EditFieldType = "number" | "text" | "textarea" | "checkbox";
interface EditFieldDef {
  key: string;
  label: string;
  type: EditFieldType;
  step?: string;
}

const EDITABLE_ENTITY_FIELDS: Record<string, EditFieldDef[]> = {
  students: [
    { key: "current_year", label: "Current Year", type: "number" },
    { key: "cgpa", label: "CGPA", type: "number", step: "0.01" },
    { key: "sgpa_last", label: "Last Semester SGPA", type: "number", step: "0.01" },
    { key: "backlogs", label: "Backlogs", type: "number" },
    { key: "is_active", label: "Active", type: "checkbox" },
    { key: "remarks", label: "Remarks", type: "textarea" },
  ],
};

// ── Entity table component ─────────────────────────────────────────────────────

function EntityTable({ entity, year }: { entity: string; year: string }) {
  const [page, setPage] = useState(1);
  const [editingRow, setEditingRow] = useState<any | null>(null);
  const PAGE_SIZE = 15;
  const qc = useQueryClient();

  const endpointMap: Record<string, string> = {
    faculty: "faculty", students: "students", research: "research",
    patents: "patents", placements: "placements", mous: "mous",
    events: "events", energy: "energy", water: "water",
    waste: "waste", awards: "awards", sdg: "sdg",
  };

  const endpoint = endpointMap[entity];

  const { data, isLoading, error } = useQuery({
    queryKey: ["master", entity, year, page],
    queryFn: async () => {
      const res = await apiClient.get(`/master/${endpoint}`, {
        params: { academic_year: year, page, size: PAGE_SIZE },
      });
      return res.data;
    },
    enabled: !!endpoint,
  });

  const columns = COLUMNS[entity] ?? [];
  const editFields = EDITABLE_ENTITY_FIELDS[entity];
  const isEditable = !!editFields;

  if (isLoading) return <TableSkeleton />;
  if (error) return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
      <p className="text-destructive text-sm">Failed to load data. Ensure the backend is running and migration 002 is applied.</p>
    </div>
  );

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  return (
    <div className="space-y-3">
      {/* Stats bar */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {total} records for <strong>{year}</strong>
        </span>
        <span className="text-muted-foreground text-xs">
          Page {page} of {pages}
        </span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {columns.map((col) => (
                <th key={col.key} className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">
                  {col.label}
                </th>
              ))}
              {isEditable && (
                <th className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (isEditable ? 1 : 0)} className="px-4 py-12 text-center text-muted-foreground">
                  No records found for {year}. Upload data via the Data Upload module.
                </td>
              </tr>
            ) : (
              items.map((row: any) => (
                <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/20 transition">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-foreground whitespace-nowrap">
                      {col.render ? col.render(row[col.key], row) : (row[col.key] ?? "—")}
                    </td>
                  ))}
                  {isEditable && (
                    <td className="px-4 py-3 whitespace-nowrap">
                      <button
                        onClick={() => setEditingRow(row)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-[#003087] hover:underline"
                      >
                        <Pencil className="w-3.5 h-3.5" /> Edit
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-end gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground px-2">{page} / {pages}</span>
          <button
            disabled={page === pages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition"
          >
            Next
          </button>
        </div>
      )}

      {editingRow && editFields && (
        <RecordEditModal
          entity={entity}
          row={editingRow}
          fields={editFields}
          onClose={() => setEditingRow(null)}
          onSaved={() => {
            setEditingRow(null);
            qc.invalidateQueries({ queryKey: ["master", entity, year] });
          }}
        />
      )}
    </div>
  );
}

// ── Helper components ─────────────────────────────────────────────────────────

function Badge({ value }: { value: string }) {
  return (
    <span className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground capitalize">
      {value?.replace(/_/g, " ")}
    </span>
  );
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
      {active ? "Active" : "Inactive"}
    </span>
  );
}

const SDG_COLORS: Record<number, string> = {
  1: "bg-red-600", 2: "bg-yellow-500", 3: "bg-green-600", 4: "bg-red-400",
  5: "bg-orange-500", 6: "bg-blue-400", 7: "bg-yellow-400", 8: "bg-red-500",
  9: "bg-orange-600", 10: "bg-pink-600", 11: "bg-orange-400", 12: "bg-amber-600",
  13: "bg-green-700", 14: "bg-blue-600", 15: "bg-green-500", 16: "bg-blue-700",
  17: "bg-blue-800",
};

function SDGBadge({ goal }: { goal: number }) {
  return (
    <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-white text-xs font-bold ${SDG_COLORS[goal] ?? "bg-gray-400"}`}>
      {goal}
    </span>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="h-10 bg-muted/40 border-b border-border" />
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-12 border-b border-border last:border-0 animate-pulse bg-muted/20" />
      ))}
    </div>
  );
}

// ── Inline record edit modal ────────────────────────────────────────────────────
// Generic across any entity listed in EDITABLE_ENTITY_FIELDS — only sends the
// fields defined for that entity, via the same PUT /master/{entity}/{id}
// endpoint the API already exposes.

function RecordEditModal({
  entity, row, fields, onClose, onSaved,
}: {
  entity: string;
  row: any;
  fields: EditFieldDef[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [values, setValues] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    for (const f of fields) initial[f.key] = row[f.key] ?? (f.type === "checkbox" ? false : "");
    return initial;
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {};
      for (const f of fields) {
        const v = values[f.key];
        if (f.type === "number") {
          payload[f.key] = v === "" || v === null ? null : Number(v);
        } else {
          payload[f.key] = v;
        }
      }
      const res = await apiClient.put(`/master/${entity}/${row.id}`, payload);
      return res.data;
    },
    onSuccess: onSaved,
    onError: (e: any) => setError(e?.response?.data?.detail || "Failed to save changes."),
  });

  const displayName = row.full_name || row.title || row.name || row.enrollment_no || row.employee_id || "Record";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-card border border-border shadow-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h3 className="font-semibold text-foreground">Edit Record</h3>
            <p className="text-xs text-muted-foreground truncate max-w-[280px]">{displayName}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3 max-h-[60vh] overflow-y-auto">
          {error && (
            <p className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</p>
          )}
          {fields.map((f) => (
            <div key={f.key} className="space-y-1">
              {f.type === "checkbox" ? (
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={!!values[f.key]}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.checked }))}
                    className="rounded border-input"
                  />
                  {f.label}
                </label>
              ) : (
                <>
                  <label className="text-xs font-medium text-muted-foreground">{f.label}</label>
                  {f.type === "textarea" ? (
                    <textarea
                      value={values[f.key] ?? ""}
                      onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                      rows={3}
                      className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
                    />
                  ) : (
                    <input
                      type={f.type === "number" ? "number" : "text"}
                      step={f.step}
                      value={values[f.key] ?? ""}
                      onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                      className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]"
                    />
                  )}
                </>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border">
          <button
            onClick={onClose}
            disabled={mutation.isPending}
            className="px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted rounded-lg transition"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#003087] hover:bg-[#002266] text-white rounded-lg transition disabled:opacity-50"
          >
            {mutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
