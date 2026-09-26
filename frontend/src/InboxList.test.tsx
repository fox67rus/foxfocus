import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { InboxList } from "./components/InboxList";
import { mergeInbox } from "./types";

describe("inbox list", () => {
  it("renders titles and the review badge with a reason", () => {
    const items = mergeInbox(
      [
        {
          id: 1,
          created_at: "2026-09-26T10:00:00Z",
          title: "Отправить договор",
          due_date: "2026-09-27",
          priority: "high",
          status: "todo",
          tags: [],
          needs_review: false,
          review_reason: null,
          source_text: "завтра отправить договор",
        },
      ],
      [
        {
          id: 2,
          created_at: "2026-09-26T11:00:00Z",
          text: "сделай важное",
          title: "сделай важное",
          tags: [],
          needs_review: true,
          review_reason: "VAGUE_INPUT",
          source_text: "сделай важное",
        },
      ],
    );

    render(
      <MemoryRouter>
        <InboxList items={items} />
      </MemoryRouter>,
    );

    expect(screen.getByText("сделай важное")).toBeInTheDocument();
    expect(screen.getByText("Отправить договор")).toBeInTheDocument();
    expect(screen.getByText(/требует проверки/i)).toBeInTheDocument();
    expect(screen.getByText(/слишком общий вход/i)).toBeInTheDocument();
  });
});
