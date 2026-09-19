export type UserRole = "viewer" | "analyst" | "admin";

export type IncidentStatus =
  | "NEW"
  | "TRIAGED"
  | "AWAITING_APPROVAL"
  | "CONTAINED"
  | "INVESTIGATING"
  | "RESOLVED"
  | "CLOSED"
  | "FALSE_POSITIVE";

export type IncidentPriority = "P1" | "P2" | "P3" | "P4";

export type ActionType = "block_ip" | "isolate_host" | "disable_user" | "restrict_access" | "notify";

export type ActionStatus =
  | "PROPOSED"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "DENIED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED"
  | "ROLLED_BACK"
  | "EXPIRED";

export type AutonomyMode = "off" | "recommend_only" | "approval_required" | "auto";

export type VerificationStatus = "VERIFIED" | "TAMPERED" | "PENDING_ANCHOR" | "CHAIN_UNAVAILABLE";

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Asset {
  id: string;
  hostname: string;
  ip_address: string;
  criticality: number;
  environment: string;
  is_protected: boolean;
  is_internet_facing: boolean;
  owner: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface RiskFactorContribution {
  factor_name: string;
  raw_value: number;
  weight: number;
  contribution: number;
  explanation: string;
}

export interface RiskBreakdown {
  score: number;
  priority: IncidentPriority;
  correlation_bonus: number;
  summary: string;
  factors: RiskFactorContribution[];
}

export interface IncidentSummary {
  id: string;
  reference_id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  priority: IncidentPriority;
  risk_score: number;
  primary_src_ip?: string;
  primary_host?: string;
  primary_username?: string;
  created_at: string;
  updated_at: string;
  assigned_to?: string;
}

export interface IncidentDetail extends IncidentSummary {
  risk_breakdown: RiskBreakdown;
  mitre_tactics: string[];
  mitre_techniques: string[];
  affected_asset_ids: string[];
  closed_at?: string;
  close_notes?: string;
}

export interface TimelineEntry {
  id: string;
  incident_id: string;
  timestamp: string;
  entry_type: string;
  title: string;
  description: string;
  actor: string;
  mitre_tactic?: string;
  mitre_technique?: string;
  metadata?: Record<string, any>;
}

export interface GuardrailDecision {
  guardrail_name: string;
  passed: boolean;
  reason: string;
  evaluated_at: string;
}

export interface ResponseAction {
  id: string;
  incident_id: string;
  action_type: ActionType;
  target: string;
  status: ActionStatus;
  idempotency_key: string;
  parameters: Record<string, any>;
  guardrail_decisions: GuardrailDecision[];
  ttl_seconds?: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  executed_at?: string;
  rolled_back_at?: string;
  approved_by?: string;
  denial_reason?: string;
  rollback_reason?: string;
  execution_result: Record<string, any>;
}

export interface AuditLedgerEntry {
  sequence_number: number;
  entry_type: string;
  incident_id?: string;
  payload: Record<string, any>;
  created_at: string;
  previous_hash: string;
  entry_hash: string;
  anchor_batch_id?: string;
}

export interface AnchorBatch {
  id: string;
  from_sequence: number;
  to_sequence: number;
  merkle_root: string;
  entry_count: number;
  status: string;
  tx_hash?: string;
  block_number?: number;
  contract_address?: string;
  error_message?: string;
  created_at: string;
  anchored_at?: string;
}

export interface IntegrityVerificationReport {
  status: VerificationStatus;
  total_entries_checked: number;
  total_batches_checked: number;
  tampered_sequence_number?: number;
  tampered_batch_id?: string;
  explanation: string;
  chain_head_hash?: string;
  verified_at: string;
}

export interface MerkleProofStep {
  position: "left" | "right";
  hash_value: string;
}

export interface MerkleProof {
  leaf_hash: string;
  leaf_index: number;
  total_leaves: number;
  proof_steps: MerkleProofStep[];
  root: string;
}

export interface ScenarioInfo {
  name: string;
  title: string;
  description: string;
  target_asset: string;
  expected_priority: string;
  expected_response: string;
}

export interface DashboardKpis {
  open_incidents_count: number;
  p1_critical_count: number;
  p2_high_count: number;
  actions_executed_today: number;
  mean_time_to_contain_seconds: number;
  autonomy_mode: string;
  integrity_status: string;
  priority_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
}
