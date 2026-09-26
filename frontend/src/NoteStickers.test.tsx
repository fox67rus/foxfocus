import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { NoteStickers } from "./components/NoteStickers";

describe("note stickers", () => {
  it("renders a note as a sticker with a review badge", () => {
    render(
      <MemoryRouter>
        <NoteStickers
          notes={[
            {
              id: 2,
              created_at: "2026-09-26T11:00:00Z",
              text: "идея: вынести поиск",
              title: "идея: вынести поиск",
              tags: [],
              needs_review: true,
              review_reason: "VAGUE_INPUT",
              source_text: "идея: вынести поиск",
            },
          ]}
        />
      </MemoryRouter>,
    );

    const card = screen.getByRole("link", { name: /идея: вынести поиск/i });
    expect(card).toHaveAttribute("href", "/items/note/2");
    expect(card).toHaveClass("note-sticker");
    expect(screen.getByText(/требует проверки/i)).toBeInTheDocument();
  });
});
