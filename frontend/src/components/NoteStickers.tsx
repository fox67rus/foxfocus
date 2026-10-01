import { Link } from "react-router-dom";

import type { Note } from "../types";
import { ReviewBadge } from "./ReviewBadge";

type Props = {
  notes: Note[];
};

export function NoteStickers({ notes }: Props) {
  if (notes.length === 0) {
    return <p className="text-sm text-faint">Пока нет заметок.</p>;
  }

  return (
    <ul className="note-board">
      {notes.map((note) => (
        <li key={note.id}>
          <Link to={`/items/note/${note.id}`} className="note-sticker">
            <p className="note-sticker-title">{note.title || note.text}</p>
            <p className="note-sticker-meta">{formatWhen(note.created_at)}</p>
            {note.needs_review ? <ReviewBadge reason={note.review_reason} tone="paper" /> : null}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function formatWhen(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ru-RU");
}
