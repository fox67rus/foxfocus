import type { AuditRun, CaptureResponse, LlmStatus, Note, Priority, Task, TaskFilter } from "./types";

export const USER_STORAGE_KEY = "foxfocus.user_id";

export function getUserId(): string {
  return localStorage.getItem(USER_STORAGE_KEY) || "u_1";
}

export function setUserId(userId: string): void {
  localStorage.setItem(USER_STORAGE_KEY, userId);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json() as Promise<T>;
}

export function capture(text: string, userId: string): Promise<CaptureResponse> {
  return request("/capture", {
    method: "POST",
    body: JSON.stringify({ text, user_id: userId }),
  });
}

export function listTasks(userId: string, status?: TaskFilter): Promise<Task[]> {
  const query = new URLSearchParams({ user_id: userId });
  if (status) {
    query.set("status", status);
  }
  return request(`/tasks?${query}`);
}

export function markDone(taskId: number, userId: string): Promise<{ status: string }> {
  return request(`/tasks/${taskId}/done`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function reviewTask(
  taskId: number,
  userId: string,
  title: string,
  priority: Priority,
  dueDate: string | null,
): Promise<Task> {
  return request(`/tasks/${taskId}/review`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, title, priority, due_date: dueDate }),
  });
}

export function listNotes(userId: string): Promise<Note[]> {
  return request(`/notes?${new URLSearchParams({ user_id: userId })}`);
}

export function reviewNote(noteId: number, userId: string, title: string): Promise<Note> {
  return request(`/notes/${noteId}/review`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export function listAudit(userId: string): Promise<AuditRun[]> {
  return request(`/audit?${new URLSearchParams({ user_id: userId })}`);
}

export function deleteTask(taskId: number, userId: string): Promise<{ status: string }> {
  return request(`/tasks/${taskId}/delete`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function deleteNote(noteId: number, userId: string): Promise<{ status: string }> {
  return request(`/notes/${noteId}/delete`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function pingLlm(userId: string): Promise<LlmStatus> {
  return request(`/llm/status?${new URLSearchParams({ user_id: userId })}`);
}
