import { useEffect, useState } from "react";

import { getUserId, listAudit, pingLlm } from "../api";
import { downloadText, toCsv, toJson } from "../export";
import type { AuditRun, LlmStatus } from "../types";

export function Journal() {
  const userId = getUserId();
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [onlyErrors, setOnlyErrors] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [llm, setLlm] = useState<LlmStatus | null>(null);
  const [llmBusy, setLlmBusy] = useState(false);

  useEffect(() => {
    listAudit(userId)
      .then(setRuns)
      .catch((err: Error) => setError(err.message));
  }, [userId]);

  const visible = onlyErrors ? runs.filter((run) => run.status === "error" || run.error) : runs;

  async function checkLlm() {
    setLlmBusy(true);
    setError(null);
    try {
      const status = await pingLlm(userId);
      setLlm(status);
      setRuns(await listAudit(userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "не удалось проверить связь");
    } finally {
      setLlmBusy(false);
    }
  }

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
        <label className="flex items-center gap-2 text-muted">
          <input
            type="checkbox"
            checked={onlyErrors}
            onChange={(event) => setOnlyErrors(event.target.checked)}
          />
          только с ошибкой
        </label>
        <button
          type="button"
          className="text-muted hover:text-ink"
          onClick={() => void checkLlm()}
          disabled={llmBusy}
        >
          {llmBusy ? "проверяю связь…" : "проверка связи"}
        </button>
        {llm ? (
          <span className={llm.status === "ok" ? "text-ok" : "text-warn"}>
            {llm.mode}
            {llm.provider ? ` · ${llm.provider}` : ""}
            {llm.model ? ` · ${llm.model}` : ""}
            {llm.status === "ok" ? " · ок" : " · нет связи"}
            {` · ${llm.duration_ms} мс`}
            {llm.detail ? ` · ${llm.detail}` : ""}
          </span>
        ) : null}
        <button type="button" className="text-muted hover:text-ink" onClick={() => exportRows("json")}>
          JSON
        </button>
        <button type="button" className="text-muted hover:text-ink" onClick={() => exportRows("csv")}>
          CSV
        </button>
      </div>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      <ul className="divide-y divide-line">
        {visible.map((run) => (
          <li key={run.id} className="py-3">
            <button
              type="button"
              className="flex w-full items-start justify-between gap-3 text-left"
              onClick={() => setOpenId(openId === run.id ? null : run.id)}
            >
              <div>
                <p className="text-sm text-ink-soft">
                  {run.action} · {run.status}
                  {run.error ? <span className="ml-2 text-warn">{run.error}</span> : null}
                </p>
                <p className="mt-1 text-xs text-faint">
                  {new Date(run.created_at).toLocaleString("ru-RU")} · {run.duration_ms} мс
                </p>
              </div>
              <span className="text-xs text-dim">{openId === run.id ? "скрыть" : "открыть"}</span>
            </button>
            {openId === run.id ? (
              <div className="mt-3 space-y-2">
                {errorDetail(run.output) ? (
                  <p className="text-xs text-warn">{errorDetail(run.output)}</p>
                ) : null}
                <div className="grid gap-3 text-xs md:grid-cols-2">
                  <pre className="overflow-auto rounded border border-line bg-surface p-3 text-ink-soft">
                    {pretty(run.input)}
                  </pre>
                  <pre className="overflow-auto rounded border border-line bg-surface p-3 text-ink-soft">
                    {pretty(run.output)}
                  </pre>
                </div>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
      {visible.length === 0 ? <p className="text-sm text-faint">Журнал пуст.</p> : null}
    </section>
  );
}

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function errorDetail(value: unknown): string | null {
  if (value && typeof value === "object" && "error_detail" in value) {
    const detail = (value as { error_detail?: unknown }).error_detail;
    return typeof detail === "string" ? detail : null;
  }
  return null;
}
