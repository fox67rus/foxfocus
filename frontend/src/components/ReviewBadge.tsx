import { reasonLabel } from "../reasons";

type Props = {
  reason?: string | null;
  tone?: "dark" | "paper";
};

export function ReviewBadge({ reason, tone = "dark" }: Props) {
  const colors = tone === "paper" ? "bg-amber-800/15 text-amber-950" : "review-badge";
  const detail = tone === "paper" ? "text-amber-900/80" : "review-badge-detail";
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${colors}`}
    >
      требует проверки
      {reason ? <span className={`ml-1 font-normal normal-case ${detail}`}>· {reasonLabel(reason)}</span> : null}
    </span>
  );
}
