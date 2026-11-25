import { describe, expect, it } from "vitest";
import { demoFollowUp, demoNote, type DemoInfo } from "./demo";

const empty: DemoInfo = { has_draft: false, has_poster: false, on_link: false, pending: false, updated_at: null };

describe("demo notes", () => {
  it("waits for publication before the intern can watch", () => {
    const draft = { ...empty, has_draft: true };
    expect(demoNote(draft, "none")).toContain("после публикации");
    expect(demoFollowUp(draft, "none")).toBeNull();
  });

  it("keeps the sent link on the previous video until the editor updates it", () => {
    const replaced = { ...empty, has_draft: true, on_link: true, pending: true };
    expect(demoNote(replaced, "published")).toContain("прежнее демо");
    expect(demoFollowUp(replaced, "published")).toBe("show");
    expect(demoFollowUp(replaced, "outdated")).toBeNull();
  });

  it("asks for an update to take a removed video off the link", () => {
    const removed = { ...empty, on_link: true, pending: true };
    expect(demoNote(removed, "published")).toContain("убрать");
    expect(demoFollowUp(removed, "published")).toBe("remove");
  });

  it("says when the link already matches the studio", () => {
    expect(demoNote({ ...empty, has_draft: true, on_link: true }, "published")).toContain("над страницей");
  });
});
