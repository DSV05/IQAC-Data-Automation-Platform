import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownAZ, ArrowUpAZ, ChevronLeft, ChevronRight, Filter, Search, X } from "lucide-react";

export type ExcelFilterColumn = {
  key: string;
  label: string;
  required?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
};

type SortDirection = "asc" | "desc";
type SortState = { key: string; direction: SortDirection } | null;

const BLANK_VALUE = "__excel_filter_blank__";

function valueId(value: unknown) {
  return value === null || value === undefined || value === "" ? BLANK_VALUE : `${typeof value}:${String(value)}`;
}

function displayValue(value: unknown, key: string) {
  if (value === null || value === undefined || value === "") return "(Blanks)";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (key === "month" && typeof value === "number") {
    return new Date(2024, value - 1).toLocaleString("en", { month: "short" });
  }
  return String(value);
}

function columnType(column: ExcelFilterColumn, rows: any[]) {
  if (/(date|year|month)/i.test(column.key)) return "date";
  const values = rows.map((row) => row[column.key]).filter((value) => value !== null && value !== undefined && value !== "");
  return values.length > 0 && values.every((value) => typeof value === "number") ? "number" : "text";
}

function sortValue(value: unknown, type: string) {
  if (value === null || value === undefined || value === "") return "";
  if (type === "number") return Number(value);
  if (type === "date") {
    const date = new Date(String(value));
    return Number.isNaN(date.getTime()) ? Number(value) || 0 : date.getTime();
  }
  return String(value).toLocaleLowerCase();
}

/** A shared Excel-like filter and sort table for every Master Data category. */
export default function ExcelFilterTable({
  columns,
  rows,
  resetKey,
  pageSize = 15,
  emptyMessage,
  renderActions,
}: {
  columns: ExcelFilterColumn[];
  rows: any[];
  resetKey: string;
  pageSize?: number;
  emptyMessage: string;
  renderActions?: (row: any) => React.ReactNode;
}) {
  const [filters, setFilters] = useState<Record<string, string[]>>({});
  const [sort, setSort] = useState<SortState>(null);
  const [openColumn, setOpenColumn] = useState<string | null>(null);
  const [valueSearch, setValueSearch] = useState("");
  const [page, setPage] = useState(1);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // A category/year/search result is a different dataset. Its filters must not
  // leak into the next dataset when the user switches category or year.
  useEffect(() => {
    setFilters({});
    setSort(null);
    setOpenColumn(null);
    setValueSearch("");
    setPage(1);
  }, [resetKey]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) setOpenColumn(null);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const filteredRows = useMemo(() => rows.filter((row) =>
    Object.entries(filters).every(([key, selected]) => selected.includes(valueId(row[key]))),
  ), [rows, filters]);

  const sortedRows = useMemo(() => {
    if (!sort) return filteredRows;
    const type = columnType(columns.find((column) => column.key === sort.key)!, rows);
    return [...filteredRows].sort((a, b) => {
      const left = sortValue(a[sort.key], type);
      const right = sortValue(b[sort.key], type);
      const comparison = typeof left === "number" && typeof right === "number"
        ? left - right
        : String(left).localeCompare(String(right), undefined, { numeric: true });
      return sort.direction === "asc" ? comparison : -comparison;
    });
  }, [columns, filteredRows, rows, sort]);

  const pages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const currentPage = Math.min(page, pages);
  const visibleRows = sortedRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const openFilter = (key: string) => {
    setOpenColumn((open) => open === key ? null : key);
    setValueSearch("");
  };
  const updateFilter = (key: string, values: string[]) => {
    setFilters((current) => ({ ...current, [key]: values }));
    setPage(1);
  };
  const clearFilter = (key: string) => {
    setFilters((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
    setPage(1);
  };

  return (
    <div ref={wrapperRef} className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground"><strong>{sortedRows.length}</strong> filtered record{sortedRows.length !== 1 ? "s" : ""}</span>
        <span className="text-muted-foreground text-xs">Page {currentPage} of {pages}</span>
      </div>

      <div className="rounded-xl border border-border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {columns.map((column) => {
                const type = columnType(column, rows);
                const uniqueValues = Array.from(new Map(rows.map((row) => {
                  const value = row[column.key];
                  return [valueId(value), { id: valueId(value), label: displayValue(value, column.key), sort: sortValue(value, type) }];
                })).values()).sort((a, b) => typeof a.sort === "number" && typeof b.sort === "number" ? a.sort - b.sort : String(a.label).localeCompare(String(b.label), undefined, { numeric: true }));
                const searchedValues = uniqueValues.filter((value) => value.label.toLocaleLowerCase().includes(valueSearch.toLocaleLowerCase()));
                const selected = filters[column.key];
                const allSelected = selected === undefined || (selected.length === uniqueValues.length && uniqueValues.every((value) => selected.includes(value.id)));
                const isActive = selected !== undefined && !allSelected;
                const sortLabels = type === "number"
                  ? ["Smallest to Largest", "Largest to Smallest"]
                  : type === "date" ? ["Oldest to Newest", "Newest to Oldest"] : ["Sort A to Z", "Sort Z to A"];

                return (
                  <th key={column.key} className="relative text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">
                    <div className="flex items-center gap-1">
                      <span>{column.label}{column.required && <span className="text-destructive ml-0.5">*</span>}</span>
                      <button
                        type="button"
                        aria-label={`Filter ${column.label}`}
                        aria-expanded={openColumn === column.key}
                        onClick={() => openFilter(column.key)}
                        className={`rounded p-0.5 transition hover:bg-muted-foreground/15 ${isActive ? "text-[#003087] bg-[#003087]/10" : "text-muted-foreground"}`}
                      >
                        <Filter className="w-3.5 h-3.5" fill={isActive ? "currentColor" : "none"} />
                      </button>
                    </div>
                    {openColumn === column.key && (
                      <div onClick={(event) => event.stopPropagation()} className="absolute left-2 top-full z-30 mt-1 w-72 rounded-lg border border-border bg-card p-2 text-left normal-case shadow-xl">
                        <button type="button" onClick={() => { setSort({ key: column.key, direction: "asc" }); setPage(1); }} className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-foreground hover:bg-muted">
                          <ArrowDownAZ className="w-3.5 h-3.5" /> {sortLabels[0]}
                        </button>
                        <button type="button" onClick={() => { setSort({ key: column.key, direction: "desc" }); setPage(1); }} className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-foreground hover:bg-muted">
                          <ArrowUpAZ className="w-3.5 h-3.5" /> {sortLabels[1]}
                        </button>
                        <div className="my-2 border-t border-border" />
                        <div className="relative mb-2">
                          <Search className="absolute left-2 top-1/2 w-3.5 h-3.5 -translate-y-1/2 text-muted-foreground" />
                          <input autoFocus value={valueSearch} onChange={(event) => setValueSearch(event.target.value)} placeholder="Search values" className="w-full rounded border border-input bg-background py-1.5 pl-7 pr-2 text-xs font-normal text-foreground outline-none focus:ring-1 focus:ring-[#003087]" />
                        </div>
                        <label className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-xs font-medium text-foreground hover:bg-muted">
                          <input type="checkbox" checked={allSelected} onChange={(event) => updateFilter(column.key, event.target.checked ? uniqueValues.map((value) => value.id) : [])} />
                          Select All
                        </label>
                        <div className="max-h-48 overflow-y-auto border-y border-border py-1">
                          {searchedValues.map((value) => (
                            <label key={value.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-xs font-normal text-foreground hover:bg-muted">
                              <input type="checkbox" checked={selected === undefined || selected.includes(value.id)} onChange={(event) => {
                                const current = selected ?? uniqueValues.map((item) => item.id);
                                updateFilter(column.key, event.target.checked ? [...new Set([...current, value.id])] : current.filter((id) => id !== value.id));
                              }} />
                              <span className="truncate" title={value.label}>{value.label}</span>
                            </label>
                          ))}
                          {searchedValues.length === 0 && <p className="px-2 py-3 text-xs font-normal text-muted-foreground">No matching values</p>}
                        </div>
                        <button type="button" disabled={!isActive} onClick={() => clearFilter(column.key)} className="mt-2 flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs font-medium text-[#003087] hover:bg-[#003087]/5 disabled:cursor-not-allowed disabled:opacity-40">
                          <X className="w-3.5 h-3.5" /> Clear Filter From {column.label}
                        </button>
                      </div>
                    )}
                  </th>
                );
              })}
              {renderActions && <th className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {visibleRows.length === 0 ? (
              <tr><td colSpan={columns.length + (renderActions ? 1 : 0)} className="px-4 py-12 text-center text-muted-foreground">{emptyMessage}</td></tr>
            ) : visibleRows.map((row) => (
              <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/20 transition">
                {columns.map((column) => <td key={column.key} className="px-4 py-3 text-foreground whitespace-nowrap">{column.render ? column.render(row[column.key], row) : (row[column.key] ?? "—")}</td>)}
                {renderActions && <td className="px-4 py-3 whitespace-nowrap">{renderActions(row)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && <div className="flex items-center justify-end gap-2">
        <button disabled={currentPage === 1} onClick={() => setPage((value) => value - 1)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition"><ChevronLeft className="w-3.5 h-3.5" /> Prev</button>
        <span className="text-sm text-muted-foreground px-2">{currentPage} / {pages}</span>
        <button disabled={currentPage === pages} onClick={() => setPage((value) => value + 1)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition">Next <ChevronRight className="w-3.5 h-3.5" /></button>
      </div>}
    </div>
  );
}
