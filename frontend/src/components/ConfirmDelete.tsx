type Props = {
  title: string;
  busy?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export function ConfirmDelete({ title, busy = false, onCancel, onConfirm }: Props) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-delete-title"
      className="fixed inset-0 z-20 flex items-center justify-center bg-black/60 p-4"
    >
      <div className="w-full max-w-sm space-y-4 rounded border border-zinc-700 bg-zinc-900 p-4 shadow-xl">
        <p id="confirm-delete-title" className="text-sm text-zinc-100">
          Удалить «{title}»? Это нельзя отменить.
        </p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            className="text-sm text-zinc-400 hover:text-zinc-200 disabled:opacity-40"
            onClick={onCancel}
            disabled={busy}
          >
            Отмена
          </button>
          <button
            type="button"
            className="rounded bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-40"
            onClick={onConfirm}
            disabled={busy}
          >
            {busy ? "Удаляю…" : "Удалить"}
          </button>
        </div>
      </div>
    </div>
  );
}
