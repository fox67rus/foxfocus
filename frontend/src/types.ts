export type ItemType = "task" | "note";
export type Priority = "low" | "medium" | "high";
export type TaskStatus = "todo" | "in_progress" | "done";
export type TaskFilter = "open" | "done";

export type CaptureResponse = {
  status: string;
  item_id: number;
  item_type: ItemType;
  needs_review: boolean;
};

export type Task = {
  id: number;
  created_at: string;
  title: string;
  due_date: string | null;
  priority: Priority;
  status: TaskStatus;
  tags: string[];
  needs_review: boolean;
  review_reason: string | null;
  source_text: string | null;
};

export type Note = {
  id: number;
  created_at: string;
  text: string;
  title: string | null;
  tags: string[];
  needs_review: boolean;
  review_reason: string | null;
  source_text: string | null;
};

export type LlmStatus = {
  status: "ok" | "error";
  mode: string;
  provider: string | null;
  base_url: string | null;
  model: string | null;
  detail: string | null;
  duration_ms: number;
};

export type AuditRun = {
  id: number;
  created_at: string;
  action: string;
  input: unknown;
  output: unknown;
  status: string;
  error: string | null;
  duration_ms: number;
};

export type InboxItem = {
  kind: ItemType;
  id: number;
  created_at: string;
  title: string;
  needs_review: boolean;
  review_reason: string | null;
  source_text: string | null;
};

export function taskToInbox(task: Task): InboxItem {
  return {
    kind: "task",
    id: task.id,
    created_at: task.created_at,
    title: task.title,
    needs_review: task.needs_review,
    review_reason: task.review_reason,
    source_text: task.source_text,
  };
}

export function noteToInbox(note: Note): InboxItem {
  return {
    kind: "note",
    id: note.id,
    created_at: note.created_at,
    title: note.title || note.text,
    needs_review: note.needs_review,
    review_reason: note.review_reason,
    source_text: note.source_text,
  };
}

export function mergeInbox(tasks: Task[], notes: Note[], limit = 50): InboxItem[] {
  return [...tasks.map(taskToInbox), ...notes.map(noteToInbox)]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, limit);
}
