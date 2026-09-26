import { useEffect, useState } from "react";

import { getUserId, listAudit } from "../api";
import { downloadText, toCsv, toJson } from "../export";
import type { AuditRun } from "../types";

export function Journal() {
  const userId = getUserId();
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [onlyErrors, setOnlyErrors] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAudit(userId)
      .then(setRuns)
      .catch((err: Error) => setError(err.message));
  }, [userId]);

  const visible = onlyErrors ? runs.filter((run) => run.status === "error" || run.error) : runs;

  function exportRows(kind: "json" | "csv") {
    const rows = visible.map((run) => ({
      id: run.id,
      created_at: run.created_at,
      action: run.action,
      status: run.status,
      error: run.error,
      duration_ms: run.duration_ms,
      input: run.input,
      output: run.output,
    }));
    if (kind === "json") {
      downloadText("audit.json", toJson(rows), "application/json");
    } else {
      downloadText("audit.csv", toCsv(rows), "text/csv");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label className="flex items-center gap-2 text-zinc-400">
          <input
            type="checkbox"
            checked={onlyErrors}
            onChange={(event) => setOnlyErrors(event.target.checked)}
          />
          только с ошибкой
        </label>
        <button type="button" className="text-zinc-400 hover:text-zinc-200" onClick={() => exportRows("json")}>
          JSON
        </button>
        <button type="button" className="text-zinc-400 hover:text-zinc-200" onClick={() => exportRows("csv")}>
          CSV
        </button>
      </div>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <ul className="divide-y divide-zinc-800">
        {visible.map((run) => (
          <li key={run.id} className="py-3">
            <button
              type="button"
              className="flex w-full items-start justify-between gap-3 text-left"
              onClick={() => setOpenId(openId === run.id ? null : run.id)}
            >
              <div>
                <p className="text-sm text-zinc-200">
                  {run.action} · {run.status}
                  {run.error ? <span className="ml-2 text-amber-300">{run.error}</span> : null}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {new Date(run.created_at).toLocaleString("ru-RU")} · {run.duration_ms} мс
                </p>
              </div>
              <span className="text-xs text-zinc-600">{openId === run.id ? "скрыть" : "открыть"}</span>
            </button>
            {openId === run.id ? (
              <div className="mt-3 grid gap-3 text-xs md:grid-cols-2">
                <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900 p-3 text-zinc-300">
                  {pretty(run.input)}
                </pre>
                <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900 p-3 text-zinc-300">
                  {pretty(run.output)}
                </pre>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
      {visible.length === 0 ? <p className="text-sm text-zinc-500">Журнал пуст.</p> : null}
    </section>
  );
}

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
