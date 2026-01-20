const API_BASE = '/api';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.detail || `Error: ${response.status}` };
    }

    const data = await response.json();
    return { data };
  } catch (err) {
    return { error: 'Network error. Please try again.' };
  }
}

// Auth API
export interface User {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function register(email: string, password: string): Promise<ApiResponse<User>> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<ApiResponse<LoginResponse>> {
  // OAuth2 expects form data
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.detail || 'Login failed' };
    }

    const data = await response.json();
    return { data };
  } catch (err) {
    return { error: 'Network error. Please try again.' };
  }
}

export async function getMe(token?: string): Promise<ApiResponse<User>> {
  if (token) {
    // Use provided token directly
    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { error: errorData.detail || `Error: ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (err) {
      return { error: 'Network error. Please try again.' };
    }
  }
  return request<User>('/auth/me');
}

// Chat API
export interface ChatRequest {
  prompt: string;
  model?: string;
}

export interface ChatResponse {
  response: string;
  model: string;
  prompt_tokens?: number;
  completion_tokens?: number;
}

export async function sendChat(prompt: string, model?: string): Promise<ApiResponse<ChatResponse>> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ prompt, model }),
  });
}

export async function getModels(): Promise<ApiResponse<string[]>> {
  return request<string[]>('/chat/models');
}

export interface ChatHistoryItem {
  id: number;
  prompt: string;
  response: string;
  model: string;
  created_at: string;
}

export async function getChatHistory(limit: number = 50): Promise<ApiResponse<ChatHistoryItem[]>> {
  return request<ChatHistoryItem[]>(`/chat/history?limit=${limit}`);
}

// Admin API
export interface UserStats {
  id: number;
  email: string;
  role: string;
  created_at: string;
  total_requests: number;
  total_tokens: number;
}

export interface UsageByModel {
  model: string;
  request_count: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface UsageByUser {
  user_id: number;
  email: string;
  request_count: number;
  total_tokens: number;
}

export interface DailyUsage {
  date: string;
  request_count: number;
  total_tokens: number;
}

export interface AdminStats {
  total_users: number;
  total_requests: number;
  total_tokens: number;
  active_users_today: number;
  requests_today: number;
  tokens_today: number;
}

export interface AdminDashboard {
  stats: AdminStats;
  usage_by_model: UsageByModel[];
  usage_by_user: UsageByUser[];
  daily_usage: DailyUsage[];
}

export async function getAdminUsers(): Promise<ApiResponse<UserStats[]>> {
  return request<UserStats[]>('/admin/users');
}

export async function getAdminStats(days: number = 7): Promise<ApiResponse<AdminDashboard>> {
  return request<AdminDashboard>(`/admin/stats?days=${days}`);
}

export async function updateUserRole(userId: number, role: string): Promise<ApiResponse<{message: string}>> {
  return request<{message: string}>(`/admin/users/${userId}/role?role=${role}`, {
    method: 'PATCH',
  });
}

export async function deleteUser(userId: number): Promise<ApiResponse<{message: string}>> {
  return request<{message: string}>(`/admin/users/${userId}`, {
    method: 'DELETE',
  });
}
