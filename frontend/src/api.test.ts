import { afterEach, describe, expect, it, vi } from "vitest";

import { capture, listTasks } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("posts capture with text and user_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", item_id: 1, item_type: "task", needs_review: false }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const body = await capture("купить кофе", "u_1");

    expect(body.item_type).toBe("task");
    expect(fetchMock).toHaveBeenCalledOnce();
    const [path, init] = fetchMock.mock.calls[0];
    expect(path).toBe("/capture");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ text: "купить кофе", user_id: "u_1" });
  });

  it("lists tasks with open filter", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    vi.stubGlobal("fetch", fetchMock);

    await listTasks("u_2", "open");

    const [path] = fetchMock.mock.calls[0];
    expect(String(path)).toBe("/tasks?user_id=u_2&status=open");
  });
});
