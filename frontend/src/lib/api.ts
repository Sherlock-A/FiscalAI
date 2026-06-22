const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_VERSION = "/api/v1";

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE}${API_VERSION}`;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private authHeaders(): HeadersInit {
    const token = this.getToken();
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  private async refreshDemoToken(): Promise<boolean> {
    try {
      const r = await fetch(`${API_BASE}/api/v1/auth/demo-token`);
      if (!r.ok) return false;
      const data = await r.json();
      if (data?.access_token) {
        localStorage.setItem("access_token", data.access_token);
        return true;
      }
    } catch {}
    return false;
  }

  async get<T>(path: string, retried = false): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: this.authHeaders(),
    });
    if (res.status === 401 && !retried) {
      const refreshed = await this.refreshDemoToken();
      if (refreshed) return this.get(path, true);
      throw new Error("Session expirée");
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail ?? `HTTP ${res.status}`);
    }
    return res.json();
  }

  async post<T>(path: string, body: unknown, retried = false): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.authHeaders(),
      body: JSON.stringify(body),
    });
    if (res.status === 401 && !retried) {
      const refreshed = await this.refreshDemoToken();
      if (refreshed) return this.post(path, body, true);
      throw new Error("Session expirée");
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail ?? `HTTP ${res.status}`);
    }
    return res.json();
  }

  async patch<T>(path: string, body: unknown, retried = false): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "PATCH",
      headers: this.authHeaders(),
      body: JSON.stringify(body),
    });
    if (res.status === 401 && !retried) {
      const refreshed = await this.refreshDemoToken();
      if (refreshed) return this.patch(path, body, true);
      throw new Error("Session expirée");
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail ?? `HTTP ${res.status}`);
    }
    return res.json();
  }

  async postFile(path: string, body: unknown, retried = false): Promise<Blob> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.authHeaders(),
      body: JSON.stringify(body),
    });
    if (res.status === 401 && !retried) {
      const refreshed = await this.refreshDemoToken();
      if (refreshed) return this.postFile(path, body, true);
      throw new Error("Session expirée");
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail ?? `HTTP ${res.status}`);
    }
    return res.blob();
  }
}

export const apiClient = new ApiClient();
