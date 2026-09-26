import { useEffect, useState } from "react";

import { getUserId, listNotes } from "../api";
import { NoteStickers } from "../components/NoteStickers";
import { downloadText, toCsv, toJson } from "../export";
import type { Note } from "../types";

export function Notes() {
  const userId = getUserId();
  const [onlyReview, setOnlyReview] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listNotes(userId)
      .then(setNotes)
      .catch((err: Error) => setError(err.message));
  }, [userId]);

  const visible = onlyReview ? notes.filter((note) => note.needs_review) : notes;

  function exportRows(kind: "json" | "csv") {
    const rows = visible.map((note) => ({
      id: note.id,
      title: note.title || note.text,
      needs_review: note.needs_review,
      review_reason: note.review_reason,
    }));
    if (kind === "json") {
      downloadText("notes.json", toJson(rows), "application/json");
    } else {
      downloadText("notes.csv", toCsv(rows), "text/csv");
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
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
      <NoteStickers notes={visible} />
    </section>
  );
}
