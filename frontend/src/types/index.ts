export interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  type: 'income' | 'expense' | 'transfer';
  category_id: number | null;
  transaction_date: string;
  description: string | null;
  merchant: string | null;
  payment_method: string | null;
  source: 'manual' | 'import';
  import_id: number | null;
  tags: Record<string, any> | null;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  icon: string | null;
  parent_id: number | null;
  is_system: boolean;
  sort_order: number;
  children: Category[];
}

export interface DetectionResult {
  id: number;
  user_id: number;
  transaction_id: number | null;
  detector_type: string;
  severity: 'high' | 'medium' | 'low';
  anomaly_score: number;
  reason: Array<{
    detector: string; method?: string; rule_id?: string;
    severity: string; score?: number; detail: string;
  }>;
  suggestion: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Budget {
  id: number;
  category_id: number | null;
  amount_limit: number;
  period: string;
  start_date: string;
  end_date: string;
  alert_threshold: number;
  spent_amount: number;
  progress_pct: number;
}

export interface ImportRecord {
  id: number;
  filename: string;
  source_type: string;
  status: string;
  row_count: number;
  new_count: number;
  skipped_count: number;
  created_at: string;
}

export interface ImportResult {
  import_id: number;
  status: string;
  row_count: number;
  new_count: number;
  skipped_count: number;
}
