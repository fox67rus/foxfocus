import { Link } from "react-router-dom";

import type { InboxItem } from "../types";
import { ReviewBadge } from "./ReviewBadge";

type Props = {
  items: InboxItem[];
};

export function InboxList({ items }: Props) {
  if (items.length === 0) {
    return <p className="text-sm text-zinc-500">Пока пусто. Вставьте текст и нажмите «Разобрать».</p>;
  }

  return (
    <ul className="divide-y divide-zinc-800">
      {items.map((item) => (
        <li key={`${item.kind}-${item.id}`}>
          <Link
            to={`/items/${item.kind}/${item.id}`}
            className="flex items-start justify-between gap-4 py-3 hover:bg-zinc-900/60"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-zinc-100">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-500">
                {item.kind === "task" ? "задача" : "заметка"} · {formatWhen(item.created_at)}
              </p>
            </div>
            {item.needs_review ? <ReviewBadge reason={item.review_reason} /> : null}
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
