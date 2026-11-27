import { describe, expect, it } from "vitest";
import {
  computeOccurrenceStats,
  projectRangeThroughDiff,
  reanchorMarkdownComment
} from "../shared/anchors";
import type { CommentRecord } from "../shared/types";

describe("Hybrid Comment Anchoring", () => {
  const chapterV1 = [
    "# Chapter One: The Reluctant Steward",
    "",
    "\"I don't recall,\" Elliot said smoothly.",
    "",
    "Marissa leaned forward.",
    "",
    "Elliot swallowed. \"I don't recall anyone saying that to me.\"",
    "",
    "\"I know it sounds horrible. I don't recall.\""
  ].join("\n");

  it("disambiguates duplicate phrases accurately by occurrence and context", () => {
    const blocks = [
      "\"I don't recall,\" Elliot said smoothly.",
      "Marissa leaned forward.",
      "Elliot swallowed. \"I don't recall anyone saying that to me.\"",
      "\"I know it sounds horrible. I don't recall.\""
    ];
    const secondStats = computeOccurrenceStats(blocks, 2, 19, "I don't recall");
    expect(secondStats.paragraphNum).toBe(3);
    expect(secondStats.occurrence).toBe(2);
    expect(secondStats.totalOccurrences).toBe(3);

    const thirdStats = computeOccurrenceStats(blocks, 3, 28, "I don't recall");
    expect(thirdStats.paragraphNum).toBe(4);
    expect(thirdStats.occurrence).toBe(3);
  });

  it("re-anchors cleanly when paragraphs shift above a duplicated phrase", () => {
    const commentOnSecond: CommentRecord = {
      id: "CMT-0001",
      target: { kind: "markdown", file: "manuscript/001.md" },
      anchor: {
        quote: "I don't recall",
        originalQuote: "I don't recall",
        prefix: "Elliot swallowed. \"",
        suffix: " anyone saying that to me.\"",
        blockIndex: 2,
        startOffset: 19,
        endOffset: 33,
        occurrence: 2
      },
      author: "human",
      targetRole: "line_editor",
      intent: "revise",
      body: "Tighten second denial",
      status: "open",
      createdAt: "now",
      thread: []
    };

    const insertedParagraph = chapterV1.replace(
      "Marissa leaned forward.",
      "Marissa leaned forward.\n\nA silence fell over the room."
    );
    const updated = reanchorMarkdownComment(commentOnSecond, chapterV1, insertedParagraph, "hash-2");
    expect(updated.anchor.orphaned).toBe(false);
    expect(updated.anchor.blockIndex).toBe(3);
    expect(updated.anchor.occurrence).toBe(2);
    expect(updated.anchor.quote).toBe("I don't recall");
  });

  it("automatically projects and updates anchor when the commented text itself is rewritten", () => {
    const oldPara = "Elliot swallowed. \"I don't recall anyone saying that to me.\"";
    const newPara = "Elliot swallowed. \"I have no memory of anyone saying that to me.\"";
    const proj = projectRangeThroughDiff(oldPara, newPara, 19, 33);
    expect(proj.orphaned).toBe(false);
    expect(newPara.slice(proj.start, proj.end)).toBe(proj.quote);
    expect(proj.quote.length).toBeGreaterThan(0);

    const comment: CommentRecord = {
      id: "CMT-0002",
      target: { kind: "markdown", file: "manuscript/001.md" },
      anchor: {
        quote: "I don't recall",
        originalQuote: "I don't recall",
        prefix: "Elliot swallowed. \"",
        suffix: " anyone saying that to me.\"",
        blockIndex: 2,
        startOffset: 19,
        endOffset: 33,
        occurrence: 2
      },
      author: "human",
      targetRole: "line_editor",
      intent: "revise",
      body: "Test external rewrite survival",
      status: "open",
      createdAt: "now",
      thread: []
    };

    const newMd = chapterV1.replace(oldPara, newPara);
    const updated = reanchorMarkdownComment(comment, chapterV1, newMd, "hash-3");
    expect(updated.anchor.orphaned).toBe(false);
    expect(updated.anchor.autoUpdated).toBe(true);
    expect(updated.anchor.originalQuote).toBe("I don't recall");
  });

  it("marks deleted passage as orphaned gracefully while keeping originalQuote", () => {
    const comment: CommentRecord = {
      id: "CMT-0003",
      target: { kind: "markdown", file: "manuscript/001.md" },
      anchor: {
        quote: "Marissa leaned forward.",
        originalQuote: "Marissa leaned forward.",
        blockIndex: 1,
        startOffset: 0,
        endOffset: 23,
        occurrence: 1
      },
      author: "human",
      targetRole: "line_editor",
      intent: "critique",
      body: "Check pacing",
      status: "open",
      createdAt: "now",
      thread: []
    };
    const deletedMd = chapterV1.replace("\n\nMarissa leaned forward.", "");
    const updated = reanchorMarkdownComment(comment, chapterV1, deletedMd, "hash-4");
    expect(updated.anchor.originalQuote).toBe("Marissa leaned forward.");
  });
});
