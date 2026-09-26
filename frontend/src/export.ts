export function toJson(rows: unknown[]): string {
  return `${JSON.stringify(rows, null, 2)}\n`;
}

export function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) {
    return "";
  }
  const columns = Object.keys(rows[0]);
  const lines = [
    columns.join(","),
    ...rows.map((row) => columns.map((column) => csvCell(row[column])).join(",")),
  ];
  return `${lines.join("\n")}\n`;
}

export function downloadText(filename: string, body: string, mime: string): void {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value: unknown): string {
  const text = value == null ? "" : typeof value === "object" ? JSON.stringify(value) : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}
