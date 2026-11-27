import React, { useMemo, useState } from "react";
import type {
  BackupStatus,
  BookDetail,
  ChapterContent,
  CommentRecord,
  VersionEntry
} from "../../shared/types";
import { computeOccurrenceStats } from "../../shared/anchors";

export type RailTab = "notes" | "versions" | "context" | "backups";

export interface PendingNoteTarget {
  kind: "markdown" | "record";
  file: string;
  blockIndex?: number;
  startOffset?: number;
  endOffset?: number;
  quote: string;
  prefix?: string;
  suffix?: string;
  occurrence?: number;
  totalOccurrences?: number;
  recordId?: string;
  recordTitle?: string;
  defaultRole?: string;
  defaultIntent?: string;
}

interface RightCompanionProps {
  book: BookDetail;
  activeChapter: ChapterContent | null;
  railTab: RailTab;
  activeCmtId: string | null;
  baselineVersionId: string;
  pendingTarget: PendingNoteTarget | null;
  backupStatus: BackupStatus;
  onChangeTab: (tab: RailTab) => void;
  onAddComment: (cmt: CommentRecord) => void;
  onResolveComment: (cmtId: string) => void;
  onClickComment: (cmt: CommentRecord) => void;
  onCompareVersion: (versionId: string, mode: "inline" | "sidebyside") => void;
  onRestoreVersion: (versionId: string) => void;
  onOpenSaveMilestone: () => void;
  onPinSplitRef: (refKey: string) => void;
  onChangeBackupSettings: (settings: {
    autoIntervalMinutes: number;
    privacyMode: "private-auto" | "public-pull-only";
  }) => void;
  onBackupNow: (mode: "refresh" | "save-and-share") => void;
  onCopyForAssistant: () => void;
}

const ROLE_LABELS: Record<string, string> = {
  "@line_editor": "Line Editor",
  "@canon_keeper": "World Continuity",
  "@character_director": "Character Voice",
  "@drafter": "Scene Drafter",
  "@reader_advocate": "First Reader"
};

export const RightCompanion: React.FC<RightCompanionProps> = ({
  book,
  activeChapter,
  railTab,
  activeCmtId,
  baselineVersionId,
  pendingTarget,
  backupStatus,
  onChangeTab,
  onAddComment,
  onResolveComment,
  onClickComment,
  onCompareVersion,
  onRestoreVersion,
  onOpenSaveMilestone,
  onPinSplitRef,
  onChangeBackupSettings,
  onBackupNow,
  onCopyForAssistant
}) => {
  const [scope, setScope] = useState<"all" | "page">("all");
  const [filter, setFilter] = useState<"all" | "open" | "needs-review" | "resolved">("all");
  const [role, setRole] = useState("@line_editor");
  const [intent, setIntent] = useState("revise");
  const [noteBody, setNoteBody] = useState("");
  const [manualQuote, setManualQuote] = useState("");

  React.useEffect(() => {
    if (pendingTarget) {
      setManualQuote(pendingTarget.quote);
      if (pendingTarget.defaultRole) setRole(pendingTarget.defaultRole);
      if (pendingTarget.defaultIntent) setIntent(pendingTarget.defaultIntent);
    }
  }, [pendingTarget]);

  const openCount = book.comments.filter((c) => c.status !== "resolved" && c.status !== "dismissed").length;

  const visibleComments = useMemo(() => {
    return book.comments.filter((c) => {
      if (scope === "page" && activeChapter) {
        if (c.target.kind === "markdown" && c.target.file !== activeChapter.relPath) return false;
      }
      if (filter !== "all" && c.status !== filter) return false;
      return true;
    });
  }, [book.comments, scope, filter, activeChapter]);

  const detectedContext = useMemo(() => {
    const text = activeChapter?.rawMarkdown ?? "";
    const matchedChars = book.characters.filter(
      (ch) => text.includes(ch.name) || text.toLowerCase().includes(ch.name.toLowerCase())
    );
    const matchedCanon = book.canon.filter(
      (f) => text.includes(f.title) || (f.id && text.includes(f.id))
    );
    return { matchedChars, matchedCanon };
  }, [activeChapter, book.characters, book.canon]);

  const handleSubmitNote = () => {
    const body = noteBody.trim();
    if (!body) return;

    const quote = (manualQuote || pendingTarget?.quote || "").trim();
    const id = `CMT-${String(book.comments.length + 1).padStart(4, "0")}`;

    let target: CommentRecord["target"];
    if (pendingTarget && pendingTarget.kind === "record" && pendingTarget.recordId) {
      target = {
        kind: "record",
        file: pendingTarget.file,
        recordId: pendingTarget.recordId,
        recordTitle: pendingTarget.recordTitle
      };
    } else {
      target = {
        kind: "markdown",
        file: pendingTarget?.file ?? activeChapter?.relPath ?? book.chapters[0]?.relPath ?? ""
      };
    }

    const newCmt: CommentRecord = {
      id,
      target,
      anchor: {
        quote,
        originalQuote: quote,
        prefix: pendingTarget?.prefix,
        suffix: pendingTarget?.suffix,
        blockIndex: pendingTarget?.blockIndex,
        startOffset: pendingTarget?.startOffset,
        endOffset: pendingTarget?.endOffset,
        occurrence: pendingTarget?.occurrence,
        fileSha256: activeChapter?.sha256,
        autoUpdated: false,
        orphaned: false
      },
      author: "human",
      targetRole: role.replace(/^@/, ""),
      intent,
      body,
      status: "open",
      createdAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      thread: []
    };

    onAddComment(newCmt);
    setNoteBody("");
    setManualQuote("");
  };

  return (
    <aside className="sidebar-right" aria-label="Story Companion">
      <div className="rail-tabs">
        <button
          type="button"
          className={`rail-tab ${railTab === "notes" ? "is-active" : ""}`}
          onClick={() => onChangeTab("notes")}
        >
          Notes <span className="badge-count">{openCount}</span>
        </button>
        <button
          type="button"
          className={`rail-tab ${railTab === "versions" ? "is-active" : ""}`}
          onClick={() => onChangeTab("versions")}
        >
          Versions <span className="badge-count">{activeChapter?.versions.length ?? 0}</span>
        </button>
        <button
          type="button"
          className={`rail-tab ${railTab === "context" ? "is-active" : ""}`}
          onClick={() => onChangeTab("context")}
        >
          Context
        </button>
        <button
          type="button"
          className={`rail-tab ${railTab === "backups" ? "is-active" : ""}`}
          onClick={() => onChangeTab("backups")}
        >
          Backups
        </button>
      </div>

      <div className="rail-scroll">
        {railTab === "notes" && (
          <>
            <div className="composer">
              <div style={{ fontSize: "11.5px", fontWeight: 700, marginBottom: "6px", display: "flex", justifyContent: "space-between" }}>
                <span>Add Margin Note</span>
                <span style={{ color: "var(--muted)", fontWeight: 400 }}>Saved cleanly beside book</span>
              </div>
              <input
                type="text"
                value={manualQuote}
                onChange={(e) => setManualQuote(e.target.value)}
                placeholder="Highlight a line in your draft or world rule..."
              />
              {pendingTarget && pendingTarget.kind === "record" && (
                <div className="anchor-meta" style={{ color: "var(--accent)" }}>
                  Attached to World Rule · {pendingTarget.recordId} ({pendingTarget.recordTitle})
                </div>
              )}
              {pendingTarget && pendingTarget.kind === "markdown" && typeof pendingTarget.blockIndex === "number" && (
                <div className="anchor-meta" style={{ color: "var(--sage)" }}>
                  Attached to Paragraph {pendingTarget.blockIndex + 1}
                  {pendingTarget.totalOccurrences && pendingTarget.totalOccurrences > 1 && pendingTarget.occurrence
                    ? ` · mention ${pendingTarget.occurrence} of ${pendingTarget.totalOccurrences}`
                    : ""}
                </div>
              )}
              <div className="composer-row">
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="@line_editor">Line Editor</option>
                  <option value="@canon_keeper">World Continuity</option>
                  <option value="@character_director">Character Voice</option>
                  <option value="@drafter">Scene Drafter</option>
                  <option value="@reader_advocate">First Reader</option>
                </select>
                <select value={intent} onChange={(e) => setIntent(e.target.value)}>
                  <option value="revise">Revise passage</option>
                  <option value="check-canon">Check continuity</option>
                  <option value="critique">Give feedback</option>
                  <option value="personal-note">Personal note</option>
                </select>
              </div>
              <textarea
                rows={2}
                value={noteBody}
                onChange={(e) => setNoteBody(e.target.value)}
                placeholder="Write a note for your collaborator..."
              />
              <button
                type="button"
                className="btn btn-primary btn-sm"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={handleSubmitNote}
              >
                Save Note
              </button>
            </div>

            <div className="seg" style={{ width: "100%", display: "grid", gridTemplateColumns: "1fr 1fr", marginBottom: "8px" }}>
              <button type="button" className={scope === "all" ? "is-active" : ""} onClick={() => setScope("all")}>
                All Notes
              </button>
              <button type="button" className={scope === "page" ? "is-active" : ""} onClick={() => setScope("page")}>
                This Page Only
              </button>
            </div>

            <div style={{ display: "flex", gap: "4px", marginBottom: "10px", flexWrap: "wrap" }}>
              {(["all", "open", "needs-review", "resolved"] as const).map((k) => (
                <button
                  key={k}
                  type="button"
                  className={`btn btn-sm ${filter === k ? "is-active" : ""}`}
                  onClick={() => setFilter(k)}
                >
                  {k === "needs-review" ? "Needs Review" : k[0].toUpperCase() + k.slice(1)}
                </button>
              ))}
            </div>

            {visibleComments.map((c) => {
              let locationLabel = "Book note";
              if (c.target.kind === "record") {
                locationLabel = `World Rule · ${c.target.recordId}`;
              } else if (activeChapter && c.target.file === activeChapter.relPath && typeof c.anchor.blockIndex === "number") {
                const stats = computeOccurrenceStats(
                  activeChapter.blocks,
                  c.anchor.blockIndex,
                  c.anchor.startOffset,
                  c.anchor.quote
                );
                locationLabel = `Paragraph ${stats.paragraphNum}`;
                if (stats.totalOccurrences > 1 && stats.occurrence) {
                  locationLabel += ` · mention ${stats.occurrence} of ${stats.totalOccurrences}`;
                }
              } else if (c.target.kind === "markdown") {
                locationLabel = c.target.file.split("/").pop() ?? c.target.file;
              }

              const roleDisplay = ROLE_LABELS[`@${c.targetRole}`] ?? ROLE_LABELS[c.targetRole] ?? c.targetRole;

              return (
                <div
                  key={c.id}
                  className={`card ${activeCmtId === c.id ? "is-highlighted" : ""}`}
                  onClick={() => onClickComment(c)}
                  style={{ cursor: "pointer" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "4px", marginBottom: "4px" }}>
                    <span className="pill pill-role">{roleDisplay}</span>
                    <span className={`pill ${c.status === "resolved" ? "pill-sage" : c.status === "needs-review" ? "pill-gold" : ""}`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="anchor-meta">
                    <span>{locationLabel}</span>
                    {c.anchor.autoUpdated && <span className="pill pill-writer">Updated automatically</span>}
                    {c.anchor.orphaned && <span className="pill pill-rose">Line removed</span>}
                  </div>
                  {c.anchor.quote && <div className="card-quote">"{c.anchor.quote}"</div>}
                  <div style={{ fontSize: "12.5px", lineHeight: 1.45, marginBottom: "8px" }}>{c.body}</div>
                  {c.thread.length > 0 && (
                    <div className="agent-reply-box">
                      <strong>{c.thread[c.thread.length - 1].author}:</strong> {c.thread[c.thread.length - 1].body}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: "6px", marginTop: "8px", alignItems: "center" }}>
                    {c.status !== "resolved" && (
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onResolveComment(c.id);
                        }}
                      >
                        Mark Resolved
                      </button>
                    )}
                    <span style={{ fontSize: "11px", color: "var(--muted)", marginLeft: "auto" }}>{c.createdAt}</span>
                  </div>
                </div>
              );
            })}
            {visibleComments.length === 0 && (
              <div className="card" style={{ color: "var(--muted)", textAlign: "center" }}>
                No notes in this view yet.
              </div>
            )}
          </>
        )}

        {railTab === "versions" && (
          <>
            <div className="card" style={{ background: "var(--panel-alt)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <strong style={{ fontSize: "12.5px" }}>Draft Versions</strong>
                <button type="button" className="btn btn-sm btn-primary" onClick={onOpenSaveMilestone}>
                  + Save Milestone
                </button>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--muted)", lineHeight: 1.45 }}>
                Your studio saves snapshots automatically. Restoring an earlier draft always creates a new draft so nothing is lost.
              </div>
            </div>

            {(activeChapter?.versions ?? []).map((v: VersionEntry, idx: number) => (
              <div key={v.id} className={`card ${baselineVersionId === v.id ? "is-highlighted" : ""}`}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <strong>Draft {v.num}</strong>
                    <span className={`pill ${v.role === "external" ? "pill-sage" : "pill-writer"}`}>{v.author}</span>
                    {idx === 0 && <span className="pill pill-gold">Current</span>}
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--muted)" }}>{v.timestamp}</span>
                </div>
                <div style={{ fontSize: "12.5px", marginBottom: "4px" }}>{v.summary}</div>
                <div style={{ fontSize: "11px", color: "var(--muted)", marginBottom: "8px" }}>{v.delta}</div>
                <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
                  <button type="button" className="btn btn-sm" onClick={() => onCompareVersion(v.id, "inline")}>
                    Show Changes
                  </button>
                  <button type="button" className="btn btn-sm" onClick={() => onCompareVersion(v.id, "sidebyside")}>
                    Compare Drafts
                  </button>
                  {idx > 0 && (
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={() => onRestoreVersion(v.id)}
                    >
                      Restore
                    </button>
                  )}
                </div>
              </div>
            ))}
          </>
        )}

        {railTab === "context" && (
          <>
            <div className="card" style={{ background: "var(--panel-alt)" }}>
              <strong style={{ fontSize: "12.5px" }}>Appearing in This Chapter</strong>
              <div style={{ fontSize: "11.5px", color: "var(--muted)", marginTop: "3px" }}>
                Characters and world rules recognized in the active draft.
              </div>
            </div>
            {detectedContext.matchedChars.map((ch) => (
              <div key={ch.id} className="card">
                <div style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--accent)", textTransform: "uppercase" }}>
                  Character · {ch.id}
                </div>
                <div style={{ fontWeight: 700, margin: "3px 0" }}>{ch.name}</div>
                <div style={{ fontSize: "12px", color: "var(--ink-soft)", marginBottom: "8px" }}>{ch.role || ch.subtitle}</div>
                <button type="button" className="btn btn-sm" onClick={() => onPinSplitRef(ch.id)}>
                  Pin Beside Draft
                </button>
              </div>
            ))}
            {detectedContext.matchedCanon.map((f) => (
              <div key={f.id} className="card">
                <div style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--sage)", textTransform: "uppercase" }}>
                  World Rule · {f.id}
                </div>
                <div style={{ fontWeight: 700, margin: "3px 0" }}>{f.title}</div>
                <div style={{ fontSize: "12px", color: "var(--ink-soft)", marginBottom: "8px" }}>{f.text}</div>
                <button type="button" className="btn btn-sm" onClick={() => onPinSplitRef(f.id)}>
                  Pin Beside Draft
                </button>
              </div>
            ))}
            {detectedContext.matchedChars.length === 0 && detectedContext.matchedCanon.length === 0 && (
              <div className="card" style={{ color: "var(--muted)" }}>
                Pin any character or world rule using Split Reference in the top bar.
              </div>
            )}
          </>
        )}

        {railTab === "backups" && (
          <>
            <div className="card" style={{ background: "var(--panel-alt)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <strong style={{ fontSize: "12.5px" }}>Automatic Saving &amp; Cloud Backups</strong>
                <span className={`pill ${backupStatus.ahead || backupStatus.behind ? "pill-gold" : "pill-sage"}`}>
                  {backupStatus.ahead > 0 ? "Unsaved backup" : "Backed up"}
                </span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--muted)", marginBottom: "8px" }}>
                Last backup: <strong>{backupStatus.lastBackupTime}</strong>
              </div>
              <div className="composer-row" style={{ marginBottom: "7px" }}>
                <select
                  className="baseline-select"
                  style={{ flex: 1 }}
                  value={backupStatus.autoIntervalMinutes}
                  onChange={(e) =>
                    onChangeBackupSettings({
                      autoIntervalMinutes: Number(e.target.value),
                      privacyMode: backupStatus.privacyMode
                    })
                  }
                >
                  <option value={1}>Back up automatically every 1 minute</option>
                  <option value={2}>Back up automatically every 2 minutes</option>
                  <option value={5}>Back up automatically every 5 minutes</option>
                  <option value={0}>Back up manually only</option>
                </select>
              </div>
              <div style={{ marginBottom: "10px" }}>
                <select
                  className="baseline-select"
                  style={{ width: "100%" }}
                  value={backupStatus.privacyMode}
                  onChange={(e) =>
                    onChangeBackupSettings({
                      autoIntervalMinutes: backupStatus.autoIntervalMinutes,
                      privacyMode: e.target.value as "private-auto" | "public-pull-only"
                    })
                  }
                >
                  <option value="private-auto">Private workspace (auto-save &amp; check updates)</option>
                  <option value="public-pull-only">Public catalog (keep unpublished drafts on this computer)</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="btn btn-sm btn-primary"
                  style={{ flex: 1, justifyContent: "center" }}
                  onClick={() => onBackupNow("save-and-share")}
                >
                  Save &amp; Back Up Now
                </button>
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => onBackupNow("refresh")}
                >
                  Check for Updates
                </button>
              </div>
            </div>

            <div className="card" style={{ background: "var(--panel-alt)" }}>
              <strong style={{ fontSize: "12.5px" }}>Collaborate with Your Writing Assistant</strong>
              <div style={{ fontSize: "11.5px", color: "var(--muted)", margin: "4px 0 10px", lineHeight: 1.45 }}>
                Your notes stay saved beside your book. Copy a prompt for Antigravity whenever you want your editorial notes addressed; changes will appear here automatically.
              </div>
              <button
                type="button"
                className="btn btn-sm btn-primary"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={onCopyForAssistant}
              >
                Copy Notes for Assistant
              </button>
            </div>

            {backupStatus.recentEvents.map((ev) => (
              <div key={ev.id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span className="pill pill-sage">{ev.source}</span>
                  <span style={{ fontSize: "11px", color: "var(--muted)" }}>{ev.time}</span>
                </div>
                <div style={{ fontSize: "12.5px", lineHeight: 1.45 }}>{ev.summary}</div>
              </div>
            ))}
          </>
        )}
      </div>
    </aside>
  );
};
