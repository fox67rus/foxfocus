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

const CSV_BOM = "\uFEFF";

/** Excel на Windows без BOM читает UTF-8 как системную кодировку. */
export function withCsvBom(body: string): string {
  return body.startsWith(CSV_BOM) ? body : `${CSV_BOM}${body}`;
}

export function downloadText(filename: string, body: string, mime: string): void {
  const csv = mime.includes("csv") || filename.endsWith(".csv");
  const payload = csv ? withCsvBom(body) : body;
  const type = csv ? "text/csv;charset=utf-8" : mime;
  const blob = new Blob([payload], { type });
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
