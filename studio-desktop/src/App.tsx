import React, { useEffect, useState } from "react";
import type {
  BackupStatus,
  BookDetail,
  BookSummary,
  ChapterContent,
  CommentRecord
} from "../shared/types";
import { getStudioApi } from "./api";
import { splitChapterMarkdown } from "../shared/markdown";
import { LeftNavigator, type AppView } from "./components/LeftNavigator";
import { ProseEditor, type DraftSelectionAnchor } from "./components/ProseEditor";
import { RightCompanion, type PendingNoteTarget, type RailTab } from "./components/RightCompanion";
import { SemanticViews } from "./components/SemanticViews";
import { PublishModal, QuickJumpModal, SaveMilestoneModal } from "./components/Modals";

const api = getStudioApi();

const THEMES = [
  { id: "warm", label: "Warm Paper" },
  { id: "light", label: "Crisp Light" },
  { id: "dark", label: "Evening Ink" }
];

const VIEW_LABELS: Record<AppView, string> = {
  chapter: "Manuscript",
  brief: "Book Brief",
  scenes: "Story Outline",
  style: "Style & Voice",
  characters: "Characters",
  bible: "World Bible",
  canon: "World Rules",
  knowledge: "Who Knows What",
  gates: "Checkpoints",
  publish: "Publish & Audio"
};

export const App: React.FC = () => {
  const [books, setBooks] = useState<BookSummary[]>([]);
  const [book, setBook] = useState<BookDetail | null>(null);
  const [chapter, setChapter] = useState<ChapterContent | null>(null);
  const [activeView, setActiveView] = useState<AppView>("chapter");
  const [diffMode, setDiffMode] = useState<"clean" | "inline" | "sidebyside">("clean");
  const [plainTextMode, setPlainTextMode] = useState(false);
  const [baselineVersionId, setBaselineVersionId] = useState("");
  const [baselineText, setBaselineText] = useState("");

  const [railTab, setRailTab] = useState<RailTab>("notes");
  const [activeCmtId, setActiveCmtId] = useState<string | null>(null);
  const [pendingTarget, setPendingTarget] = useState<PendingNoteTarget | null>(null);
  const [selectedCharId, setSelectedCharId] = useState("");

  const [splitRefOpen, setSplitRefOpen] = useState(false);
  const [splitRefKey, setSplitRefKey] = useState("");
  const [focusMode, setFocusMode] = useState(false);
  const [themeIdx, setThemeIdx] = useState(0);

  const [quickJumpOpen, setQuickJumpOpen] = useState(false);
  const [milestoneOpen, setMilestoneOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);

  const [externalBanner, setExternalBanner] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [backupStatus, setBackupStatus] = useState<BackupStatus>({
    state: "saved",
    message: "All changes saved",
    ahead: 0,
    behind: 0,
    lastBackupTime: "Just now",
    branch: "main",
    isPublicOrigin: false,
    autoIntervalMinutes: 2,
    privacyMode: "private-auto",
    recentEvents: []
  });

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast((cur) => (cur === msg ? null : cur)), 3000);
  };

  const loadBookAndFirstChapter = async (bookRelPath: string) => {
    const detail = await api.loadBook(bookRelPath);
    setBook(detail);
    setSelectedCharId(detail.characters[0]?.id ?? "");
    setSplitRefKey(detail.characters[0]?.id ?? "BRIEF");
    if (detail.chapters.length > 0) {
      const ch = await api.readChapter(bookRelPath, detail.chapters[0].relPath);
      setChapter(ch);
      const baseVer = ch.versions[1]?.id ?? ch.versions[0]?.id ?? "";
      setBaselineVersionId(baseVer);
      if (baseVer) {
        const txt = await api.readVersionText(bookRelPath, ch.relPath, baseVer);
        setBaselineText(txt);
      }
      setActiveView("chapter");
    } else {
      setChapter(null);
      setActiveView("brief");
    }
    setDiffMode("clean");
    setExternalBanner(null);
  };

  const initLibrary = async () => {
    const list = await api.scanLibrary();
    setBooks(list);
    const status = await api.getBackupStatus();
    setBackupStatus(status);
    if (list.length > 0) {
      const preferred =
        list.find((b) => b.id === "the-hot-potato-of-corporate-castle") ?? list[0];
      await loadBookAndFirstChapter(preferred.relPath);
    }
  };

  useEffect(() => {
    void initLibrary();
    const unsubExt = api.onExternalChange((ev) => {
      setBook((curBook) => {
        if (!curBook || curBook.summary.relPath !== ev.bookRelPath) return curBook;
        void api.loadBook(ev.bookRelPath).then((refreshed) => {
          setBook(refreshed);
        });
        setChapter((curChap) => {
          if (curChap && ev.kind === "chapter" && curChap.relPath === ev.fileRelPath) {
            void api.readChapter(ev.bookRelPath, ev.fileRelPath).then((freshChap) => {
              setChapter(freshChap);
              setExternalBanner(ev.message);
            });
          }
          return curChap;
        });
        return curBook;
      });
    });
    const unsubBackup = api.onBackupStatus((st) => {
      setBackupStatus(st);
    });
    return () => {
      unsubExt();
      unsubBackup();
    };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setQuickJumpOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", THEMES[themeIdx].id);
  }, [themeIdx]);

  useEffect(() => {
    if (!book || !chapter || !baselineVersionId) return;
    void api
      .readVersionText(book.summary.relPath, chapter.relPath, baselineVersionId)
      .then((txt) => setBaselineText(txt || chapter.rawMarkdown));
  }, [baselineVersionId, book?.summary.relPath, chapter?.relPath]);

  if (!book) {
    return (
      <div style={{ padding: "48px", fontFamily: "var(--serif)", textAlign: "center" }}>
        <h2>Book Studio</h2>
        <p style={{ color: "var(--muted)" }}>Loading your books…</p>
        <button
          type="button"
          className="btn btn-primary"
          onClick={async () => {
            const folder = await api.chooseRepoFolder();
            if (folder) await initLibrary();
          }}
        >
          Choose Book Studio Library Folder…
        </button>
      </div>
    );
  }

  const openNoteCount = book.comments.filter(
    (c) => c.status !== "resolved" && c.status !== "dismissed"
  ).length;

  const handleOpenChapter = async (chapterRel: string) => {
    const ch = await api.readChapter(book.summary.relPath, chapterRel);
    setChapter(ch);
    const baseVer = ch.versions[1]?.id ?? ch.versions[0]?.id ?? "";
    setBaselineVersionId(baseVer);
    setActiveView("chapter");
    setDiffMode("clean");
    setExternalBanner(null);
  };

  const handleSaveChapter = async (rawMarkdown: string, updatedComments?: CommentRecord[]) => {
    if (!chapter) return;
    setBackupStatus((s) => ({ ...s, state: "saving", message: "Saving…" }));
    const res = await api.saveChapter(
      book.summary.relPath,
      chapter.relPath,
      rawMarkdown,
      updatedComments
    );
    const parsed = splitChapterMarkdown(rawMarkdown);
    setChapter((prev) =>
      prev
        ? {
            ...prev,
            title: parsed.title || prev.title,
            bodyMarkdown: parsed.bodyMarkdown,
            blocks: parsed.blocks,
            rawMarkdown,
            sha256: res.sha256,
            wordCount: res.wordCount,
            versions: res.versions
          }
        : prev
    );
    setBook((prev) => {
      if (!prev) return prev;
      const nextChapters = prev.chapters.map((c) =>
        c.relPath === chapter.relPath
          ? {
              ...c,
              title: parsed.title || c.title,
              wordCount: res.wordCount,
              sha256: res.sha256
            }
          : c
      );
      return {
        ...prev,
        chapters: nextChapters,
        ...(updatedComments ? { comments: updatedComments } : {})
      };
    });
  };

  const handleCopyForAssistant = async () => {
    const open = book.comments.filter((c) => c.status === "open");
    const msCount = open.filter((c) => c.target.kind === "markdown").length;
    const canonCount = open.filter((c) => c.target.kind === "record").length;
    const ids = open.map((c) => c.id).join(", ") || "none";
    const prompt = `Use the address-comments skill on ${book.summary.relPath} ("${book.summary.title}") to address open notes in reviews/comments.json (${msCount} manuscript, ${canonCount} world rules): ${ids}.`;
    await api.copyToClipboard(prompt);
    showToast(`Copied prompt for assistant (${open.length} open note${open.length === 1 ? "" : "s"})`);
  };

  const splitChar = book.characters.find((c) => c.id === splitRefKey);
  const splitRule = book.canon.find((f) => f.id === splitRefKey);

  return (
    <div className={`app ${focusMode ? "is-focus" : ""}`}>
      <header className="topbar">
        <div className="topbar-left">
          <div className="brand">
            <span className="brand-mark">B</span>
            <span>Book Studio</span>
          </div>
          <div className="breadcrumbs">
            <button type="button" className="crumb-btn" onClick={() => setActiveView("brief")}>
              {book.summary.universeTitle}
            </button>
            <span>›</span>
            <button type="button" className="crumb-btn" onClick={() => setActiveView("brief")}>
              {book.summary.title}
            </button>
            <span>›</span>
            <span className="crumb-current">
              {activeView === "chapter" && chapter ? chapter.title : VIEW_LABELS[activeView]}
            </span>
          </div>
          <button
            type="button"
            className={`sync-pill ${backupStatus.state === "saving" ? "is-saving" : backupStatus.state === "updated" ? "is-updated" : ""}`}
            onClick={() => setRailTab("backups")}
            title="View saving & automatic backup settings"
          >
            <span className="sync-dot" />
            <span>{backupStatus.message}</span>
          </button>
        </div>

        <div>
          <button type="button" className="cmd-trigger" onClick={() => setQuickJumpOpen(true)}>
            <span>Jump to chapter, character…</span>
            <span className="kbd">Ctrl K</span>
          </button>
        </div>

        <div className="topbar-right">
          {activeView === "chapter" && (
            <button
              type="button"
              className={`btn ${plainTextMode ? "is-active" : ""}`}
              onClick={() => setPlainTextMode((v) => !v)}
            >
              Plain Text
            </button>
          )}
          <button
            type="button"
            className={`btn ${splitRefOpen ? "is-active" : ""}`}
            onClick={() => setSplitRefOpen((v) => !v)}
          >
            Split Ref
          </button>
          <button
            type="button"
            className={`btn ${focusMode ? "is-active" : ""}`}
            onClick={() => setFocusMode((v) => !v)}
          >
            Focus
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => setThemeIdx((i) => (i + 1) % THEMES.length)}
          >
            {THEMES[themeIdx].label}
          </button>
          <button type="button" className="btn btn-primary" onClick={handleCopyForAssistant}>
            <span>Copy Notes for Assistant</span>
            <span className="badge-count">{openNoteCount}</span>
          </button>
        </div>
      </header>

      <div className="workspace">
        <LeftNavigator
          books={books}
          book={book}
          activeView={activeView}
          activeChapterRel={chapter?.relPath ?? ""}
          onSelectBook={(rel) => void loadBookAndFirstChapter(rel)}
          onChooseLibraryFolder={async () => {
            const folder = await api.chooseRepoFolder();
            if (folder) await initLibrary();
          }}
          onSelectView={(view, chRel) => {
            if (view === "chapter" && chRel) {
              void handleOpenChapter(chRel);
            } else {
              setActiveView(view);
            }
          }}
          onCreateChapter={async () => {
            const { relPath } = await api.createChapter(
              book.summary.relPath,
              `Chapter ${book.chapters.length + 1}`
            );
            const refreshed = await api.loadBook(book.summary.relPath);
            setBook(refreshed);
            await handleOpenChapter(relPath);
            showToast("Added new chapter to your book");
          }}
          onMoveChapter={async (index, dir) => {
            const list = book.chapters.map((c) => c.relPath);
            const target = index + dir;
            if (target < 0 || target >= list.length) return;
            [list[index], list[target]] = [list[target], list[index]];
            await api.reorderChapters(book.summary.relPath, list);
            const refreshed = await api.loadBook(book.summary.relPath);
            setBook(refreshed);
          }}
        />

        <main className="center-stage">
          <div className="center-body" style={{ flexDirection: "column" }}>
            {activeView === "chapter" && chapter ? (
              <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
                <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
                  <ProseEditor
                    chapter={chapter}
                    comments={book.comments}
                    activeCmtId={activeCmtId}
                    diffMode={diffMode}
                    plainTextMode={plainTextMode}
                    baselineVersionId={baselineVersionId}
                    baselineText={baselineText}
                    externalBanner={externalBanner}
                    onDismissBanner={() => setExternalBanner(null)}
                    onChangeDiffMode={(m) => {
                      setPlainTextMode(false);
                      setDiffMode(m);
                    }}
                    onSelectBaseline={setBaselineVersionId}
                    onOpenVersions={() => setRailTab("versions")}
                    onOpenSaveMilestone={() => setMilestoneOpen(true)}
                    onSaveChapter={(md, nextCmts) => void handleSaveChapter(md, nextCmts)}
                    onSelectComment={(id) => {
                      setActiveCmtId(id);
                      setRailTab("notes");
                    }}
                    onStartCommentFromSelection={(sel: DraftSelectionAnchor, defaultRole, defaultIntent) => {
                      setPendingTarget({
                        kind: "markdown",
                        file: chapter.relPath,
                        blockIndex: sel.blockIndex,
                        startOffset: sel.startOffset,
                        endOffset: sel.endOffset,
                        quote: sel.quote,
                        prefix: sel.prefix,
                        suffix: sel.suffix,
                        occurrence: sel.occurrence,
                        totalOccurrences: sel.totalOccurrences,
                        defaultRole,
                        defaultIntent
                      });
                      setRailTab("notes");
                    }}
                  />
                </div>

                {splitRefOpen && (
                  <aside className="split-pane">
                    <div className="split-pane-header">
                      <select
                        className="baseline-select"
                        style={{ flex: 1 }}
                        value={splitRefKey}
                        onChange={(e) => setSplitRefKey(e.target.value)}
                      >
                        {book.characters.map((c) => (
                          <option key={c.id} value={c.id}>
                            Character: {c.name}
                          </option>
                        ))}
                        {book.canon.map((f) => (
                          <option key={f.id} value={f.id}>
                            Rule: {f.title}
                          </option>
                        ))}
                        <option value="BRIEF">Book Brief</option>
                      </select>
                      <button type="button" className="btn btn-sm" onClick={() => setSplitRefOpen(false)}>
                        Close
                      </button>
                    </div>
                    <div className="split-pane-body">
                      {splitChar ? (
                        <>
                          <span className="pill">{splitChar.id}</span>
                          <h3 style={{ fontFamily: "var(--serif)", margin: "6px 0 4px" }}>{splitChar.name}</h3>
                          <p><strong>Role:</strong> {splitChar.role}</p>
                          <p><strong>Want:</strong> {splitChar.want}</p>
                          <p><strong>Voice:</strong> {splitChar.voice}</p>
                        </>
                      ) : splitRule ? (
                        <>
                          <span className="pill">{splitRule.id}</span>
                          <h3 style={{ fontFamily: "var(--serif)", margin: "6px 0 6px" }}>{splitRule.title}</h3>
                          <p>{splitRule.text}</p>
                        </>
                      ) : (
                        <>
                          <h3 style={{ fontFamily: "var(--serif)", margin: "0 0 8px" }}>Book Brief</h3>
                          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "var(--sans)", margin: 0 }}>
                            {book.briefMarkdown}
                          </pre>
                        </>
                      )}
                    </div>
                  </aside>
                )}
              </div>
            ) : (
              <SemanticViews
                book={book}
                view={activeView === "chapter" ? "brief" : activeView}
                selectedCharId={selectedCharId}
                activeCmtId={activeCmtId}
                onSelectChar={setSelectedCharId}
                onSaveTextFile={(rel, content) =>
                  void api.saveBookTextFile(book.summary.relPath, rel, content)
                }
                onSaveCharacter={(rel, fields) => {
                  setBook((prev) =>
                    prev
                      ? {
                          ...prev,
                          characters: prev.characters.map((ch) =>
                            ch.relPath === rel ? { ...ch, ...fields } : ch
                          )
                        }
                      : prev
                  );
                  void api.saveCharacterSheet(book.summary.relPath, rel, fields);
                }}
                onStartRecordComment={(target) => {
                  setPendingTarget(target);
                  setRailTab("notes");
                }}
                onAcceptProposal={async (propId) => {
                  const nextCanon = await api.acceptCanonProposal(
                    book.summary.relPath,
                    propId
                  );
                  setBook((prev) => (prev ? { ...prev, canon: nextCanon } : prev));
                  showToast("Accepted rule into your universe canon");
                }}
                onOpenChapter={(chRel) => void handleOpenChapter(chRel)}
                onRunStudioCheck={() => api.runStudioCheck(book.summary.relPath)}
                onRunBookBuild={() => api.runBookBuild(book.summary.relPath)}
                onRunCatalogValidate={() => api.runCatalogValidate()}
                onOpenPublishModal={() => setPublishOpen(true)}
                onRunAudioDoctor={() => api.runAudioDoctor()}
                onRunAudioStep={(step) => api.runAudioStep(book.summary.relPath, step)}
              />
            )}
          </div>
        </main>

        <RightCompanion
          book={book}
          activeChapter={chapter}
          railTab={railTab}
          activeCmtId={activeCmtId}
          baselineVersionId={baselineVersionId}
          pendingTarget={pendingTarget}
          backupStatus={backupStatus}
          onChangeTab={setRailTab}
          onAddComment={async (cmt) => {
            const next = [cmt, ...book.comments];
            await api.saveComments(book.summary.relPath, next);
            setBook({ ...book, comments: next });
            setPendingTarget(null);
            setActiveCmtId(cmt.id);
            showToast(`Saved note ${cmt.id}`);
          }}
          onResolveComment={async (cmtId) => {
            const next = book.comments.map((c) =>
              c.id === cmtId ? { ...c, status: "resolved" } : c
            );
            await api.saveComments(book.summary.relPath, next);
            setBook({ ...book, comments: next });
          }}
          onClickComment={(c) => {
            setActiveCmtId(c.id);
            if (c.target.kind === "record") {
              setActiveView("canon");
            } else if (c.target.file.startsWith("manuscript/")) {
              if (chapter?.relPath !== c.target.file) {
                void handleOpenChapter(c.target.file);
              } else {
                setActiveView("chapter");
                setDiffMode("clean");
              }
            }
          }}
          onCompareVersion={(vId, mode) => {
            setBaselineVersionId(vId);
            setPlainTextMode(false);
            setDiffMode(mode);
            setActiveView("chapter");
          }}
          onRestoreVersion={async (vId) => {
            if (!chapter) return;
            const restored = await api.restoreVersion(
              book.summary.relPath,
              chapter.relPath,
              vId
            );
            setChapter(restored);
            setDiffMode("clean");
            showToast(`Restored ${vId} as a new draft`);
          }}
          onOpenSaveMilestone={() => setMilestoneOpen(true)}
          onPinSplitRef={(key) => {
            setSplitRefKey(key);
            setSplitRefOpen(true);
          }}
          onChangeBackupSettings={async (settings) => {
            const st = await api.setBackupSettings(settings);
            setBackupStatus(st);
          }}
          onBackupNow={async (mode) => {
            const st = await api.runBackupNow(mode);
            setBackupStatus(st);
            showToast(st.message);
          }}
          onCopyForAssistant={() => void handleCopyForAssistant()}
        />
      </div>

      <QuickJumpModal
        open={quickJumpOpen}
        book={book}
        onClose={() => setQuickJumpOpen(false)}
        onOpenChapter={(rel) => void handleOpenChapter(rel)}
        onOpenCharacter={(cid) => {
          setSelectedCharId(cid);
          setActiveView("characters");
        }}
        onOpenCanon={() => setActiveView("canon")}
        onChangeDiffMode={(m) => {
          setActiveView("chapter");
          setDiffMode(m);
        }}
        onToggleFocus={() => setFocusMode((v) => !v)}
      />

      <SaveMilestoneModal
        open={milestoneOpen}
        onClose={() => setMilestoneOpen(false)}
        onConfirm={async (label, alsoBackup) => {
          if (!chapter) return;
          const nextVers = await api.saveNamedMilestone(
            book.summary.relPath,
            chapter.relPath,
            label,
            alsoBackup
          );
          setChapter({ ...chapter, versions: nextVers });
          showToast(`Saved milestone: ${label}`);
        }}
      />

      <PublishModal
        open={publishOpen}
        book={book}
        onClose={() => setPublishOpen(false)}
        onConfirm={async (includeAudio) => {
          const res = await api.runPublishRelease(book.summary.relPath, includeAudio);
          showToast(res.summary);
        }}
      />

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
};
