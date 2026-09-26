import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getUserId, listTasks, markDone } from "../api";
import { ReviewBadge } from "../components/ReviewBadge";
import { downloadText, toCsv, toJson } from "../export";
import type { Task, TaskFilter } from "../types";

export function Tasks() {
  const userId = getUserId();
  const [status, setStatus] = useState<TaskFilter | "all">("open");
  const [onlyReview, setOnlyReview] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const rows = await listTasks(userId, status === "all" ? undefined : status);
    setTasks(rows);
  }

  useEffect(() => {
    reload().catch((err: Error) => setError(err.message));
  }, [userId, status]);

  const visible = onlyReview ? tasks.filter((task) => task.needs_review) : tasks;

  async function complete(taskId: number) {
    await markDone(taskId, userId);
    await reload();
  }

  function exportRows(kind: "json" | "csv") {
    const rows = visible.map((task) => ({
      id: task.id,
      title: task.title,
      status: task.status,
      priority: task.priority,
      due_date: task.due_date,
      needs_review: task.needs_review,
      review_reason: task.review_reason,
    }));
    if (kind === "json") {
      downloadText("tasks.json", toJson(rows), "application/json");
    } else {
      downloadText("tasks.csv", toCsv(rows), "text/csv");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <select
          className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
          value={status}
          onChange={(event) => setStatus(event.target.value as TaskFilter | "all")}
        >
          <option value="open">открытые</option>
          <option value="done">сделанные</option>
          <option value="all">все</option>
        </select>
        <label className="flex items-center gap-2 text-zinc-400">
          <input
            type="checkbox"
            checked={onlyReview}
            onChange={(event) => setOnlyReview(event.target.checked)}
          />
          требует проверки
        </label>
        <button type="button" className="text-zinc-400 hover:text-zinc-200" onClick={() => exportRows("json")}>
          JSON
        </button>
        <button type="button" className="text-zinc-400 hover:text-zinc-200" onClick={() => exportRows("csv")}>
          CSV
        </button>
      </div>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="text-xs uppercase text-zinc-500">
            <tr>
              <th className="py-2 pr-3">Заголовок</th>
              <th className="py-2 pr-3">Срок</th>
              <th className="py-2 pr-3">Приоритет</th>
              <th className="py-2 pr-3">Статус</th>
              <th className="py-2 pr-3">Проверка</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {visible.map((task) => (
              <tr key={task.id}>
                <td className="py-2 pr-3">
                  <Link to={`/items/task/${task.id}`} className="hover:underline">
                    {task.title}
                  </Link>
                </td>
                <td className="py-2 pr-3 text-zinc-400">{task.due_date ?? "—"}</td>
                <td className="py-2 pr-3 text-zinc-400">{task.priority}</td>
                <td className="py-2 pr-3 text-zinc-400">{task.status}</td>
                <td className="py-2 pr-3">
                  {task.needs_review ? <ReviewBadge reason={task.review_reason} /> : "—"}
                </td>
                <td className="py-2 text-right">
                  {task.status !== "done" ? (
                    <button
                      type="button"
                      className="text-zinc-300 hover:text-white"
                      onClick={() => complete(task.id)}
                    >
                      Выполнить
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {visible.length === 0 ? <p className="text-sm text-zinc-500">Нет задач по фильтру.</p> : null}
    </section>
  );
}
