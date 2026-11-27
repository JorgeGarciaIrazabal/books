import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type {
  BookDetail,
  BookSummary,
  CanonRecord,
  ChapterContent,
  ChapterSummary,
  CharacterSheet,
  CommentRecord,
  DisclosureRecord,
  EditorialGate,
  EditorialIssue,
  SceneCard
} from "../shared/types";
import { countWords, splitChapterMarkdown } from "../shared/markdown";
import { reanchorMarkdownComment } from "../shared/anchors";
import {
  ensureInitialSnapshot,
  listVersions,
  readVersionBlob,
  recordSnapshot
} from "./history";

const RESERVED_TOP = new Set([
  "templates",
  "tools",
  "docs",
  "node_modules",
  "studio-desktop",
  "publications",
  "narration",
  "site",
  "_site",
  "tests"
]);

// SHA-256 hashes of files written by this app, used to prevent self-watcher echo loops.
const recentOwnWrites = new Map<string, number>();

export function markOwnWrite(absPath: string, hash: string): void {
  const key = `${path.resolve(absPath)}::${hash}`;
  recentOwnWrites.set(key, Date.now());
  for (const [k, ts] of recentOwnWrites.entries()) {
    if (Date.now() - ts > 15000) recentOwnWrites.delete(k);
  }
}

export function isOwnWrite(absPath: string, hash: string): boolean {
  const key = `${path.resolve(absPath)}::${hash}`;
  const ts = recentOwnWrites.get(key);
  if (!ts) return false;
  if (Date.now() - ts > 15000) {
    recentOwnWrites.delete(key);
    return false;
  }
  return true;
}

export function sha256Text(text: string): string {
  return crypto.createHash("sha256").update(text, "utf-8").digest("hex");
}

export function confinedPath(baseDir: string, relativePath: string): string {
  const resolvedBase = path.resolve(baseDir);
  const candidate = path.resolve(resolvedBase, relativePath);
  if (candidate !== resolvedBase && !candidate.startsWith(resolvedBase + path.sep)) {
    throw new Error(`Path escapes scope: ${relativePath}`);
  }
  return candidate;
}

export function atomicWriteFile(absPath: string, content: string): string {
  fs.mkdirSync(path.dirname(absPath), { recursive: true });
  const hash = sha256Text(content);
  markOwnWrite(absPath, hash);
  const tmpPath = path.join(
    path.dirname(absPath),
    `.studio-app-${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );
  fs.writeFileSync(tmpPath, content, "utf-8");
  fs.renameSync(tmpPath, absPath);
  return hash;
}

function safeReadText(filePath: string): string {
  try {
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return "";
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "";
  }
}

function safeReadJson<T>(filePath: string, fallback: T): T {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return fallback;
  }
}

function discoverBookDirs(repoRoot: string): string[] {
  const found: string[] = [];
  if (!fs.existsSync(repoRoot)) return found;

  for (const universeEntry of fs.readdirSync(repoRoot, { withFileTypes: true })) {
    if (!universeEntry.isDirectory()) continue;
    if (universeEntry.name.startsWith(".") || RESERVED_TOP.has(universeEntry.name)) continue;
    const uDir = path.join(repoRoot, universeEntry.name);
    if (!fs.existsSync(path.join(uDir, "universe.json"))) continue;

    for (const seriesEntry of fs.readdirSync(uDir, { withFileTypes: true })) {
      if (!seriesEntry.isDirectory() || seriesEntry.name.startsWith(".")) continue;
      const sDir = path.join(uDir, seriesEntry.name);
      if (!fs.existsSync(path.join(sDir, "series.json"))) continue;

      for (const bookEntry of fs.readdirSync(sDir, { withFileTypes: true })) {
        if (!bookEntry.isDirectory() || bookEntry.name.startsWith(".")) continue;
        const bDir = path.join(sDir, bookEntry.name);
        if (fs.existsSync(path.join(bDir, "book.json"))) {
          found.push(path.posix.join(universeEntry.name, seriesEntry.name, bookEntry.name));
        }
      }
    }
  }
  return found.sort();
}

function parseCharacterMarkdown(relPath: string, raw: string): CharacterSheet {
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  const heading = (lines.find((l) => l.startsWith("# ")) ?? "# Unnamed").slice(2).trim();
  const [namePart, ...restSub] = heading.split(",");
  const name = namePart.trim();
  const subtitle = restSub.join(",").trim();

  const idMatch = raw.match(/-\s*ID:\s*([A-Za-z0-9_-]+)/i);
  const statusMatch = raw.match(/-\s*Status:\s*([A-Za-z0-9_-]+)/i);
  const roleMatch = raw.match(/-\s*\*\*Role\*\*:\s*([^\n]+)/);
  const wantMatch = raw.match(/-\s*\*\*Want\*\*:\s*([^\n]+)/);
  const limitsMatch = raw.match(/-\s*\*\*Limits\*\*:\s*([^\n]+)/);

  let voice = "";
  let sampleLine = "";
  const voiceIdx = lines.findIndex((l) => /^##\s+Voice/i.test(l));
  if (voiceIdx >= 0) {
    const chunk: string[] = [];
    for (let i = voiceIdx + 1; i < lines.length; i++) {
      if (lines[i].startsWith("## ")) break;
      if (/^Sample line/i.test(lines[i])) {
        sampleLine = lines.slice(i + 1, i + 3).find((x) => x.trim())?.trim() ?? "";
        break;
      }
      if (lines[i].trim()) chunk.push(lines[i].trim());
    }
    voice = chunk.join(" ");
  }

  return {
    id: idMatch ? idMatch[1] : path.basename(relPath, ".md"),
    relPath,
    name,
    subtitle,
    status: statusMatch ? statusMatch[1] : "draft",
    role: roleMatch ? roleMatch[1].trim() : "",
    want: wantMatch ? wantMatch[1].trim() : "",
    limits: limitsMatch ? limitsMatch[1].trim() : "",
    voice,
    sampleLine,
    rawMarkdown: raw
  };
}

function loadCharacters(universeDir: string): CharacterSheet[] {
  const charsDir = path.join(universeDir, "characters");
  if (!fs.existsSync(charsDir)) return [];
  const sheets: CharacterSheet[] = [];
  for (const entry of fs.readdirSync(charsDir).sort()) {
    if (!entry.endsWith(".md") || entry === "README.md" || entry.startsWith("_")) continue;
    const full = path.join(charsDir, entry);
    const raw = safeReadText(full);
    if (!raw.trim()) continue;
    sheets.push(parseCharacterMarkdown(`characters/${entry}`, raw));
  }
  return sheets;
}

function loadComments(bookDir: string): CommentRecord[] {
  const cmtPath = path.join(bookDir, "reviews", "comments.json");
  const data = safeReadJson<{ schema_version?: number; comments?: CommentRecord[] }>(cmtPath, {
    schema_version: 1,
    comments: []
  });
  return Array.isArray(data.comments) ? data.comments : [];
}

export function scanLibrary(repoRoot: string): BookSummary[] {
  const dirs = discoverBookDirs(repoRoot);
  return dirs.map((relPath) => {
    const bookDir = confinedPath(repoRoot, relPath);
    const universeDir = path.dirname(path.dirname(bookDir));
    const seriesDir = path.dirname(bookDir);

    const bookJson = safeReadJson<Record<string, unknown>>(path.join(bookDir, "book.json"), {});
    const universeJson = safeReadJson<Record<string, unknown>>(path.join(universeDir, "universe.json"), {});
    const seriesJson = safeReadJson<Record<string, unknown>>(path.join(seriesDir, "series.json"), {});
    const chapters = Array.isArray(bookJson.chapters) ? bookJson.chapters : [];
    const chars = loadCharacters(universeDir);
    const comments = loadComments(bookDir);
    const openComments = comments.filter((c) => c.status !== "resolved" && c.status !== "dismissed").length;

    const bookId = String(bookJson.id ?? path.basename(bookDir));
    const pubCover = path.join(repoRoot, "publications", "covers", `${bookId}.jpg`);

    return {
      relPath,
      id: bookId,
      universe: String(bookJson.universe ?? path.basename(universeDir)),
      universeTitle: String(universeJson.title ?? path.basename(universeDir)),
      series: String(bookJson.series ?? path.basename(seriesDir)),
      seriesTitle: String(seriesJson.title ?? path.basename(seriesDir)),
      title: String(bookJson.title ?? bookId),
      kind: String(bookJson.kind ?? "fiction"),
      stage: String(bookJson.stage ?? "brief"),
      language: String(bookJson.language ?? "en"),
      chapterCount: chapters.length,
      characterCount: chars.length,
      openCommentCount: openComments,
      coverPath: fs.existsSync(pubCover) ? pubCover : null
    };
  });
}

export function loadBook(repoRoot: string, bookRelPath: string): BookDetail {
  const summary = scanLibrary(repoRoot).find((b) => b.relPath === bookRelPath);
  if (!summary) throw new Error(`Book not found: ${bookRelPath}`);

  const bookDir = confinedPath(repoRoot, bookRelPath);
  const universeDir = path.dirname(path.dirname(bookDir));
  const bookJson = safeReadJson<Record<string, unknown>>(path.join(bookDir, "book.json"), {});
  const chapterList = Array.isArray(bookJson.chapters)
    ? bookJson.chapters.filter((x): x is string => typeof x === "string")
    : [];

  const comments = loadComments(bookDir);

  const chapters: ChapterSummary[] = chapterList.map((chRel) => {
    const full = confinedPath(bookDir, chRel);
    const raw = safeReadText(full);
    const parsed = splitChapterMarkdown(raw);
    const open = comments.filter(
      (c) =>
        c.target.kind === "markdown" &&
        c.target.file === chRel &&
        c.status !== "resolved" &&
        c.status !== "dismissed"
    ).length;
    return {
      relPath: chRel,
      title: parsed.title || path.basename(chRel, ".md"),
      wordCount: countWords(parsed.bodyMarkdown),
      openComments: open,
      sha256: sha256Text(raw)
    };
  });

  const characters = loadCharacters(universeDir);

  const canonJson = safeReadJson<{ facts?: Array<Record<string, unknown>> }>(
    path.join(universeDir, "canon.json"),
    { facts: [] }
  );
  const proposalsJson = safeReadJson<{ proposals?: Array<Record<string, unknown>> }>(
    path.join(bookDir, "canon", "proposals.json"),
    { proposals: [] }
  );

  const canon: CanonRecord[] = [
    ...(canonJson.facts ?? []).map((f) => ({
      id: String(f.id ?? "FACT"),
      title: String(f.title ?? f.id ?? "World Fact"),
      text: String(f.fact ?? f.text ?? ""),
      status: String(f.status ?? "accepted"),
      scope: String(f.scope ?? summary.universe),
      sourceFile: "../../canon.json",
      provenance: f.provenance ? String(f.provenance) : undefined,
      storyTime: f.effective_story_time ? String(f.effective_story_time) : undefined,
      isProposal: false
    })),
    ...(proposalsJson.proposals ?? [])
      .filter((p) => String(p.status ?? "proposed") !== "accepted")
      .map((p) => ({
        id: String(p.id ?? "PROP"),
        title: String(p.title ?? p.id ?? "Proposed World Rule"),
        text: String(p.fact ?? p.text ?? ""),
        status: String(p.status ?? "proposed"),
        scope: String(p.scope ?? summary.universe),
        sourceFile: "canon/proposals.json",
        provenance: p.source_passage ? String(p.source_passage) : undefined,
        storyTime: p.story_time ? String(p.story_time) : undefined,
        isProposal: true
      }))
  ];

  const scenesJson = safeReadJson<{ scenes?: Array<Record<string, unknown>> }>(
    path.join(bookDir, "scenes.json"),
    { scenes: [] }
  );
  const scenes: SceneCard[] = (scenesJson.scenes ?? []).map((s) => ({
    id: String(s.id ?? "SC"),
    chapter: String(s.chapter ?? ""),
    pov: String(s.pov ?? ""),
    place: s.place ? String(s.place) : undefined,
    storyTime: s.story_time ? String(s.story_time) : undefined,
    incoming: String(s.incoming ?? s.incoming_state ?? ""),
    turn: String(s.turn ?? ""),
    outgoing: String(s.outgoing ?? s.outgoing_state ?? ""),
    status: s.status ? String(s.status) : undefined
  }));

  const knowJson = safeReadJson<{ disclosures?: Array<Record<string, unknown>> }>(
    path.join(bookDir, "knowledge.json"),
    { disclosures: [] }
  );
  const disclosures: DisclosureRecord[] = (knowJson.disclosures ?? []).map((d) => ({
    id: String(d.id ?? "KN"),
    topic: String(d.topic ?? d.subject ?? ""),
    knownBy: Array.isArray(d.known_by)
      ? d.known_by.map(String)
      : Array.isArray(d.learned_by)
        ? d.learned_by.map(String)
        : [],
    reader: String(d.reader ?? d.when ?? ""),
    when: d.when ? String(d.when) : undefined,
    note: d.note ? String(d.note) : undefined
  }));

  const gatesJson = safeReadJson<{ gates?: Array<Record<string, unknown>> }>(
    path.join(bookDir, "reviews", "gates.json"),
    { gates: [] }
  );
  const gates: EditorialGate[] = (gatesJson.gates ?? []).map((g) => ({
    id: String(g.id ?? "GATE"),
    checkpoint: String(g.checkpoint ?? ""),
    status: String(g.status ?? "pending"),
    reviewer: String(g.reviewer ?? ""),
    evidence: String(g.evidence ?? ""),
    openIssues: Array.isArray(g.open_issues) ? g.open_issues.map(String) : []
  }));

  const issuesJson = safeReadJson<{ issues?: Array<Record<string, unknown>> }>(
    path.join(bookDir, "reviews", "issues.json"),
    { issues: [] }
  );
  const issues: EditorialIssue[] = (issuesJson.issues ?? []).map((i) => ({
    id: String(i.id ?? "ISSUE"),
    severity: String(i.severity ?? "minor"),
    status: String(i.status ?? "open"),
    location: String(i.location ?? ""),
    evidence: String(i.evidence ?? ""),
    suggestion: String(i.suggestion ?? "")
  }));

  const pubManifest = safeReadJson<{ books?: Array<{ id?: string }> }>(
    path.join(repoRoot, "publications", "manifest.json"),
    { books: [] }
  );
  const isPublicEdition = Boolean(
    (pubManifest.books ?? []).some((item) => item.id === summary.id) ||
      fs.existsSync(path.join(repoRoot, "publications", `${summary.id}.epub`))
  );

  const hasNarrationConfig =
    Boolean(bookJson.narration) ||
    fs.existsSync(path.join(bookDir, "production", "narration", "script.md")) ||
    fs.existsSync(path.join(repoRoot, "site", "audio", summary.id));

  return {
    summary,
    chapters,
    characters,
    canon,
    scenes,
    disclosures,
    gates,
    issues,
    comments,
    briefMarkdown: safeReadText(path.join(bookDir, "brief.md")),
    styleMarkdown: safeReadText(path.join(bookDir, "style.md")),
    outlineMarkdown: safeReadText(path.join(bookDir, "outline.md")),
    bibleMarkdown: safeReadText(path.join(universeDir, "bible.md")),
    glossaryMarkdown: safeReadText(path.join(universeDir, "glossary.md")),
    isPublicEdition,
    hasNarrationConfig
  };
}

export function readChapter(
  repoRoot: string,
  bookRelPath: string,
  chapterRelPath: string
): ChapterContent {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const absPath = confinedPath(bookDir, chapterRelPath);
  const rawMarkdown = safeReadText(absPath);
  const parsed = splitChapterMarkdown(rawMarkdown);
  const versions = ensureInitialSnapshot(repoRoot, bookRelPath, chapterRelPath, rawMarkdown);

  return {
    relPath: chapterRelPath,
    title: parsed.title || path.basename(chapterRelPath, ".md"),
    bodyMarkdown: parsed.bodyMarkdown,
    rawMarkdown,
    blocks: parsed.blocks,
    sha256: sha256Text(rawMarkdown),
    wordCount: countWords(parsed.bodyMarkdown),
    versions
  };
}

export function saveChapter(
  repoRoot: string,
  bookRelPath: string,
  chapterRelPath: string,
  rawMarkdown: string,
  updatedComments?: CommentRecord[]
): { sha256: string; wordCount: number; versions: ReturnType<typeof listVersions> } {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const absPath = confinedPath(bookDir, chapterRelPath);
  const hash = atomicWriteFile(absPath, rawMarkdown);

  const existingVersions = listVersions(repoRoot, bookRelPath, chapterRelPath);
  let versions = existingVersions;
  // Record automatic snapshot if first save or >20 words changed since latest snapshot
  const latestBlob = existingVersions[0] ? readVersionBlob(repoRoot, existingVersions[0].sha256) : null;
  if (
    !latestBlob ||
    Math.abs(countWords(rawMarkdown) - countWords(latestBlob)) >= 20
  ) {
    versions = recordSnapshot(repoRoot, bookRelPath, chapterRelPath, rawMarkdown, {
      author: "You",
      role: "writer",
      summary: "Automatic draft checkpoint"
    });
  }

  if (updatedComments) {
    saveComments(repoRoot, bookRelPath, updatedComments);
  }

  const parsed = splitChapterMarkdown(rawMarkdown);
  return {
    sha256: hash,
    wordCount: countWords(parsed.bodyMarkdown),
    versions
  };
}

export function saveComments(
  repoRoot: string,
  bookRelPath: string,
  comments: CommentRecord[]
): void {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const cmtPath = confinedPath(bookDir, "reviews/comments.json");
  atomicWriteFile(
    cmtPath,
    JSON.stringify({ schema_version: 1, comments }, null, 2) + "\n"
  );
}

export function createChapter(
  repoRoot: string,
  bookRelPath: string,
  title: string
): { relPath: string } {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const bookJsonPath = path.join(bookDir, "book.json");
  const bookJson = safeReadJson<Record<string, unknown>>(bookJsonPath, {});
  const chapters = Array.isArray(bookJson.chapters)
    ? bookJson.chapters.filter((x): x is string => typeof x === "string")
    : [];

  const num = String(chapters.length + 1).padStart(3, "0");
  const slug =
    title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "new-chapter";
  let relPath = `manuscript/${num}-${slug}.md`;
  let counter = 2;
  while (fs.existsSync(confinedPath(bookDir, relPath))) {
    relPath = `manuscript/${num}-${slug}-${counter++}.md`;
  }

  atomicWriteFile(confinedPath(bookDir, relPath), `# ${title.trim() || "Untitled Chapter"}\n\n`);
  bookJson.chapters = [...chapters, relPath];
  atomicWriteFile(bookJsonPath, JSON.stringify(bookJson, null, 2) + "\n");
  return { relPath };
}

export function reorderChapters(
  repoRoot: string,
  bookRelPath: string,
  chapters: string[]
): void {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const bookJsonPath = path.join(bookDir, "book.json");
  const bookJson = safeReadJson<Record<string, unknown>>(bookJsonPath, {});
  bookJson.chapters = chapters;
  atomicWriteFile(bookJsonPath, JSON.stringify(bookJson, null, 2) + "\n");
}

export function saveBookTextFile(
  repoRoot: string,
  bookRelPath: string,
  fileRelPath: string,
  content: string
): void {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const universeDir = path.dirname(path.dirname(bookDir));
  const target =
    fileRelPath === "bible.md" || fileRelPath === "glossary.md"
      ? confinedPath(universeDir, fileRelPath)
      : confinedPath(bookDir, fileRelPath);
  atomicWriteFile(target, content);
}

export function saveCharacterSheet(
  repoRoot: string,
  bookRelPath: string,
  charRelPath: string,
  fields: Pick<CharacterSheet, "role" | "want" | "limits" | "voice" | "sampleLine">
): void {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const universeDir = path.dirname(path.dirname(bookDir));
  const absPath = confinedPath(universeDir, charRelPath);
  let raw = safeReadText(absPath);
  if (!raw) return;

  const replaceBullet = (src: string, label: string, val: string) => {
    const re = new RegExp(`(-\\s*\\*\\*${label}\\*\\*:\\s*)([^\\n]*)`);
    return re.test(src) ? src.replace(re, `$1${val}`) : src;
  };
  raw = replaceBullet(raw, "Role", fields.role);
  raw = replaceBullet(raw, "Want", fields.want);
  raw = replaceBullet(raw, "Limits", fields.limits);
  atomicWriteFile(absPath, raw);
}

export function acceptCanonProposal(
  repoRoot: string,
  bookRelPath: string,
  proposalId: string
): CanonRecord[] {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const universeDir = path.dirname(path.dirname(bookDir));
  const propPath = path.join(bookDir, "canon", "proposals.json");
  const canonPath = path.join(universeDir, "canon.json");
  const uniPath = path.join(universeDir, "universe.json");

  const propData = safeReadJson<{ schema_version: number; proposals: Array<Record<string, unknown>> }>(
    propPath,
    { schema_version: 1, proposals: [] }
  );
  const canonData = safeReadJson<{ schema_version: number; facts: Array<Record<string, unknown>> }>(
    canonPath,
    { schema_version: 1, facts: [] }
  );
  const uniData = safeReadJson<Record<string, unknown>>(uniPath, {});

  const prop = propData.proposals.find((p) => p.id === proposalId);
  if (prop && prop.status !== "accepted") {
    prop.status = "accepted";
    const nextNum = String((canonData.facts?.length ?? 0) + 1).padStart(4, "0");
    canonData.facts.push({
      id: `FACT-${nextNum}`,
      ...(prop.title ? { title: prop.title } : {}),
      scope: prop.scope ?? path.basename(universeDir),
      status: "accepted",
      fact: prop.fact ?? prop.text ?? "",
      provenance: `Promoted from ${proposalId}`,
      effective_story_time: prop.story_time ?? "Book scope"
    });
    const curRev = Number(uniData.canon_revision ?? 0);
    uniData.canon_revision = curRev + 1;
    atomicWriteFile(propPath, JSON.stringify(propData, null, 2) + "\n");
    atomicWriteFile(canonPath, JSON.stringify(canonData, null, 2) + "\n");
    atomicWriteFile(uniPath, JSON.stringify(uniData, null, 2) + "\n");
  }

  return loadBook(repoRoot, bookRelPath).canon;
}

/**
 * Re-anchors all chapter comments after an external disk edit (e.g. from Antigravity).
 */
export function handleExternalChapterUpdate(
  repoRoot: string,
  bookRelPath: string,
  chapterRelPath: string
): { updatedCount: number } {
  const bookDir = confinedPath(repoRoot, bookRelPath);
  const absPath = confinedPath(bookDir, chapterRelPath);
  const newMarkdown = safeReadText(absPath);
  const newHash = sha256Text(newMarkdown);

  const versions = listVersions(repoRoot, bookRelPath, chapterRelPath);
  const prevText = versions[0] ? readVersionBlob(repoRoot, versions[0].sha256) : null;

  recordSnapshot(repoRoot, bookRelPath, chapterRelPath, newMarkdown, {
    author: "External update",
    role: "external",
    summary: "Updated on disk outside editor"
  });

  const comments = loadComments(bookDir);
  let updatedCount = 0;
  const nextComments = comments.map((c) => {
    if (c.target.kind === "markdown" && c.target.file === chapterRelPath) {
      const updated = reanchorMarkdownComment(c, prevText, newMarkdown, newHash);
      if (
        updated.anchor.startOffset !== c.anchor.startOffset ||
        updated.anchor.quote !== c.anchor.quote ||
        updated.anchor.orphaned !== c.anchor.orphaned
      ) {
        updatedCount++;
      }
      return updated;
    }
    return c;
  });

  if (updatedCount > 0) {
    saveComments(repoRoot, bookRelPath, nextComments);
  }
  return { updatedCount };
}
