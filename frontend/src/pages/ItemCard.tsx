import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getUserId, listAudit, listNotes, listTasks, reviewNote, reviewTask } from "../api";
import { ReviewBadge } from "../components/ReviewBadge";
import type { AuditRun, ItemType, Note, Priority, Task } from "../types";

export function ItemCard() {
  const { kind, id } = useParams();
  const userId = getUserId();
  const itemId = Number(id);
  const [task, setTask] = useState<Task | null>(null);
  const [note, setNote] = useState<Note | null>(null);
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (kind === "task") {
        const tasks = await listTasks(userId);
        const found = tasks.find((row) => row.id === itemId) ?? null;
        setTask(found);
        if (found) {
          setTitle(found.title);
          setPriority(found.priority);
          setDueDate(found.due_date ?? "");
        }
      } else {
        const notes = await listNotes(userId);
        const found = notes.find((row) => row.id === itemId) ?? null;
        setNote(found);
        if (found) {
          setTitle(found.title || found.text);
        }
      }
      const audit = await listAudit(userId);
      setRuns(audit);
    }
    setLoading(true);
    load()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [kind, itemId, userId]);

  const item = kind === "task" ? task : note;
  const sourceText = item?.source_text ?? (note ? note.text : null);
  const related = runs.filter((run) => mentions(run, sourceText, itemId, kind as ItemType));

  async function confirmReview(event: React.FormEvent) {
    event.preventDefault();
    setSaved(false);
    try {
      if (kind === "task") {
        const updated = await reviewTask(itemId, userId, title, priority, dueDate || null);
        setDueDate(updated.due_date ?? "");
        setTask(updated);
      } else {
        const updated = await reviewNote(itemId, userId, title);
        setNote(updated);
      }
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "не удалось сохранить");
    }
  }

  if (!kind || Number.isNaN(itemId)) {
    return <p className="text-sm text-zinc-500">Некорректный адрес.</p>;
  }
  if (loading) {
    return <p className="text-sm text-zinc-500">Загружаю…</p>;
  }
  if (error) {
    return <p className="text-sm text-red-400">{error}</p>;
  }
  if (!item) {
    return <p className="text-sm text-zinc-500">Запись не найдена.</p>;
  }

  return (
    <article className="space-y-6">
      <p className="text-sm text-zinc-500">
        <Link to="/" className="hover:text-zinc-300">
          ← входящие
        </Link>
      </p>
      <header className="space-y-2">
        <h1 className="text-xl font-semibold">{kind === "task" ? task?.title : note?.title || note?.text}</h1>
        {item.needs_review ? <ReviewBadge reason={item.review_reason} /> : null}
        {kind === "task" && task ? (
          <p className="text-sm text-zinc-400">
            {task.status} · {task.priority} · срок {task.due_date ?? "не указан"}
          </p>
        ) : null}
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <div>
          <h2 className="mb-2 text-xs uppercase text-zinc-500">Сырой ввод</h2>
          <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900 p-3 text-sm text-zinc-300">
            {sourceText || "—"}
          </pre>
        </div>
        <div>
          <h2 className="mb-2 text-xs uppercase text-zinc-500">Вывод модели</h2>
          <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900 p-3 text-sm text-zinc-300">
            {pretty(related.find((run) => run.action === "structure")?.output) || "нет записи structure"}
          </pre>
        </div>
      </section>

      <form onSubmit={confirmReview} className="space-y-3 rounded border border-zinc-800 p-4">
        <h2 className="text-sm font-medium">Ручная проверка</h2>
        <label className="block text-sm text-zinc-400">
          заголовок
          <input
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
        </label>
        {kind === "task" ? (
          <>
            <label className="block text-sm text-zinc-400">
              срок
              <input
                type="date"
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
            </label>
            <label className="block text-sm text-zinc-400">
              приоритет
              <select
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100"
                value={priority}
                onChange={(event) => setPriority(event.target.value as Priority)}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>
          </>
        ) : null}
        <button type="submit" className="rounded bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-950">
          Подтвердить проверку
        </button>
        {saved ? <p className="text-sm text-emerald-400">Метка снята.</p> : null}
      </form>
    </article>
  );
}

function mentions(run: AuditRun, sourceText: string | null, itemId: number, kind: ItemType): boolean {
  const dump = JSON.stringify(run);
  if (sourceText && dump.includes(sourceText)) {
    return true;
  }
  return dump.includes(`"item_id": ${itemId}`) && dump.includes(kind);
}

function pretty(value: unknown): string {
  return value == null ? "" : JSON.stringify(value, null, 2);
}
