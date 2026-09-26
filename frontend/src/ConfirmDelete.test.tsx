import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDelete } from "./components/ConfirmDelete";

describe("confirm delete", () => {
  it("asks to confirm and can be cancelled", () => {
    const onCancel = vi.fn();
    render(<ConfirmDelete title="купить кофе" onCancel={onCancel} onConfirm={vi.fn()} />);

    expect(screen.getByRole("dialog")).toHaveTextContent("купить кофе");
    expect(screen.getByRole("dialog")).toHaveTextContent("нельзя отменить");
    screen.getByRole("button", { name: "Отмена" }).click();
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
