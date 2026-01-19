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

export async function getMe(): Promise<ApiResponse<User>> {
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
