import { reasonLabel } from "../reasons";

type Props = {
  reason?: string | null;
};

export function ReviewBadge({ reason }: Props) {
  return (
    <span className="inline-flex items-center rounded bg-amber-500/20 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-amber-300">
      требует проверки
      {reason ? <span className="ml-1 font-normal normal-case text-amber-200/90">· {reasonLabel(reason)}</span> : null}
    </span>
  );
}
