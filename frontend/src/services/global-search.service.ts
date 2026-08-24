import apiClient from "@/services/api";

export interface SearchHit {
  category: string;
  id: string;
  label: string;
  sublabel: string | null;
  academic_year: string | null;
  department_id: string | null;
  [key: string]: unknown;
}

export interface GlobalSearchResponse {
  query: string;
  total: number;
  returned: number;
  category_counts: Record<string, number>;
  results: SearchHit[];
  by_category: Record<string, SearchHit[]>;
}

export const ALL_CATEGORIES = [
  "faculty",
  "students",
  "research",
  "patents",
  "placements",
  "mous",
  "events",
  "awards",
  "sdg",
  "funded_projects",
  "higher_studies",
  "consultancy",
] as const;

export type SearchCategory = (typeof ALL_CATEGORIES)[number];

export interface GlobalSearchParams {
  q: string;
  categories?: SearchCategory[];
  academic_year?: string;
  limit?: number;
}

export async function globalSearch(
  params: GlobalSearchParams
): Promise<GlobalSearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.q);
  if (params.academic_year) searchParams.set("academic_year", params.academic_year);
  if (params.limit) searchParams.set("limit", String(params.limit));

  const cats = params.categories ?? ALL_CATEGORIES;
  cats.forEach((c) => searchParams.append("categories", c));

  const { data } = await apiClient.get<GlobalSearchResponse>(
    `/global-search/?${searchParams.toString()}`
  );
  return data;
}
