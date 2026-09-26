import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { capture, getUserId, listNotes, listTasks } from "../api";
import { InboxList } from "../components/InboxList";
import { mergeInbox, type InboxItem } from "../types";

export function Inbox() {
  const navigate = useNavigate();
  const userId = getUserId();
  const [text, setText] = useState("");
  const [onlyReview, setOnlyReview] = useState(false);
  const [items, setItems] = useState<InboxItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const [tasks, notes] = await Promise.all([listTasks(userId), listNotes(userId)]);
    setItems(mergeInbox(tasks, notes));
  }

  useEffect(() => {
    reload().catch((err: Error) => setError(err.message));
  }, [userId]);

  const visible = onlyReview ? items.filter((item) => item.needs_review) : items;

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await capture(text, userId);
      setText("");
      await reload();
      navigate(`/items/${created.item_type}/${created.item_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "не удалось разобрать");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-3">
        <textarea
          className="h-32 w-full resize-y rounded border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          placeholder="Вставьте сырой текст"
          value={text}
          onChange={(event) => setText(event.target.value)}
          required
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={busy || !text.trim()}
            className="rounded bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-950 disabled:opacity-40"
          >
            {busy ? "Разбираю…" : "Разобрать"}
          </button>
          <label className="flex items-center gap-2 text-sm text-zinc-400">
            <input
              type="checkbox"
              checked={onlyReview}
              onChange={(event) => setOnlyReview(event.target.checked)}
            />
            только требует проверки
          </label>
        </div>
      </form>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <InboxList items={visible} />
    </section>
  );
}
