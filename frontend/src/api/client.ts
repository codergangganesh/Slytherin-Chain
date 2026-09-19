import type {
  AnchorBatch,
  Asset,
  AuditLedgerEntry,
  AuthTokens,
  DashboardKpis,
  IncidentDetail,
  IncidentPriority,
  IncidentStatus,
  IncidentSummary,
  IntegrityVerificationReport,
  MerkleProof,
  ResponseAction,
  ScenarioInfo,
  TimelineEntry,
  UserProfile,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

class ApiClient {
  private loginPromise: Promise<string> | null = null;

  private async ensureToken(): Promise<string> {
    const existing = localStorage.getItem("sentinel_token");
    if (existing) return existing;

    if (!this.loginPromise) {
      this.loginPromise = (async () => {
        try {
          const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: "admin",
              password: "admin_demo_password",
            }),
          });
          if (res.ok) {
            const data: AuthTokens = await res.json();
            localStorage.setItem("sentinel_token", data.access_token);
            return data.access_token;
          }
        } catch (e) {
          console.error("Auto login error:", e);
        } finally {
          this.loginPromise = null;
        }
        return "";
      })();
    }
    return this.loginPromise;
  }

  private async request<T>(path: string, options: RequestInit = {}, retryCount = 0): Promise<T> {
    const token = await this.ensureToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    };

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      if (res.status === 401 && retryCount === 0) {
        localStorage.removeItem("sentinel_token");
        // Retry once after clearing stale token
        return this.request<T>(path, options, 1);
      }

      let errMessage = `HTTP error ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail?.error?.message) {
          errMessage = errJson.detail.error.message;
        } else if (errJson.detail) {
          errMessage = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Response body was not valid JSON, use status text fallback
      }
      throw new Error(errMessage);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return res.json();
  }

  // Auth
  async login(username: string, password: string): Promise<AuthTokens> {
    const res = await this.request<AuthTokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("sentinel_token", res.access_token);
    return res;
  }

  async getMyProfile(): Promise<UserProfile> {
    return this.request<UserProfile>("/auth/me");
  }

  logout(): void {
    localStorage.removeItem("sentinel_token");
  }

  // Dashboard
  async getDashboardSummary(): Promise<DashboardKpis> {
    return this.request<DashboardKpis>("/dashboard/summary");
  }

  async getDashboardTrends(): Promise<Array<{ date: string; incident_count: number; actions_count: number }>> {
    return this.request("/dashboard/trends");
  }

  // Incidents
  async getIncidents(params?: { status?: IncidentStatus; priority?: IncidentPriority }): Promise<{ items: IncidentSummary[]; total: number }> {
    const q = new URLSearchParams();
    if (params?.status) q.append("status", params.status);
    if (params?.priority) q.append("priority", params.priority);
    const qs = q.toString();
    return this.request(qs ? `/incidents?${qs}` : "/incidents");
  }

  async getIncident(id: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${id}`);
  }

  async getIncidentTimeline(id: string): Promise<TimelineEntry[]> {
    return this.request<TimelineEntry[]>(`/incidents/${id}/timeline`);
  }

  async transitionIncident(id: string, target_status: IncidentStatus, notes?: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ target_status, notes }),
    });
  }

  async addIncidentNote(id: string, note: string): Promise<TimelineEntry> {
    return this.request<TimelineEntry>(`/incidents/${id}/notes`, {
      method: "POST",
      body: JSON.stringify({ note }),
    });
  }

  // Assets
  async getAssets(): Promise<{ items: Asset[]; total: number }> {
    return this.request<{ items: Asset[]; total: number }>("/assets");
  }

  async createAsset(asset: Partial<Asset>): Promise<Asset> {
    return this.request<Asset>("/assets", {
      method: "POST",
      body: JSON.stringify(asset),
    });
  }

  async deleteAsset(id: string): Promise<void> {
    return this.request<void>(`/assets/${id}`, { method: "DELETE" });
  }

  // Response Actions
  async getResponseActions(incidentId?: string): Promise<{ items: ResponseAction[]; total: number }> {
    const q = incidentId ? `?incident_id=${incidentId}` : "";
    return this.request<{ items: ResponseAction[]; total: number }>(`/response-actions${q}`);
  }

  async approveAction(id: string): Promise<ResponseAction> {
    return this.request<ResponseAction>(`/response-actions/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  async denyAction(id: string, reason: string): Promise<ResponseAction> {
    return this.request<ResponseAction>(`/response-actions/${id}/deny`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async rollbackAction(id: string, reason: string): Promise<ResponseAction> {
    return this.request<ResponseAction>(`/response-actions/${id}/rollback`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  // Integrity & Blockchain
  async getIntegrityStatus(): Promise<IntegrityVerificationReport> {
    return this.request<IntegrityVerificationReport>("/integrity/status");
  }

  async triggerVerify(): Promise<IntegrityVerificationReport> {
    return this.request<IntegrityVerificationReport>("/integrity/verify", { method: "POST" });
  }

  async getLedgerEntries(incidentId?: string): Promise<{ items: AuditLedgerEntry[]; total: number }> {
    const q = incidentId ? `?incident_id=${incidentId}` : "";
    return this.request<{ items: AuditLedgerEntry[]; total: number }>(`/integrity/entries${q}`);
  }

  async getMerkleProof(sequence: number): Promise<MerkleProof> {
    return this.request<MerkleProof>(`/integrity/entries/${sequence}/proof`);
  }

  async getAnchorBatches(): Promise<{ items: AnchorBatch[]; total: number }> {
    return this.request<{ items: AnchorBatch[]; total: number }>("/integrity/batches");
  }

  async anchorNow(): Promise<AnchorBatch> {
    return this.request<AnchorBatch>("/integrity/anchor-now", { method: "POST" });
  }

  // Reports
  async generateReport(incidentId: string, format: "json" | "md" | "pdf"): Promise<{ download_url: string }> {
    return this.request<{ download_url: string }>(`/reports/incidents/${incidentId}?format=${format}`, {
      method: "POST",
    });
  }

  // Settings
  async getAutonomyMode(): Promise<{ autonomy_mode: string }> {
    return this.request<{ autonomy_mode: string }>("/settings/autonomy-mode");
  }

  async updateAutonomyMode(mode: string): Promise<{ autonomy_mode: string }> {
    return this.request<{ autonomy_mode: string }>("/settings/autonomy-mode", {
      method: "PUT",
      body: JSON.stringify({ autonomy_mode: mode }),
    });
  }

  async getPlaybooks(): Promise<any[]> {
    return this.request<any[]>("/settings/playbooks");
  }

  // Simulator
  async getScenarios(): Promise<ScenarioInfo[]> {
    return this.request<ScenarioInfo[]>("/simulator/scenarios");
  }

  async runScenario(name: string, speed: number = 1.0): Promise<{ status: string; events_injected: number; alerts_triggered: number }> {
    return this.request(`/simulator/scenarios/${name}/run?speed=${speed}`, {
      method: "POST",
    });
  }
}

export const api = new ApiClient();
