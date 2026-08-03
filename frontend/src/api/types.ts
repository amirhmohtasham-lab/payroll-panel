// Shared TypeScript types for API responses and upload records.

export type UserRole = 'operator' | 'accountant';

export interface MeResponse {
  username: string;
  role: UserRole;
  name: string;
}

export interface LoginResponse {
  ok: boolean;
  redirect: string;
  role: UserRole;
  name: string;
}

export interface UserOut {
  id: string;
  username: string;
  name: string;
  role: UserRole;
}

export interface Issue {
  severity: 'error' | 'warn';
  code: string;
  sheet: string | null;
  message: string;
}

export interface IssueGroup {
  code: string;
  count: number;
  items: Issue[];
}

export interface SheetSummary {
  name: string;
  foreman: string | null;
  list_no: string | null;
  workplace: string | null;
  period: string | null;
  worker_rows: number;
  worker_gross: string | number | null;
  desc_gross: string | number | null;
  error_count: number;
  warn_count: number;
}

export interface AuditSummary {
  sheet_count: number;
  worker_rows: number;
  sheets: SheetSummary[];
}

export interface UploadRecord {
  id: string;
  upload_type: 'payroll' | 'fertilizer';
  month_key: string;
  month_label: string;
  original_filename: string;
  sha256: string;
  uploaded_at: string;
  error_count: number;
  warn_count: number;
  highlight_url: string | null;
  drive_file_id: string | null;
  drive_error: string | null;
  crop: string | null;
  season: string | null;
  row_count: number | null;
  fertilizer_count: number | null;
  audit_summary: AuditSummary | null;
  issues_grouped: IssueGroup[];
}

export interface UploadResultResponse {
  ok: boolean;
  error_count: number;
  warn_count: number;
  record: UploadRecord;
}

export interface DuplicateInfo {
  duplicate: true;
  message: string;
  existing: {
    month_key?: string;
    month_label?: string;
    filename?: string;
    uploaded_at?: string;
  };
}

export interface MonthListItem {
  month_key: string;
  month_label: string;
  filename: string;
  uploaded_at: string;
  error_count: number;
  warn_count: number;
  status_label: 'ok' | 'warn' | 'error';
  status_text: string;
  worker_rows?: number | null;
  row_count?: number | null;
  fertilizer_count?: number | null;
}

export interface MonthListResponse {
  items: MonthListItem[];
  summary: {
    month_count: number;
    total_errors: number;
    total_warns: number;
    total_workers?: number;
    total_rows?: number;
  };
}

export interface ArchiveItem {
  month_key: string;
  type: 'workforce' | 'fertilizer';
  module_label: string;
  label: string;
  filename: string;
  uploaded_at: string;
  error_count: number;
  warn_count: number;
}

export interface ArchiveResponse {
  items: ArchiveItem[];
  summary: {
    workforce_count: number;
    fertilizer_count: number;
    total: number;
  };
}

export interface ReportsDataResponse {
  foreman_totals: { labels: string[]; values: number[] };
  well_totals: { labels: string[]; values: number[] };
  monthly: { labels: string[]; worker: number[]; desc: number[] };
  status: { clean: number; error: number; warn: number };
  foreman_monthly: {
    foremen: string[];
    months: string[];
    matrix: Record<string, Record<string, number>>;
  };
  month_count: number;
  sheet_count: number;
}

export interface ChatResponse {
  reply: string;
  chart: string;
}

export interface ChatMessageOut {
  id: string;
  role: 'user' | 'assistant';
  message: string | null;
  reply: string | null;
  chart: string | null;
  created_at: string;
}
