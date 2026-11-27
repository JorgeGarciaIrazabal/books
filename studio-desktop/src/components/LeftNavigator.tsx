import React, { useState } from "react";
import type { AppUpdateStatus, BookDetail, BookSummary } from "../../shared/types";

export type AppView =
  | "chapter"
  | "brief"
  | "scenes"
  | "style"
  | "characters"
  | "bible"
  | "canon"
  | "knowledge"
  | "gates"
  | "publish";

interface LeftNavigatorProps {
  books: BookSummary[];
  book: BookDetail;
  activeView: AppView;
  activeChapterRel: string;
  appUpdateStatus: AppUpdateStatus;
  onSelectBook: (bookRelPath: string) => void;
  onChooseLibraryFolder: () => void;
  onSelectView: (view: AppView, chapterRel?: string) => void;
  onOpenExternalUrl: (url: string) => void;
  onOpenUpdatePanel: () => void;
  onCreateChapter: () => void;
  onMoveChapter: (index: number, dir: -1 | 1) => void;
}

export const LeftNavigator: React.FC<LeftNavigatorProps> = ({
  books,
  book,
  activeView,
  activeChapterRel,
  appUpdateStatus,
  onSelectBook,
  onChooseLibraryFolder,
  onSelectView,
  onOpenExternalUrl,
  onOpenUpdatePanel,
  onCreateChapter,
  onMoveChapter
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const canonNotes = book.comments.filter(
    (c) => c.target.kind === "record" && c.status !== "resolved"
  ).length;

  const initials = book.summary.title
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <aside className="sidebar-left" aria-label="Story Navigator">
      <div className="book-switcher-wrap">
        <button
          type="button"
          className="book-switcher-btn"
          onClick={() => setDropdownOpen((v) => !v)}
        >
          <div className="book-cover-mini">{initials || "BK"}</div>
          <div className="book-meta">
            <div className="book-universe-label">{book.summary.universeTitle}</div>
            <div className="book-title-label">{book.summary.title}</div>
            <div className="book-stage-row">
              <span className="stage-pill">{book.summary.stage}</span>
              <span>
                {book.chapters.length} ch · {book.characters.length} chars
              </span>
            </div>
          </div>
          <span style={{ color: "var(--muted)", fontSize: "12px" }}>▾</span>
        </button>

        {dropdownOpen && (
          <div className="book-dropdown">
            {books.map((b) => (
              <button
                key={b.relPath}
                type="button"
                className={`book-option ${b.relPath === book.summary.relPath ? "is-selected" : ""}`}
                onClick={() => {
                  setDropdownOpen(false);
                  onSelectBook(b.relPath);
                }}
              >
                <div className="book-cover-mini" style={{ width: 26, height: 34, fontSize: 10 }}>
                  {b.title.slice(0, 2).toUpperCase()}
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: "12px", fontWeight: 700 }}>{b.title}</div>
                  <div style={{ fontSize: "11px", color: "var(--muted)" }}>
                    {b.universeTitle} · {b.stage}
                  </div>
                </div>
              </button>
            ))}
            <div style={{ borderTop: "1px solid var(--line)", marginTop: "6px", paddingTop: "6px" }}>
              <button
                type="button"
                className="btn btn-sm"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => {
                  setDropdownOpen(false);
                  onChooseLibraryFolder();
                }}
              >
                Open Another Library Folder…
              </button>
            </div>
          </div>
        )}
      </div>

      <nav className="nav-scroll">
        <div className="nav-group">
          <div className="nav-group-header">
            <span>Manuscript</span>
            <button type="button" className="nav-add-btn" onClick={onCreateChapter}>
              + Chapter
            </button>
          </div>
          {book.chapters.map((ch, idx) => {
            const active = activeView === "chapter" && activeChapterRel === ch.relPath;
            return (
              <div key={ch.relPath} className="nav-item-row">
                <button
                  type="button"
                  className={`nav-item ${active ? "is-active" : ""}`}
                  onClick={() => onSelectView("chapter", ch.relPath)}
                >
                  <span className="nav-item-main">
                    <span className="nav-item-label">{ch.title}</span>
                  </span>
                  <span className="nav-item-meta">
                    <span>{ch.wordCount}w</span>
                    {ch.openComments > 0 && <span className="cmt-pill">{ch.openComments}</span>}
                  </span>
                </button>
                {active && book.chapters.length > 1 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
                    <button
                      type="button"
                      className="nav-add-btn"
                      style={{ fontSize: "9px", padding: "0 3px" }}
                      disabled={idx === 0}
                      onClick={() => onMoveChapter(idx, -1)}
                      title="Move chapter up"
                    >
                      ▲
                    </button>
                    <button
                      type="button"
                      className="nav-add-btn"
                      style={{ fontSize: "9px", padding: "0 3px" }}
                      disabled={idx === book.chapters.length - 1}
                      onClick={() => onMoveChapter(idx, 1)}
                      title="Move chapter down"
                    >
                      ▼
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="nav-group">
          <div className="nav-group-header">
            <span>Story Craft</span>
          </div>
          <button
            type="button"
            className={`nav-item ${activeView === "brief" ? "is-active" : ""}`}
            onClick={() => onSelectView("brief")}
          >
            <span className="nav-item-label">Book Brief</span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "scenes" ? "is-active" : ""}`}
            onClick={() => onSelectView("scenes")}
          >
            <span className="nav-item-label">Story Outline</span>
            <span className="nav-item-meta">{book.scenes.length}</span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "style" ? "is-active" : ""}`}
            onClick={() => onSelectView("style")}
          >
            <span className="nav-item-label">Style &amp; Voice</span>
          </button>
        </div>

        <div className="nav-group">
          <div className="nav-group-header">
            <span>World &amp; Lore</span>
          </div>
          <button
            type="button"
            className={`nav-item ${activeView === "characters" ? "is-active" : ""}`}
            onClick={() => onSelectView("characters")}
          >
            <span className="nav-item-label">Characters</span>
            <span className="nav-item-meta">{book.characters.length}</span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "bible" ? "is-active" : ""}`}
            onClick={() => onSelectView("bible")}
          >
            <span className="nav-item-label">World Bible &amp; Glossary</span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "canon" ? "is-active" : ""}`}
            onClick={() => onSelectView("canon")}
          >
            <span className="nav-item-label">World Rules &amp; Canon</span>
            <span className="nav-item-meta">
              {book.canon.length}
              {canonNotes > 0 && <span className="cmt-pill">{canonNotes}</span>}
            </span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "knowledge" ? "is-active" : ""}`}
            onClick={() => onSelectView("knowledge")}
          >
            <span className="nav-item-label">Who Knows What</span>
            <span className="nav-item-meta">{book.disclosures.length}</span>
          </button>
        </div>

        <div className="nav-group">
          <div className="nav-group-header">
            <span>Editorial &amp; Publishing</span>
          </div>
          <button
            type="button"
            className={`nav-item ${activeView === "gates" ? "is-active" : ""}`}
            onClick={() => onSelectView("gates")}
          >
            <span className="nav-item-label">Editorial Checkpoints</span>
            <span className="nav-item-meta">{book.issues.length || "clean"}</span>
          </button>
          <button
            type="button"
            className={`nav-item ${activeView === "publish" ? "is-active" : ""}`}
            onClick={() => onSelectView("publish")}
          >
            <span className="nav-item-label">Publish &amp; Audio</span>
            {book.hasNarrationConfig && <span className="nav-item-meta">audio</span>}
          </button>
          {book.isPublicEdition && book.publishedReaderUrl && (
            <button
              type="button"
              className="nav-item"
              onClick={() => onOpenExternalUrl(book.publishedReaderUrl!)}
              title={book.publishedReaderUrl}
            >
              <span className="nav-item-label">Open Published Book ↗</span>
              <span className="nav-item-meta">web</span>
            </button>
          )}
          {book.publishedLibraryUrl && (
            <button
              type="button"
              className="nav-item"
              onClick={() => onOpenExternalUrl(book.publishedLibraryUrl!)}
              title={book.publishedLibraryUrl}
            >
              <span className="nav-item-label">Open Public Library ↗</span>
              <span className="nav-item-meta">site</span>
            </button>
          )}
        </div>
      </nav>

      <div className="sidebar-footer">
        <span>
          {appUpdateStatus.currentVersion
            ? `Book Studio v${appUpdateStatus.currentVersion}`
            : "Draft history active"}
        </span>
        {appUpdateStatus.state === "downloaded" || appUpdateStatus.state === "available" ? (
          <button
            type="button"
            className="pill pill-gold"
            style={{ border: "none", cursor: "pointer" }}
            onClick={onOpenUpdatePanel}
          >
            Update ready
          </button>
        ) : (
          <span style={{ color: "var(--sage)", fontWeight: 600 }}>Ready</span>
        )}
      </div>
    </aside>
  );
};
