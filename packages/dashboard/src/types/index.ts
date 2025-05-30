// Common type definitions for the EUDI-Connect dashboard

// API Keys
export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  suffix: string;
  created_at: string;
  last_used: string;
  status: 'active' | 'revoked' | 'expired';
  environment: 'production' | 'development' | 'test';
  permissions: string[];
  rate_limit: number;
  total_requests: number;
}

// Credential Types
export interface CredentialType {
  id: string;
  name: string;
  schema: string;
  description: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  total_issued: number;
  total_verified: number;
  total_revoked?: number;
  status: 'active' | 'inactive' | 'deprecated';
  template?: {
    fields: CredentialField[];
    context: string[];
    type: string[];
    revocation_registry?: string;
    cryptographic_suite?: string;
  };
  historical_stats?: HistoricalStat[];
  verification_results?: VerificationResult[];
}

export interface CredentialField {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

export interface HistoricalStat {
  month: string;
  issued: number;
  verified: number;
  revoked: number;
}

export interface VerificationResult {
  name: string;
  value: number;
}

// Credential Logs
export interface CredentialLog {
  id: string;
  operation: 'issue' | 'verify' | 'revoke';
  credential_type_id: string;
  credential_type_name: string;
  wallet_id: string;
  timestamp: string;
  status: 'success' | 'failed' | 'pending';
  error?: string;
  user_id: string;
  metadata: Record<string, any>;
}

// Wallet Providers
export interface WalletProvider {
  id: string;
  name: string;
  description: string;
  version: string;
  provider: string;
  status: 'verified' | 'testing' | 'deprecated';
  compatibility: 'full' | 'partial' | 'limited' | 'incompatible';
  last_checked: string;
  supported_features: string[];
  active_sessions: number;
  total_sessions: number;
  success_rate: number;
}

// Wallet Sessions
export interface WalletSession {
  id: string;
  wallet_provider_id: string;
  wallet_provider_name: string;
  user_id: string;
  status: 'active' | 'completed' | 'error' | 'expired';
  created_at: string;
  last_activity: string;
  operations: WalletOperation[];
  error?: {
    code: string;
    message: string;
  };
  device_info: {
    os?: string;
    model?: string;
    ip_address?: string;
    location?: string;
    reason?: string;
  };
}

export interface WalletOperation {
  type: string;
  timestamp: string;
  status: string;
}

// Compliance Scanning
export interface ComplianceScan {
  id: string;
  name: string;
  wallet_name: string;
  wallet_version: string;
  wallet_provider: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total_requirements: number;
  passed_requirements: number;
  failed_requirements: number;
  warning_requirements: number;
  manual_check_requirements: number;
  compliance_score: number;
  description?: string;
  config?: {
    category_filter?: string | null;
    level_filter?: string | null;
    timestamp: string;
  };
}

export interface ComplianceResult {
  id: string;
  requirement: {
    id: string;
    code: string;
    name: string;
    category: string;
    level: string;
    description: string;
    legal_reference?: string;
  };
  status: 'pass' | 'warning' | 'fail' | 'manual_check_required' | 'not_applicable';
  message: string;
  details: Record<string, any>;
  remediation_steps?: string;
  execution_time_ms: number;
  executed_at: string;
}

// Billing & Subscription
export interface BillingPlan {
  id: string;
  name: string;
  price: number;
  billing_cycle: 'monthly' | 'yearly';
  description: string;
  features: string[];
  limits: {
    credential_operations: number | string;
    api_keys: number | string;
    wallet_sessions: number | string;
    compliance_scans: number | string;
  };
  popular?: boolean;
}

export interface Subscription {
  id: string;
  name: string;
  price: number;
  billing_cycle: 'monthly' | 'yearly';
  next_billing_date: string;
  status: 'active' | 'canceled' | 'past_due';
  features: string[];
  limits: {
    credential_operations: number | string;
    api_keys: number | string;
    wallet_sessions: number | string;
    compliance_scans: number | string;
  };
  current_usage: {
    credential_operations: number;
    api_keys: number;
    wallet_sessions: number;
    compliance_scans: number;
  };
}

export interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  description: string;
}

// Team Management
export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'developer' | 'viewer';
  status: 'active' | 'invited' | 'disabled';
  avatar: string;
  last_active?: string;
  joined_at: string;
  permissions: string[];
}

export interface Role {
  id: string;
  name: string;
  description: string;
}

// Utility Types
export interface ChartDataPoint {
  date: string;
  [key: string]: string | number;
}

// UI Components Props Types
export interface DateRangePickerProps {
  from: Date;
  to: Date;
  onSelect: (range: { from: Date; to: Date } | undefined) => void;
  className?: string;
}
