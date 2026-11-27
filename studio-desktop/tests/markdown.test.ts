import { describe, expect, it } from "vitest";
import {
  bodyMarkdownToEditorHtml,
  editorJsonToChapterMarkdown,
  splitChapterMarkdown
} from "../shared/markdown";

describe("Craft-safe Markdown utilities", () => {
  it("splits title and body blocks cleanly without injecting em dashes", () => {
    const md = [
      "# Chapter One: The Audit",
      "",
      "\"Who is it?\" she asked.",
      "",
      "\"Dorrik.\""
    ].join("\n");

    const parsed = splitChapterMarkdown(md);
    expect(parsed.title).toBe("Chapter One: The Audit");
    expect(parsed.blocks).toEqual(["\"Who is it?\" she asked.", "\"Dorrik.\""]);
  });

  it("serializes TipTap JSON back to clean Markdown without comment tags or em dashes", () => {
    const doc = {
      type: "doc",
      content: [
        {
          type: "paragraph",
          content: [
            { type: "text", text: "She kept her voice mild and " },
            { type: "text", text: "level", marks: [{ type: "italic" }, { type: "commentAnchor" }] },
            { type: "text", text: "." }
          ]
        }
      ]
    };

    const output = editorJsonToChapterMarkdown("Chapter One", doc);
    expect(output).toBe("# Chapter One\n\nShe kept her voice mild and *level*.\n");
    expect(output).not.toContain("commentAnchor");
    expect(output).not.toContain("—");
  });

  it("renders inline emphasis cleanly to editor HTML", () => {
    const html = bodyMarkdownToEditorHtml("Behind him hung *First Principles* and **Bold Truth**.");
    expect(html).toContain("<em>First Principles</em>");
    expect(html).toContain("<strong>Bold Truth</strong>");
  });
});
