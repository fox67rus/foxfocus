import { describe, expect, it } from "vitest";

import { toCsv, toJson } from "./export";

describe("export", () => {
  it("writes json and csv for a task row", () => {
    const rows = [{ id: 1, title: "купить кофе", needs_review: false }];

    expect(toJson(rows)).toContain('"title": "купить кофе"');
    expect(toCsv(rows)).toBe('id,title,needs_review\n"1","купить кофе","false"\n');
  });
});
