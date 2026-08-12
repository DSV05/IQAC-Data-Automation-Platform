// ── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole =
  | "super_admin"
  | "iqac_admin"
  | "department_coordinator"
  | "data_entry_operator"
  | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

// ── API Responses ─────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
}

// ── Shared ────────────────────────────────────────────────────────────────────

export interface SelectOption {
  label: string;
  value: string;
}

export type AcademicYear = string; // e.g. "2023-24"

// ── AI Natural Language Search (Module 6) ───────────────────────────────────

export type AIQueryStatus = "success" | "blocked" | "error";

export interface NLQueryResponse {
  id: string;
  question: string;
  generated_sql: string | null;
  status: AIQueryStatus;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_ms: number | null;
  truncated: boolean;
  explanation: string | null;
  error_message: string | null;
  ai_provider: string | null;
}

export interface AIQueryHistoryItem {
  id: string;
  question: string;
  generated_sql: string | null;
  status: AIQueryStatus;
  row_count: number | null;
  execution_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface AISchemaInfo {
  ai_configured: boolean;
  ai_provider: string;
  tables: string[];
  example_questions: string[];
}

// ── RAG Chatbot (Module 7) ──────────────────────────────────────────────────

export type RAGDocumentType = "naac_ssr" | "annual_report" | "nirf_report" | "policy" | "other";
export type RAGDocumentStatus = "processing" | "ready" | "failed";

export interface RAGDocumentItem {
  id: string;
  title: string;
  original_filename: string;
  doc_type: RAGDocumentType;
  academic_year: string | null;
  status: RAGDocumentStatus;
  page_count: number | null;
  chunk_count: number | null;
  file_size_bytes: number | null;
  error_message: string | null;
  uploaded_by_name: string | null;
  created_at: string;
}

export interface RAGSource {
  document_id: string;
  title: string;
  filename: string;
  page: number;
  snippet: string;
  score: number;
}

export interface RAGChatResponse {
  id: string;
  question: string;
  answer: string | null;
  sources: RAGSource[];
  status: "success" | "error";
  execution_ms: number | null;
  error_message: string | null;
  ai_provider: string | null;
}

export interface RAGChatHistoryItem {
  id: string;
  question: string;
  answer: string | null;
  status: "success" | "error";
  execution_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface RAGInfo {
  ai_configured: boolean;
  ai_provider: string;
  document_count: number;
  ready_document_count: number;
}

// ── Report Generator (Module 8) ─────────────────────────────────────────────

export type ReportType = "nirf" | "naac_ssr" | "aishe";
export type ReportFormat = "xlsx" | "pdf";

export interface ReportTypeInfo {
  value: ReportType;
  label: string;
  description: string;
}

export interface ReportHistoryItem {
  id: string;
  report_type: ReportType;
  report_format: ReportFormat;
  academic_year: string | null;
  file_size_bytes: number | null;
  created_at: string;
}

// ── Excel Auto-Fill (Module 9) ──────────────────────────────────────────────

export interface ExcelTemplateItem {
  id: string;
  title: string;
  original_filename: string;
  sheet_count: number | null;
  token_count: number | null;
  file_size_bytes: number | null;
  uploaded_by_name: string | null;
  created_at: string;
}

export interface TokenInfo {
  token: string;
  sample_value: unknown;
  group: string;
}

export interface FillHistoryItem {
  id: string;
  template_id: string | null;
  academic_year: string | null;
  tokens_filled: number;
  tokens_missing: string[] | null;
  error_message: string | null;
  file_size_bytes: number | null;
  created_at: string;
}

// ── Workflow & Approvals (Module 10) ────────────────────────────────────────

export type WorkflowStatus = "draft" | "submitted" | "approved" | "rejected" | "locked";

export interface SubmissionItem {
  id: string;
  department_id: string;
  department_name: string;
  academic_year: string;
  status: WorkflowStatus;
  version: number;
  submitted_by_name: string | null;
  submitted_at: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_comments: string | null;
  locked_by_name: string | null;
  locked_at: string | null;
  created_at: string;
}

export interface WorkflowHistoryItem {
  id: string;
  from_status: WorkflowStatus | null;
  to_status: WorkflowStatus;
  version: number;
  actor_name: string | null;
  comments: string | null;
  created_at: string;
}

// ── Notifications (Module 11) ───────────────────────────────────────────────

export type NotificationType =
  | "missing_data"
  | "deadline_reminder"
  | "workflow_submitted"
  | "workflow_approved"
  | "workflow_rejected"
  | "workflow_locked"
  | "general";

export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface DeadlineItem {
  id: string;
  title: string;
  description: string | null;
  academic_year: string | null;
  due_date: string;
  department_id: string | null;
  department_name: string | null;
  reminder_days_before: number;
  last_reminded_on: string | null;
  created_at: string;
}
