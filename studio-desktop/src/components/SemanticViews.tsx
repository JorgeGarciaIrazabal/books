import React, { useState } from "react";
import type { BookDetail, CharacterSheet, CommandResult } from "../../shared/types";
import type { PendingNoteTarget } from "./RightCompanion";
import type { AppView } from "./LeftNavigator";

interface SemanticViewsProps {
  book: BookDetail;
  view: Exclude<AppView, "chapter">;
  selectedCharId: string;
  activeCmtId: string | null;
  onSelectChar: (id: string) => void;
  onSaveTextFile: (fileRelPath: string, content: string) => void;
  onSaveCharacter: (
    charRelPath: string,
    fields: Pick<CharacterSheet, "role" | "want" | "limits" | "voice" | "sampleLine">
  ) => void;
  onStartRecordComment: (target: PendingNoteTarget) => void;
  onAcceptProposal: (proposalId: string) => void;
  onOpenChapter: (chapterRelPath: string) => void;
  onRunStudioCheck: () => Promise<CommandResult>;
  onRunBookBuild: () => Promise<CommandResult>;
  onRunCatalogValidate: () => Promise<CommandResult>;
  onOpenPublishModal: () => void;
  onRunAudioDoctor: () => Promise<CommandResult>;
  onRunAudioStep: (step: "prepare" | "pilot" | "render" | "verify") => Promise<CommandResult>;
}

export const SemanticViews: React.FC<SemanticViewsProps> = ({
  book,
  view,
  selectedCharId,
  activeCmtId,
  onSelectChar,
  onSaveTextFile,
  onSaveCharacter,
  onStartRecordComment,
  onAcceptProposal,
  onOpenChapter,
  onRunStudioCheck,
  onRunBookBuild,
  onRunCatalogValidate,
  onOpenPublishModal,
  onRunAudioDoctor,
  onRunAudioStep
}) => {
  const [audioEnabled, setAudioEnabled] = useState(book.hasNarrationConfig);
  const [statusLog, setStatusLog] = useState<CommandResult | null>(null);
  const [audioLog, setAudioLog] = useState<CommandResult | null>(null);
  const [busy, setBusy] = useState(false);

  const selectedChar =
    book.characters.find((c) => c.id === selectedCharId) || book.characters[0] || null;
  const [charFields, setCharFields] = useState({
    role: selectedChar?.role ?? "",
    want: selectedChar?.want ?? "",
    limits: selectedChar?.limits ?? ""
  });

  React.useEffect(() => {
    if (selectedChar) {
      setCharFields({
        role: selectedChar.role,
        want: selectedChar.want,
        limits: selectedChar.limits
      });
    }
  }, [selectedChar?.id]);

  if (view === "characters") {
    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">WORLD &amp; LORE · CHARACTER SHEETS</div>
              <h1 className="view-title">Cast &amp; Voice Profiles</h1>
            </div>
          </div>
          {book.characters.length === 0 ? (
            <div className="card" style={{ color: "var(--muted)" }}>
              No character profiles added to this universe yet.
            </div>
          ) : (
            <>
              <div className="grid-2" style={{ marginBottom: "20px" }}>
                {book.characters.map((c) => (
                  <div
                    key={c.id}
                    className={`card char-card ${selectedChar?.id === c.id ? "is-highlighted" : ""}`}
                    onClick={() => onSelectChar(c.id)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <strong>{c.name}</strong>
                      <span className={`pill ${c.status === "accepted" ? "pill-sage" : "pill-gold"}`}>{c.status}</span>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--accent)", fontWeight: 600, marginBottom: "4px" }}>
                      {c.subtitle}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                      {(c.role || c.voice).slice(0, 100)}
                    </div>
                  </div>
                ))}
              </div>

              {selectedChar && (
                <div className="card" style={{ padding: "18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
                    <div>
                      <span className="pill">{selectedChar.id}</span>
                      <h2 style={{ margin: "6px 0 2px", fontFamily: "var(--serif)" }}>
                        {selectedChar.name} {selectedChar.subtitle ? `— ${selectedChar.subtitle}` : ""}
                      </h2>
                    </div>
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={() =>
                        onStartRecordComment({
                          kind: "markdown",
                          file: selectedChar.relPath,
                          quote: `${selectedChar.name}: ${selectedChar.sampleLine || selectedChar.role.slice(0, 70)}`,
                          defaultRole: "@character_director",
                          defaultIntent: "critique"
                        })
                      }
                    >
                      + Add Note on Character
                    </button>
                  </div>

                  <div className="field-label">Role &amp; Agency</div>
                  <textarea
                    className="editable-box"
                    rows={2}
                    value={charFields.role}
                    onChange={(e) => {
                      const next = { ...charFields, role: e.target.value };
                      setCharFields(next);
                      onSaveCharacter(selectedChar.relPath, {
                        ...selectedChar,
                        ...next
                      });
                    }}
                  />
                  <div className="field-label">Desire / Want</div>
                  <textarea
                    className="editable-box"
                    rows={2}
                    value={charFields.want}
                    onChange={(e) => {
                      const next = { ...charFields, want: e.target.value };
                      setCharFields(next);
                      onSaveCharacter(selectedChar.relPath, {
                        ...selectedChar,
                        ...next
                      });
                    }}
                  />
                  <div className="field-label">Limits &amp; Rules</div>
                  <textarea
                    className="editable-box"
                    rows={2}
                    value={charFields.limits}
                    onChange={(e) => {
                      const next = { ...charFields, limits: e.target.value };
                      setCharFields(next);
                      onSaveCharacter(selectedChar.relPath, {
                        ...selectedChar,
                        ...next
                      });
                    }}
                  />
                  {selectedChar.voice && (
                    <>
                      <div className="field-label">Voice &amp; Sample Line</div>
                      <div className="editable-box">
                        {selectedChar.voice}
                        {selectedChar.sampleLine && (
                          <div style={{ marginTop: "6px", fontStyle: "italic" }}>{selectedChar.sampleLine}</div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  if (view === "canon") {
    const activeCmt = book.comments.find((c) => c.id === activeCmtId);
    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">WORLD CONTINUITY</div>
              <h1 className="view-title">World Rules &amp; Canon ({book.canon.length})</h1>
            </div>
          </div>
          {book.canon.map((f) => {
            const openCount = book.comments.filter(
              (c) => c.target.kind === "record" && c.target.recordId === f.id && c.status !== "resolved"
            ).length;
            const isHighlighted =
              activeCmt?.target.kind === "record" && activeCmt.target.recordId === f.id;
            return (
              <div key={f.id} className={`card ${isHighlighted ? "is-highlighted" : ""}`}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px", gap: "8px", flexWrap: "wrap" }}>
                  <div>
                    <span className="pill">{f.id}</span>
                    <strong style={{ marginLeft: "6px" }}>{f.title}</strong>
                  </div>
                  <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
                    {openCount > 0 && <span className="cmt-pill">{openCount} note(s)</span>}
                    <span className={`pill ${f.status === "accepted" ? "pill-sage" : "pill-gold"}`}>{f.status}</span>
                    <button
                      type="button"
                      className="btn btn-sm"
                      onClick={() =>
                        onStartRecordComment({
                          kind: "record",
                          file: f.sourceFile,
                          recordId: f.id,
                          recordTitle: f.title,
                          quote: f.text.slice(0, 90),
                          defaultRole: "@canon_keeper",
                          defaultIntent: "check-canon"
                        })
                      }
                    >
                      + Add Note
                    </button>
                    {f.isProposal && f.status !== "accepted" && (
                      <button
                        type="button"
                        className="btn btn-sm btn-sage"
                        onClick={() => onAcceptProposal(f.id)}
                      >
                        Accept into World Rules
                      </button>
                    )}
                  </div>
                </div>
                <p style={{ margin: 0, color: "var(--ink-soft)", lineHeight: 1.5 }}>{f.text}</p>
              </div>
            );
          })}
          {book.canon.length === 0 && (
            <div className="card" style={{ color: "var(--muted)" }}>
              No world rules recorded for this book yet.
            </div>
          )}
        </div>
      </div>
    );
  }

  if (view === "scenes") {
    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">STORY CRAFT</div>
              <h1 className="view-title">Story Outline &amp; Scene Beats</h1>
            </div>
          </div>
          {book.scenes.map((sc) => (
            <div key={sc.id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "6px" }}>
                <div>
                  <span className="pill">{sc.id}</span>
                  <strong style={{ marginLeft: "6px" }}>{sc.chapter}</strong>
                </div>
                <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                  {sc.pov && <span className="pill pill-role">POV: {sc.pov}</span>}
                  {sc.chapter && (
                    <button type="button" className="btn btn-sm" onClick={() => onOpenChapter(sc.chapter)}>
                      Open Chapter →
                    </button>
                  )}
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "10px" }}>
                <div className="editable-box">
                  <strong>Starting Situation:</strong>
                  <br />
                  {sc.incoming}
                </div>
                <div className="editable-box">
                  <strong>Turning Point:</strong>
                  <br />
                  {sc.turn}
                </div>
                <div className="editable-box">
                  <strong>Outcome:</strong>
                  <br />
                  {sc.outgoing}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (view === "knowledge") {
    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">READER &amp; CHARACTER DISCLOSURE</div>
              <h1 className="view-title">Who Knows What</h1>
            </div>
          </div>
          <div className="card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Secret or Fact</th>
                  <th>Known By Characters</th>
                  <th>Reader Learns</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {book.disclosures.map((d) => (
                  <tr key={d.id}>
                    <td><span className="pill">{d.id}</span></td>
                    <td><strong>{d.topic}</strong></td>
                    <td>{d.knownBy.join(", ")}</td>
                    <td><span className="pill pill-sage">{d.reader}</span></td>
                    <td style={{ color: "var(--muted)" }}>{d.note ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  if (view === "gates") {
    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">QUALITY CHECKPOINTS</div>
              <h1 className="view-title">Editorial Checkpoints</h1>
            </div>
          </div>
          <div className="grid-2" style={{ marginBottom: "18px" }}>
            {book.gates.map((g) => (
              <div key={g.id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
                  <strong>{g.checkpoint}</strong>
                  <span className={`pill ${g.status === "pass" ? "pill-sage" : "pill-gold"}`}>{g.status}</span>
                </div>
                <div style={{ fontSize: "11.5px", color: "var(--accent)", fontWeight: 600, marginBottom: "4px" }}>
                  {g.reviewer}
                </div>
                <div style={{ fontSize: "12.5px", color: "var(--ink-soft)" }}>{g.evidence}</div>
              </div>
            ))}
          </div>
          <h3 style={{ fontFamily: "var(--serif)", margin: "0 0 10px" }}>Open Findings ({book.issues.length})</h3>
          {book.issues.map((iss) => (
            <div key={iss.id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <span className="pill pill-rose">{iss.severity}</span>
                  <strong style={{ marginLeft: "6px" }}>{iss.location}</strong>
                </div>
                <span className="pill">{iss.status}</span>
              </div>
              <p style={{ margin: "6px 0 0", fontSize: "12.5px", color: "var(--ink-soft)" }}>{iss.evidence}</p>
            </div>
          ))}
          {book.issues.length === 0 && (
            <div className="card" style={{ color: "var(--sage)", fontWeight: 600 }}>
              No open blocking editorial findings.
            </div>
          )}
        </div>
      </div>
    );
  }

  if (view === "publish") {
    const runAction = async (fn: () => Promise<CommandResult>, setter: (r: CommandResult) => void) => {
      setBusy(true);
      try {
        const res = await fn();
        setter(res);
      } finally {
        setBusy(false);
      }
    };

    return (
      <div className="canvas-scroll">
        <div className="paper paper-wide">
          <div className="view-header">
            <div>
              <div className="chapter-eyebrow">PUBLISHING &amp; READ-ALOUD STUDIO</div>
              <h1 className="view-title">Publish &amp; Audio</h1>
            </div>
            <span className={`pill ${book.isPublicEdition ? "pill-sage" : "pill-gold"}`}>
              {book.isPublicEdition ? "Public Reader Edition" : "Private Draft"}
            </span>
          </div>

          <div className="card" style={{ padding: "16px", marginBottom: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
              <div>
                <strong style={{ fontSize: "15px" }}>Reading Copy &amp; Public Edition</strong>
                <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                  Publishing happens only when you explicitly request it. Margin notes never appear in reading copies.
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: statusLog ? "10px" : 0 }}>
              <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(onRunStudioCheck, setStatusLog)}>
                Check Book Readiness
              </button>
              <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(onRunBookBuild, setStatusLog)}>
                Prepare Reading Copy
              </button>
              <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(onRunCatalogValidate, setStatusLog)}>
                Verify Reader Package
              </button>
              <button type="button" className="btn btn-sm btn-primary" disabled={busy} onClick={onOpenPublishModal}>
                Publish to Readers…
              </button>
            </div>
            {statusLog && (
              <div className="editable-box" style={{ fontSize: "12px" }}>
                <strong style={{ color: statusLog.ok ? "var(--sage)" : "var(--rose)" }}>{statusLog.summary}</strong>
                {statusLog.details && <pre style={{ margin: "6px 0 0", whiteSpace: "pre-wrap", fontFamily: "var(--mono)", fontSize: "11px" }}>{statusLog.details}</pre>}
              </div>
            )}
          </div>

          <div className="card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", flexWrap: "wrap", gap: "8px" }}>
              <div>
                <strong style={{ fontSize: "15px" }}>Audio &amp; Read-Aloud (Optional)</strong>
                <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                  Builds narration in a separate audio layer using Fish Audio Drama 3 without altering your book text.
                </div>
              </div>
              <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12.5px", fontWeight: 600, cursor: "pointer" }}>
                <input type="checkbox" checked={audioEnabled} onChange={(e) => setAudioEnabled(e.target.checked)} />
                Build Audio for this Book
              </label>
            </div>

            {audioEnabled ? (
              <>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: audioLog ? "10px" : 0 }}>
                  <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(onRunAudioDoctor, setAudioLog)}>
                    Check Audio Studio
                  </button>
                  <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(() => onRunAudioStep("prepare"), setAudioLog)}>
                    1. Prepare Chapters
                  </button>
                  <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(() => onRunAudioStep("pilot"), setAudioLog)}>
                    2. Record Short Sample
                  </button>
                  <button type="button" className="btn btn-sm" disabled={busy} onClick={() => runAction(() => onRunAudioStep("render"), setAudioLog)}>
                    3. Record Full Audiobook
                  </button>
                  <button type="button" className="btn btn-sm btn-primary" disabled={busy} onClick={() => runAction(() => onRunAudioStep("verify"), setAudioLog)}>
                    4. Check Audio Quality
                  </button>
                </div>
                {audioLog && (
                  <div className="editable-box" style={{ fontSize: "12px" }}>
                    <strong style={{ color: audioLog.ok ? "var(--sage)" : "var(--rose)" }}>{audioLog.summary}</strong>
                    {audioLog.details && <pre style={{ margin: "6px 0 0", whiteSpace: "pre-wrap", fontFamily: "var(--mono)", fontSize: "11px" }}>{audioLog.details}</pre>}
                  </div>
                )}
              </>
            ) : (
              <div className="editable-box" style={{ color: "var(--muted)" }}>
                Audio narration is off for this draft. Check <strong>Build Audio for this Book</strong> above whenever you want to prepare and record read-aloud audio.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Brief / Style / Bible text documents
  const docConfig: Record<"brief" | "style" | "bible", { label: string; file: string; initial: string }> = {
    brief: { label: "Book Brief & Promise", file: "brief.md", initial: book.briefMarkdown },
    style: { label: "Style & Voice Guide", file: "style.md", initial: book.styleMarkdown },
    bible: { label: "World Bible & Glossary", file: "bible.md", initial: book.bibleMarkdown }
  };
  const cfg = docConfig[view as "brief" | "style" | "bible"];

  return (
    <div className="canvas-scroll">
      <div className="paper">
        <div className="chapter-eyebrow">STORY FOUNDATION</div>
        <h1 className="view-title" style={{ marginBottom: "14px" }}>{cfg.label}</h1>
        <textarea
          className="raw-md-pre"
          defaultValue={cfg.initial}
          onChange={(e) => onSaveTextFile(cfg.file, e.target.value)}
        />
      </div>
    </div>
  );
};
