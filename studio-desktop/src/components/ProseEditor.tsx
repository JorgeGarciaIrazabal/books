import React, { useEffect, useMemo, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import type { ChapterContent, CommentRecord, VersionEntry } from "../../shared/types";
import { diffWords } from "../../shared/diff";
import {
  bodyMarkdownToEditorHtml,
  countWords,
  editorJsonToChapterMarkdown,
  splitChapterMarkdown
} from "../../shared/markdown";
import { computeOccurrenceStats } from "../../shared/anchors";
import { CommentAnchorMark } from "./CommentMark";

export interface DraftSelectionAnchor {
  kind: "markdown";
  blockIndex: number;
  startOffset: number;
  endOffset: number;
  quote: string;
  prefix: string;
  suffix: string;
  occurrence?: number;
  totalOccurrences: number;
}

interface ProseEditorProps {
  chapter: ChapterContent;
  comments: CommentRecord[];
  activeCmtId: string | null;
  diffMode: "clean" | "inline" | "sidebyside";
  plainTextMode: boolean;
  baselineVersionId: string;
  baselineText: string;
  externalBanner: string | null;
  onDismissBanner: () => void;
  onChangeDiffMode: (mode: "clean" | "inline" | "sidebyside") => void;
  onSelectBaseline: (versionId: string) => void;
  onOpenVersions: () => void;
  onOpenSaveMilestone: () => void;
  onSaveChapter: (rawMarkdown: string, updatedComments?: CommentRecord[]) => void;
  onSelectComment: (cmtId: string) => void;
  onStartCommentFromSelection: (anchor: DraftSelectionAnchor, role?: string, intent?: string) => void;
}

export const ProseEditor: React.FC<ProseEditorProps> = ({
  chapter,
  comments,
  activeCmtId,
  diffMode,
  plainTextMode,
  baselineVersionId,
  baselineText,
  externalBanner,
  onDismissBanner,
  onChangeDiffMode,
  onSelectBaseline,
  onOpenVersions,
  onOpenSaveMilestone,
  onSaveChapter,
  onSelectComment,
  onStartCommentFromSelection
}) => {
  const [title, setTitle] = useState(chapter.title);
  const [plainDraft, setPlainDraft] = useState(chapter.rawMarkdown);
  const [selectionBar, setSelectionBar] = useState<{
    top: number;
    left: number;
    anchor: DraftSelectionAnchor;
  } | null>(null);

  const saveTimerRef = useRef<number | null>(null);
  const titleRef = useRef(title);
  const commentsRef = useRef(comments);
  const suppressUpdateRef = useRef(false);
  const ownSavedShaRef = useRef<string | null>(null);
  titleRef.current = title;
  commentsRef.current = comments;

  useEffect(() => {
    if (ownSavedShaRef.current && ownSavedShaRef.current === chapter.sha256) {
      return;
    }
    setTitle(chapter.title);
    setPlainDraft(chapter.rawMarkdown);
  }, [chapter.relPath, chapter.sha256, chapter.title, chapter.rawMarkdown]);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      Placeholder.configure({ placeholder: "Begin writing your scene..." }),
      CommentAnchorMark
    ],
    content: bodyMarkdownToEditorHtml(chapter.bodyMarkdown),
    onUpdate: ({ editor: ed }) => {
      if (suppressUpdateRef.current) return;
      const doc = ed.state.doc;
      const newMd = editorJsonToChapterMarkdown(titleRef.current, ed.getJSON());
      setPlainDraft(newMd);

      // Extract live updated positions for every active comment mark in this chapter
      const updatedRanges = new Map<
        string,
        { blockIndex: number; startOffset: number; endOffset: number; quote: string; prefix: string; suffix: string }
      >();

      const blocks: string[] = [];
      doc.forEach((blockNode, _pos, blockIndex) => {
        blocks.push(blockNode.textContent);
        let charOffset = 0;
        blockNode.descendants((child) => {
          if (!child.isText) return true;
          const text = child.text ?? "";
          for (const mark of child.marks) {
            if (mark.type.name === "commentAnchor" && mark.attrs.cmtId) {
              const cmtId = String(mark.attrs.cmtId);
              const prev = updatedRanges.get(cmtId);
              const start = prev ? Math.min(prev.startOffset, charOffset) : charOffset;
              const end = prev ? Math.max(prev.endOffset, charOffset + text.length) : charOffset + text.length;
              const fullBlk = blockNode.textContent;
              updatedRanges.set(cmtId, {
                blockIndex,
                startOffset: start,
                endOffset: end,
                quote: fullBlk.slice(start, end),
                prefix: fullBlk.slice(Math.max(0, start - 36), start),
                suffix: fullBlk.slice(end, Math.min(fullBlk.length, end + 36))
              });
            }
          }
          charOffset += text.length;
          return true;
        });
      });

      let commentsChanged = false;
      const nextComments = commentsRef.current.map((c) => {
        if (c.target.kind !== "markdown" || c.target.file !== chapter.relPath || c.status === "resolved") {
          return c;
        }
        const live = updatedRanges.get(c.id);
        if (live && live.endOffset > live.startOffset) {
          const stats = computeOccurrenceStats(blocks, live.blockIndex, live.startOffset, live.quote);
          const autoUpdated = live.quote !== c.anchor.originalQuote;
          if (
            live.blockIndex !== c.anchor.blockIndex ||
            live.startOffset !== c.anchor.startOffset ||
            live.endOffset !== c.anchor.endOffset ||
            live.quote !== c.anchor.quote ||
            c.anchor.orphaned
          ) {
            commentsChanged = true;
            return {
              ...c,
              anchor: {
                ...c.anchor,
                blockIndex: live.blockIndex,
                startOffset: live.startOffset,
                endOffset: live.endOffset,
                quote: live.quote,
                prefix: live.prefix,
                suffix: live.suffix,
                occurrence: stats.occurrence ?? undefined,
                autoUpdated,
                orphaned: false
              }
            };
          }
        } else if (!live && !c.anchor.orphaned) {
          commentsChanged = true;
          return {
            ...c,
            anchor: { ...c.anchor, orphaned: true }
          };
        }
        return c;
      });

      if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
      saveTimerRef.current = window.setTimeout(() => {
        // Compute sha256-free optimistic guard by letting App pass or using pending flag:
        ownSavedShaRef.current = "__PENDING__";
        onSaveChapter(newMd, commentsChanged ? nextComments : undefined);
      }, 420);
    },
    onSelectionUpdate: ({ editor: ed }) => {
      const { from, to, empty } = ed.state.selection;
      if (empty) {
        setSelectionBar(null);
        return;
      }
      const doc = ed.state.doc;
      const $from = doc.resolve(from);
      const $to = doc.resolve(to);
      if ($from.index(0) !== $to.index(0)) {
        setSelectionBar(null);
        return;
      }
      const blockIndex = $from.index(0);
      const blockNode = doc.child(blockIndex);
      const blockStart = $from.start(1);
      const startOffset = Math.max(0, from - blockStart);
      const endOffset = Math.max(startOffset, to - blockStart);
      const quote = blockNode.textContent.slice(startOffset, endOffset).trim();
      if (quote.length < 2) {
        setSelectionBar(null);
        return;
      }

      const blocks: string[] = [];
      doc.forEach((n) => blocks.push(n.textContent));
      const stats = computeOccurrenceStats(blocks, blockIndex, startOffset, quote);
      const coords = ed.view.coordsAtPos(from);

      setSelectionBar({
        top: Math.max(54, coords.top - 44),
        left: Math.max(16, Math.min(window.innerWidth - 320, coords.left)),
        anchor: {
          kind: "markdown",
          blockIndex,
          startOffset,
          endOffset,
          quote,
          prefix: blockNode.textContent.slice(Math.max(0, startOffset - 36), startOffset),
          suffix: blockNode.textContent.slice(endOffset, Math.min(blockNode.textContent.length, endOffset + 36)),
          occurrence: stats.occurrence ?? undefined,
          totalOccurrences: stats.totalOccurrences
        }
      });
    }
  });

  // Sync editor content + marks ONLY when switching chapter or receiving an external/restore update
  useEffect(() => {
    if (!editor) return;
    if (ownSavedShaRef.current === "__PENDING__") {
      ownSavedShaRef.current = chapter.sha256;
      return;
    }
    if (ownSavedShaRef.current === chapter.sha256) return;
    ownSavedShaRef.current = null;
    suppressUpdateRef.current = true;
    editor.commands.setContent(bodyMarkdownToEditorHtml(chapter.bodyMarkdown), false);
    applyCommentMarks(editor, chapter.relPath, comments, activeCmtId);
    suppressUpdateRef.current = false;
  }, [editor, chapter.relPath, chapter.sha256]);

  // Refresh mark active highlights without resetting content
  useEffect(() => {
    if (!editor) return;
    suppressUpdateRef.current = true;
    applyCommentMarks(editor, chapter.relPath, comments, activeCmtId);
    suppressUpdateRef.current = false;
  }, [editor, chapter.relPath, comments, activeCmtId]);

  const currentBlocks = useMemo(() => splitChapterMarkdown(plainDraft).blocks, [plainDraft]);
  const baseBlocks = useMemo(() => splitChapterMarkdown(baselineText).blocks, [baselineText]);

  const diffIndices = useMemo(() => {
    const indices: number[] = [];
    const maxLen = Math.max(currentBlocks.length, baseBlocks.length);
    for (let i = 0; i < maxLen; i++) {
      if ((currentBlocks[i] ?? "") !== (baseBlocks[i] ?? "")) indices.push(i);
    }
    return indices;
  }, [currentBlocks, baseBlocks]);

  const handleTitleChange = (nextTitle: string) => {
    setTitle(nextTitle);
    titleRef.current = nextTitle;
    if (!editor) return;
    const newMd = editorJsonToChapterMarkdown(nextTitle, editor.getJSON());
    setPlainDraft(newMd);
    if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(() => {
      ownSavedShaRef.current = "__PENDING__";
      onSaveChapter(newMd);
    }, 420);
  };

  const handleRestoreParagraph = (idx: number) => {
    const oldPara = baseBlocks[idx] ?? "";
    const nextBlocks = [...currentBlocks];
    nextBlocks[idx] = oldPara;
    const rebuilt = `${title.trim() ? `# ${title.trim()}\n\n` : ""}${nextBlocks.join("\n\n")}\n`;
    ownSavedShaRef.current = null;
    setPlainDraft(rebuilt);
    onSaveChapter(rebuilt);
  };

  const wordCount = countWords(splitChapterMarkdown(plainDraft).bodyMarkdown);
  const latestVer = chapter.versions[0];

  return (
    <>
      <div className="doc-toolbar">
        <div className="doc-toolbar-left">
          <button type="button" className="version-pill" onClick={onOpenVersions}>
            <span>Draft {latestVer ? latestVer.num : 1} (Current)</span>
            <span style={{ color: "var(--muted)", fontWeight: 400 }}>
              ({chapter.versions.length} saved)
            </span>
          </button>
          <div className="seg" role="group" aria-label="Change view">
            <button
              type="button"
              className={diffMode === "clean" ? "is-active" : ""}
              onClick={() => onChangeDiffMode("clean")}
            >
              Clean
            </button>
            <button
              type="button"
              className={diffMode === "inline" ? "is-active" : ""}
              onClick={() => onChangeDiffMode("inline")}
            >
              Show Changes
            </button>
            <button
              type="button"
              className={diffMode === "sidebyside" ? "is-active" : ""}
              onClick={() => onChangeDiffMode("sidebyside")}
            >
              Compare Drafts
            </button>
          </div>
          <select
            className="baseline-select"
            value={baselineVersionId}
            onChange={(e) => onSelectBaseline(e.target.value)}
            aria-label="Baseline draft to compare"
          >
            {chapter.versions.map((v: VersionEntry) => (
              <option key={v.id} value={v.id}>
                Compare with Draft {v.num} ({v.author})
              </option>
            ))}
          </select>
        </div>
        <div className="doc-toolbar-right">
          <span style={{ fontSize: "11.5px", color: "var(--muted)" }}>
            {diffIndices.length > 0
              ? `${diffIndices.length} paragraph(s) changed`
              : "Matches selected draft"}
          </span>
          <button type="button" className="btn btn-sm" onClick={onOpenSaveMilestone}>
            + Save Milestone
          </button>
        </div>
      </div>

      <div className="canvas-scroll">
        {externalBanner && (
          <div className="sync-banner">
            <div style={{ fontSize: "12.5px" }}>{externalBanner}</div>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                className="btn btn-sm btn-sage"
                onClick={() => onChangeDiffMode("inline")}
              >
                Show Changes
              </button>
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => onChangeDiffMode("sidebyside")}
              >
                Compare Drafts
              </button>
              <button type="button" className="btn btn-sm" onClick={onDismissBanner}>
                Dismiss
              </button>
            </div>
          </div>
        )}

        {plainTextMode ? (
          <div className="paper">
            <div className="chapter-eyebrow">PLAIN TEXT SOURCE</div>
            <div className="editable-box" style={{ marginBottom: "14px", fontSize: "12px" }}>
              Margin notes and draft history are stored separately so your manuscript text stays spotless.
            </div>
            <textarea
              className="raw-md-pre"
              value={plainDraft}
              onChange={(e) => {
                const next = e.target.value;
                setPlainDraft(next);
                if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
                saveTimerRef.current = window.setTimeout(() => onSaveChapter(next), 420);
              }}
            />
          </div>
        ) : diffMode === "sidebyside" ? (
          <div className="paper paper-wide">
            <div className="chapter-eyebrow">COMPARE DRAFTS</div>
            <h1 className="chapter-title-input" style={{ marginBottom: "14px" }}>
              {title}
            </h1>
            <div className="sbs-grid">
              <div className="sbs-col">
                <div className="sbs-col-header">
                  <span>Earlier Draft ({baselineVersionId})</span>
                </div>
                {currentBlocks.map((cur, idx) => {
                  const oldT = baseBlocks[idx] ?? "";
                  const changed = oldT !== cur;
                  const tokens = changed ? diffWords(oldT, cur) : [{ type: "same" as const, text: oldT }];
                  return (
                    <div key={idx} className={`sbs-row ${changed ? "is-changed" : ""}`}>
                      {tokens
                        .filter((t) => t.type !== "ins")
                        .map((t, ti) =>
                          t.type === "del" ? (
                            <span key={ti} className="diff-del">
                              {t.text}
                            </span>
                          ) : (
                            <React.Fragment key={ti}>{t.text}</React.Fragment>
                          )
                        )}
                    </div>
                  );
                })}
              </div>
              <div className="sbs-col">
                <div className="sbs-col-header">
                  <span>Current Draft</span>
                  <span style={{ color: "var(--sage)" }}>{wordCount} words</span>
                </div>
                {currentBlocks.map((cur, idx) => {
                  const oldT = baseBlocks[idx] ?? "";
                  const changed = oldT !== cur;
                  const tokens = changed ? diffWords(oldT, cur) : [{ type: "same" as const, text: cur }];
                  return (
                    <div key={idx} className={`sbs-row ${changed ? "is-changed" : ""}`}>
                      {changed && (
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontFamily: "var(--sans)" }}>
                          <span className="pill pill-writer">Changed</span>
                          <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() => handleRestoreParagraph(idx)}
                          >
                            Restore paragraph
                          </button>
                        </div>
                      )}
                      {tokens
                        .filter((t) => t.type !== "del")
                        .map((t, ti) =>
                          t.type === "ins" ? (
                            <span key={ti} className="diff-ins">
                              {t.text}
                            </span>
                          ) : (
                            <React.Fragment key={ti}>{t.text}</React.Fragment>
                          )
                        )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : diffMode === "inline" ? (
          <div className="paper">
            <div className="chapter-eyebrow">CHANGES SINCE {baselineVersionId.toUpperCase()}</div>
            <h1 className="chapter-title-input" style={{ marginBottom: "14px" }}>
              {title}
            </h1>
            {currentBlocks.map((cur, idx) => {
              const oldT = baseBlocks[idx] ?? "";
              const changed = oldT !== cur;
              const tokens = changed ? diffWords(oldT, cur) : [{ type: "same" as const, text: cur }];
              return (
                <div key={idx} className={`diff-block ${changed ? "is-changed" : ""}`}>
                  {changed && (
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontFamily: "var(--sans)" }}>
                      <span className="pill pill-writer">Paragraph {idx + 1} updated</span>
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={() => handleRestoreParagraph(idx)}
                      >
                        Revert paragraph
                      </button>
                    </div>
                  )}
                  {tokens.map((t, ti) =>
                    t.type === "del" ? (
                      <span key={ti} className="diff-del">
                        {t.text}
                      </span>
                    ) : t.type === "ins" ? (
                      <span key={ti} className="diff-ins">
                        {t.text}
                      </span>
                    ) : (
                      <React.Fragment key={ti}>{t.text}</React.Fragment>
                    )
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <article className="paper">
            <div className="chapter-eyebrow">MANUSCRIPT · LATEST VERSION</div>
            <input
              type="text"
              className="chapter-title-input"
              value={title}
              onChange={(e) => handleTitleChange(e.target.value)}
              aria-label="Chapter Title"
            />
            <div className="chapter-meta-row">
              <span>
                <strong>{wordCount}</strong> words · ~{Math.max(1, Math.ceil(wordCount / 220))} min read
              </span>
              <span style={{ color: "var(--muted)" }}>Auto-saving directly to your book</span>
            </div>
            <div
              className="tiptap-editor"
              onClick={(e) => {
                const target = e.target as HTMLElement;
                const markEl = target.closest("mark[data-cmt-id]") as HTMLElement | null;
                if (markEl?.dataset.cmtId) {
                  onSelectComment(markEl.dataset.cmtId);
                }
              }}
            >
              <EditorContent editor={editor} />
            </div>
          </article>
        )}
      </div>

      {selectionBar && diffMode === "clean" && !plainTextMode && (
        <div
          className="selection-bar"
          style={{ top: `${selectionBar.top}px`, left: `${selectionBar.left}px` }}
        >
          <button
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              editor?.chain().focus().toggleBold().run();
              setSelectionBar(null);
            }}
          >
            <strong>B</strong>
          </button>
          <button
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              editor?.chain().focus().toggleItalic().run();
              setSelectionBar(null);
            }}
          >
            <em>I</em>
          </button>
          <span className="sep" />
          <button
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              onStartCommentFromSelection(selectionBar.anchor);
              setSelectionBar(null);
            }}
          >
            + Add Note
          </button>
          <button
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              onStartCommentFromSelection(selectionBar.anchor, "@canon_keeper", "check-canon");
              setSelectionBar(null);
            }}
          >
            Check World Rules
          </button>
        </div>
      )}
    </>
  );
};

function applyCommentMarks(
  editor: NonNullable<ReturnType<typeof useEditor>>,
  chapterRelPath: string,
  comments: CommentRecord[],
  activeCmtId: string | null
) {
  const { state, view } = editor;
  const markType = state.schema.marks.commentAnchor;
  if (!markType) return;

  let tr = state.tr;
  // Clear existing marks before re-applying cleanly from comment coordinates
  tr = tr.removeMark(0, state.doc.content.size, markType);

  const chapterComments = comments.filter(
    (c) =>
      c.target.kind === "markdown" &&
      c.target.file === chapterRelPath &&
      c.status !== "resolved" &&
      !c.anchor.orphaned &&
      typeof c.anchor.blockIndex === "number" &&
      typeof c.anchor.startOffset === "number" &&
      typeof c.anchor.endOffset === "number"
  );

  for (const c of chapterComments) {
    const bIdx = c.anchor.blockIndex!;
    if (bIdx < 0 || bIdx >= state.doc.childCount) continue;
    let blockPos = 0;
    for (let i = 0; i < bIdx; i++) {
      blockPos += state.doc.child(i).nodeSize;
    }
    const blockNode = state.doc.child(bIdx);
    const textStart = blockPos + 1;
    const maxLen = blockNode.textContent.length;
    const s = Math.max(0, Math.min(maxLen, c.anchor.startOffset!));
    const e = Math.max(s, Math.min(maxLen, c.anchor.endOffset!));
    if (e > s) {
      tr = tr.addMark(
        textStart + s,
        textStart + e,
        markType.create({ cmtId: c.id, active: c.id === activeCmtId })
      );
    }
  }
  view.dispatch(tr);
}
