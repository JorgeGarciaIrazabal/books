import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type { VersionEntry } from "../shared/types";
import { countWords } from "../shared/markdown";

function sha256(text: string): string {
  return crypto.createHash("sha256").update(text, "utf-8").digest("hex");
}

function safeKey(bookRelPath: string, fileRelPath: string): string {
  return Buffer.from(`${bookRelPath}::${fileRelPath}`, "utf-8").toString("base64url");
}

function historyDirFor(repoRoot: string, bookRelPath: string, fileRelPath: string): string {
  return path.join(repoRoot, ".studio-desktop", "history", safeKey(bookRelPath, fileRelPath));
}

function blobsDirFor(repoRoot: string): string {
  return path.join(repoRoot, ".studio-desktop", "blobs");
}

function atomicWriteSync(targetPath: string, content: string): void {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  const tmpPath = path.join(
    path.dirname(targetPath),
    `.tmp-${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );
  fs.writeFileSync(tmpPath, content, "utf-8");
  fs.renameSync(tmpPath, targetPath);
}

function formatNow(): string {
  const d = new Date();
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function computeDelta(oldText: string | null, newText: string): string {
  if (oldText === null) {
    return `+${countWords(newText)} words`;
  }
  const diff = countWords(newText) - countWords(oldText);
  if (diff === 0) return "Edited phrasing";
  return diff > 0 ? `+${diff} words` : `${diff} words`;
}

export function listVersions(
  repoRoot: string,
  bookRelPath: string,
  fileRelPath: string
): VersionEntry[] {
  const indexPath = path.join(historyDirFor(repoRoot, bookRelPath, fileRelPath), "versions.json");
  if (!fs.existsSync(indexPath)) return [];
  try {
    const raw = JSON.parse(fs.readFileSync(indexPath, "utf-8"));
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

export function readVersionBlob(repoRoot: string, hash: string): string | null {
  if (!/^[a-f0-9]{64}$/.test(hash)) return null;
  const blobPath = path.join(blobsDirFor(repoRoot), `${hash}.txt`);
  if (!fs.existsSync(blobPath)) return null;
  return fs.readFileSync(blobPath, "utf-8");
}

export function readVersionText(
  repoRoot: string,
  bookRelPath: string,
  fileRelPath: string,
  versionId: string
): string | null {
  const versions = listVersions(repoRoot, bookRelPath, fileRelPath);
  const found = versions.find((v) => v.id === versionId);
  if (!found) return null;
  return readVersionBlob(repoRoot, found.sha256);
}

export function ensureInitialSnapshot(
  repoRoot: string,
  bookRelPath: string,
  fileRelPath: string,
  currentContent: string
): VersionEntry[] {
  const existing = listVersions(repoRoot, bookRelPath, fileRelPath);
  if (existing.length > 0) return existing;
  return recordSnapshot(repoRoot, bookRelPath, fileRelPath, currentContent, {
    author: "You",
    role: "writer",
    summary: "Opened current draft",
    force: true
  });
}

export function recordSnapshot(
  repoRoot: string,
  bookRelPath: string,
  fileRelPath: string,
  content: string,
  opts: {
    author: string;
    role: "writer" | "external";
    summary: string;
    force?: boolean;
  }
): VersionEntry[] {
  const hash = sha256(content);
  const blobPath = path.join(blobsDirFor(repoRoot), `${hash}.txt`);
  if (!fs.existsSync(blobPath)) {
    atomicWriteSync(blobPath, content);
  }

  const versions = listVersions(repoRoot, bookRelPath, fileRelPath);
  const latest = versions[0];
  if (latest && latest.sha256 === hash && !opts.force) {
    return versions;
  }

  const oldText = latest ? readVersionBlob(repoRoot, latest.sha256) : null;
  const nextNum = latest ? latest.num + 1 : 1;
  const entry: VersionEntry = {
    id: `v${nextNum}`,
    num: nextNum,
    author: opts.author,
    role: opts.role,
    timestamp: formatNow(),
    summary: opts.summary,
    delta: computeDelta(oldText, content),
    sha256: hash
  };

  const next = [entry, ...versions].slice(0, 80);
  const indexPath = path.join(historyDirFor(repoRoot, bookRelPath, fileRelPath), "versions.json");
  atomicWriteSync(indexPath, JSON.stringify(next, null, 2) + "\n");
  return next;
}
