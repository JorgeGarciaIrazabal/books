import React, { useState } from "react";
import type { BookDetail } from "../../shared/types";

interface QuickJumpItem {
  kind: string;
  label: string;
  action: () => void;
}

export const QuickJumpModal: React.FC<{
  open: boolean;
  book: BookDetail;
  onClose: () => void;
  onOpenChapter: (relPath: string) => void;
  onOpenCharacter: (charId: string) => void;
  onOpenCanon: () => void;
  onChangeDiffMode: (mode: "clean" | "inline" | "sidebyside") => void;
  onToggleFocus: () => void;
}> = ({
  open,
  book,
  onClose,
  onOpenChapter,
  onOpenCharacter,
  onOpenCanon,
  onChangeDiffMode,
  onToggleFocus
}) => {
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (!open) return null;

  const items: QuickJumpItem[] = [
    ...book.chapters.map((ch) => ({
      kind: "Chapter",
      label: ch.title,
      action: () => onOpenChapter(ch.relPath)
    })),
    ...book.characters.map((c) => ({
      kind: "Character",
      label: `${c.name}${c.subtitle ? ` — ${c.subtitle}` : ""}`,
      action: () => onOpenCharacter(c.id)
    })),
    ...book.canon.map((f) => ({
      kind: "World Rule",
      label: `${f.id}: ${f.title}`,
      action: () => onOpenCanon()
    })),
    { kind: "View", label: "Show Clean Latest Draft", action: () => onChangeDiffMode("clean") },
    { kind: "View", label: "Show Changes Since Earlier Draft", action: () => onChangeDiffMode("inline") },
    { kind: "View", label: "Compare Two Drafts Side-by-Side", action: () => onChangeDiffMode("sidebyside") },
    { kind: "View", label: "Toggle Distraction-Free Focus Mode", action: () => onToggleFocus() }
  ];

  const q = query.trim().toLowerCase();
  const filtered = q
    ? items.filter((it) => `${it.kind} ${it.label}`.toLowerCase().includes(q))
    : items;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="cmd-modal" onClick={(e) => e.stopPropagation()}>
        <input
          type="text"
          autoFocus
          className="cmd-input"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedIdx(0);
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setSelectedIdx((i) => (i + 1) % Math.max(1, filtered.length));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setSelectedIdx((i) => (i - 1 + Math.max(1, filtered.length)) % Math.max(1, filtered.length));
            } else if (e.key === "Enter" && filtered[selectedIdx]) {
              e.preventDefault();
              filtered[selectedIdx].action();
              onClose();
            } else if (e.key === "Escape") {
              onClose();
            }
          }}
          placeholder="Jump to chapter, character, world rule, or action..."
        />
        <div className="cmd-results">
          {filtered.map((it, idx) => (
            <button
              key={`${it.kind}-${it.label}-${idx}`}
              type="button"
              className={`cmd-item ${idx === selectedIdx ? "is-selected" : ""}`}
              onClick={() => {
                it.action();
                onClose();
              }}
            >
              <span><strong>{it.label}</strong></span>
              <span className="pill">{it.kind}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <div style={{ padding: "14px", color: "var(--muted)", textAlign: "center" }}>
              No matching items.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const SaveMilestoneModal: React.FC<{
  open: boolean;
  onClose: () => void;
  onConfirm: (label: string, alsoBackup: boolean) => void;
}> = ({ open, onClose, onConfirm }) => {
  const [label, setLabel] = useState("");
  const [alsoBackup, setAlsoBackup] = useState(false);

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: "0 0 6px", fontFamily: "var(--serif)", fontSize: "18px" }}>
          Save Draft Milestone
        </h3>
        <p style={{ margin: "0 0 12px", fontSize: "12.5px", color: "var(--muted)" }}>
          Name this moment on your chapter's version timeline so you can compare or restore it anytime.
        </p>
        <div className="field-label">Milestone name</div>
        <input
          type="text"
          autoFocus
          className="editable-box"
          style={{ marginBottom: "10px", background: "var(--bg)" }}
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="e.g., Tightened opening scene"
        />
        <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", marginBottom: "14px", cursor: "pointer" }}>
          <input type="checkbox" checked={alsoBackup} onChange={(e) => setAlsoBackup(e.target.checked)} />
          Also save to cloud backup (when private workspace is enabled)
        </label>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              onConfirm(label.trim() || "Saved milestone", alsoBackup);
              setLabel("");
              onClose();
            }}
          >
            Save Milestone
          </button>
        </div>
      </div>
    </div>
  );
};

export const PublishModal: React.FC<{
  open: boolean;
  book: BookDetail;
  onClose: () => void;
  onConfirm: (includeAudio: boolean) => void;
}> = ({ open, book, onClose, onConfirm }) => {
  const [includeAudio, setIncludeAudio] = useState(book.hasNarrationConfig);
  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: "0 0 6px", fontFamily: "var(--serif)", fontSize: "18px" }}>
          Publish Edition to Readers
        </h3>
        <p style={{ margin: "0 0 10px", fontSize: "12.5px", color: "var(--ink-soft)", lineHeight: 1.45 }}>
          {book.isPublicEdition
            ? `Build and update the public reading edition for "${book.summary.title}".`
            : `"${book.summary.title}" is currently a private draft. Confirm only if you want to prepare and publish it to readers.`}
        </p>
        <div className="editable-box" style={{ marginBottom: "10px", fontSize: "12px" }}>
          • Checks book structure and chapter order<br />
          • Ensures 0 margin notes or audio tags appear inside reader pages<br />
          • Publishing runs only when you explicitly request it
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", marginBottom: "14px", cursor: "pointer" }}>
          <input type="checkbox" checked={includeAudio} onChange={(e) => setIncludeAudio(e.target.checked)} />
          Include separate read-aloud audio layer
        </label>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              onConfirm(includeAudio);
              onClose();
            }}
          >
            Publish to Readers
          </button>
        </div>
      </div>
    </div>
  );
};
