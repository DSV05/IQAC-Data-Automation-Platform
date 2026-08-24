/**
 * GlobalSearchPage
 * ─────────────────
 * Searches across all master data categories: faculty, students, research,
 * patents, placements, MoUs, events, awards, SDG, funded projects,
 * higher studies, and consultancy.
 */

import React, { useState, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, X, Users, GraduationCap, BookOpen,
  Lightbulb, Briefcase, Handshake, CalendarDays, Award,
  Leaf, FolderOpen, TrendingUp, Building2, ChevronRight,
  Loader2, AlertCircle, SlidersHorizontal,
} from "lucide-react";
import {
  globalSearch,
  ALL_CATEGORIES,
  SearchCategory,
  SearchHit,
} from "@/services/global-search.service";

// ── Constants ─────────────────────────────────────────────────────────────────

const YEARS = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];

const CATEGORY_META: Record<
  SearchCategory,
  { label: string; Icon: React.ElementType; color: string; bg: string }
> = {
  faculty:        { label: "Faculty",         Icon: Users,         color: "text-blue-700",    bg: "bg-blue-50 border-blue-200"   },
  students:       { label: "Students",        Icon: GraduationCap, color: "text-green-700",   bg: "bg-green-50 border-green-200" },
  research:       { label: "Research",        Icon: BookOpen,      color: "text-purple-700",  bg: "bg-purple-50 border-purple-200"},
  patents:        { label: "Patents",         Icon: Lightbulb,     color: "text-amber-700",   bg: "bg-amber-50 border-amber-200" },
  placements:     { label: "Placements",      Icon: Briefcase,     color: "text-teal-700",    bg: "bg-teal-50 border-teal-200"   },
  mous:           { label: "MoUs",            Icon: Handshake,     color: "text-indigo-700",  bg: "bg-indigo-50 border-indigo-200"},
  events:         { label: "Events",          Icon: CalendarDays,  color: "text-pink-700",    bg: "bg-pink-50 border-pink-200"   },
  awards:         { label: "Awards",          Icon: Award,         color: "text-orange-700",  bg: "bg-orange-50 border-orange-200"},
  sdg:            { label: "SDG Activities",  Icon: Leaf,          color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200"},
  funded_projects:{ label: "Funded Projects", Icon: FolderOpen,    color: "text-rose-700",    bg: "bg-rose-50 border-rose-200"   },
  higher_studies: { label: "Higher Studies",  Icon: TrendingUp,    color: "text-cyan-700",    bg: "bg-cyan-50 border-cyan-200"   },
  consultancy:    { label: "Consultancy",     Icon: Building2,     color: "text-slate-700",   bg: "bg-slate-50 border-slate-200" },
};

// ── Debounce hook ──────────────────────────────────────────────────────────────

function useDebounce<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value);
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

// ── Hit card ──────────────────────────────────────────────────────────────────

function HitCard({ hit }: { hit: SearchHit }) {
  const meta = CATEGORY_META[hit.category as SearchCategory];
  if (!meta) return null;
  const { Icon, color, bg } = meta;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${bg} hover:shadow-sm transition-shadow cursor-default`}>
      <div className={`mt-0.5 flex-shrink-0 ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 truncate">{hit.label}</p>
        {hit.sublabel && (
          <p className="text-xs text-gray-500 truncate mt-0.5">{hit.sublabel}</p>
        )}
      </div>
      {hit.academic_year && (
        <span className="flex-shrink-0 text-xs text-gray-400 font-mono">{hit.academic_year}</span>
      )}
    </div>
  );
}

// ── Category section ──────────────────────────────────────────────────────────

function CategorySection({
  category,
  hits,
  collapsed,
  onToggle,
}: {
  category: SearchCategory;
  hits: SearchHit[];
  collapsed: boolean;
  onToggle: () => void;
}) {
  const meta = CATEGORY_META[category];
  if (!meta) return null;
  const { label, Icon, color } = meta;

  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 mb-2 group"
      >
        <Icon className={`w-4 h-4 ${color} flex-shrink-0`} />
        <span className={`text-sm font-semibold ${color}`}>{label}</span>
        <span className="text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5 ml-1">
          {hits.length}
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 text-gray-400 ml-auto transition-transform ${collapsed ? "" : "rotate-90"}`}
        />
      </button>
      {!collapsed && (
        <div className="space-y-2 pl-6">
          {hits.map((hit) => (
            <HitCard key={hit.id} hit={hit} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function GlobalSearchPage() {
  const [rawQuery, setRawQuery] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<Set<SearchCategory>>(
    new Set(ALL_CATEGORIES)
  );
  const [academicYear, setAcademicYear] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);

  const query = useDebounce(rawQuery.trim(), 350);
  const enabled = query.length >= 2;

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ["global-search", query, [...selectedCategories].sort(), academicYear],
    queryFn: () =>
      globalSearch({
        q: query,
        categories: [...selectedCategories] as SearchCategory[],
        academic_year: academicYear || undefined,
        limit: 100,
      }),
    enabled,
    staleTime: 30_000,
  });

  const toggleCategory = useCallback((cat: SearchCategory) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }, []);

  const toggleSection = useCallback((cat: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }, []);

  const clearAll = () => {
    setRawQuery("");
    setAcademicYear("");
    setSelectedCategories(new Set(ALL_CATEGORIES));
    inputRef.current?.focus();
  };

  const categoriesWithHits = data
    ? (Object.entries(data.by_category) as [SearchCategory, SearchHit[]][]).filter(
        ([, hits]) => hits.length > 0
      )
    : [];

  return (
    <div className="h-full flex flex-col">
      {/* ── Header ── */}
      <div className="px-6 pt-6 pb-4 border-b border-gray-200 bg-white flex-shrink-0">
        <div className="flex items-center gap-3 mb-1">
          <Search className="w-5 h-5 text-[#003087]" />
          <h1 className="text-xl font-bold text-gray-900">Global Search</h1>
        </div>
        <p className="text-sm text-gray-500 ml-8">
          Search across faculty, students, research, projects and all data categories
        </p>
      </div>

      {/* ── Search bar + filters ── */}
      <div className="px-6 py-4 bg-white border-b border-gray-100 flex-shrink-0">
        {/* Search input */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={rawQuery}
            onChange={(e) => setRawQuery(e.target.value)}
            placeholder="Search by name, ID, title, keywords…"
            className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#003087]/30 focus:border-[#003087] transition"
            autoFocus
          />
          {rawQuery && (
            <button
              onClick={() => setRawQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Year filter */}
          <select
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#003087]/30"
          >
            <option value="">All Years</option>
            {YEARS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters((f) => !f)}
            className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border transition ${
              showFilters
                ? "border-[#003087] bg-[#003087]/5 text-[#003087]"
                : "border-gray-200 text-gray-600 hover:border-gray-300"
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Categories
            {selectedCategories.size < ALL_CATEGORIES.length && (
              <span className="bg-[#003087] text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                {selectedCategories.size}
              </span>
            )}
          </button>

          {/* Select / deselect all */}
          {showFilters && (
            <>
              <button
                onClick={() => setSelectedCategories(new Set(ALL_CATEGORIES))}
                className="text-xs text-[#003087] hover:underline"
              >
                All
              </button>
              <button
                onClick={() => setSelectedCategories(new Set())}
                className="text-xs text-gray-400 hover:underline"
              >
                None
              </button>
            </>
          )}

          {/* Clear */}
          {(rawQuery || academicYear || selectedCategories.size < ALL_CATEGORIES.length) && (
            <button
              onClick={clearAll}
              className="ml-auto text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
            >
              <X className="w-3 h-3" /> Clear
            </button>
          )}
        </div>

        {/* Category chips */}
        {showFilters && (
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100">
            {ALL_CATEGORIES.map((cat) => {
              const meta = CATEGORY_META[cat];
              const active = selectedCategories.has(cat);
              return (
                <button
                  key={cat}
                  onClick={() => toggleCategory(cat)}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition ${
                    active
                      ? `${meta.bg} ${meta.color} border-current`
                      : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <meta.Icon className="w-3 h-3" />
                  {meta.label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Results area ── */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {/* Loading */}
        {isFetching && (
          <div className="flex items-center gap-2 text-gray-500 text-sm py-8 justify-center">
            <Loader2 className="w-4 h-4 animate-spin" />
            Searching…
          </div>
        )}

        {/* Error */}
        {isError && !isFetching && (
          <div className="flex items-center gap-2 text-red-600 text-sm py-8 justify-center">
            <AlertCircle className="w-4 h-4" />
            {(error as Error)?.message ?? "Search failed. Please try again."}
          </div>
        )}

        {/* Empty state — not typed yet */}
        {!isFetching && !data && !isError && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Search className="w-12 h-12 text-gray-200 mb-3" />
            <p className="text-gray-400 text-sm">Type at least 2 characters to search</p>
            <p className="text-gray-300 text-xs mt-1">
              Covers faculty, students, research, patents, placements and more
            </p>
          </div>
        )}

        {/* No results */}
        {!isFetching && data && data.total === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Search className="w-12 h-12 text-gray-200 mb-3" />
            <p className="text-gray-500 text-sm font-medium">No results for "{data.query}"</p>
            <p className="text-gray-400 text-xs mt-1">Try a different term or adjust filters</p>
          </div>
        )}

        {/* Results */}
        {!isFetching && data && data.total > 0 && (
          <>
            {/* Summary bar */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-semibold text-gray-900">{data.returned}</span>
                {data.total > data.returned && (
                  <> of <span className="font-semibold text-gray-900">{data.total}</span></>
                )}{" "}
                results for{" "}
                <span className="font-semibold text-[#003087]">"{data.query}"</span>
              </p>

              {/* Per-category badges */}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(data.category_counts)
                  .filter(([, n]) => n > 0)
                  .map(([cat, n]) => {
                    const meta = CATEGORY_META[cat as SearchCategory];
                    if (!meta) return null;
                    return (
                      <span
                        key={cat}
                        className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${meta.bg} ${meta.color}`}
                      >
                        <meta.Icon className="w-3 h-3" />
                        {n}
                      </span>
                    );
                  })}
              </div>
            </div>

            {/* Category sections */}
            {categoriesWithHits.map(([cat, hits]) => (
              <CategorySection
                key={cat}
                category={cat}
                hits={hits}
                collapsed={collapsedSections.has(cat)}
                onToggle={() => toggleSection(cat)}
              />
            ))}

            {data.total > data.returned && (
              <p className="text-xs text-gray-400 text-center mt-4">
                Showing first {data.returned} of {data.total} results. Refine your search to narrow results.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
