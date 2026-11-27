import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import chokidar, { type FSWatcher } from "chokidar";
import type { BackupStatus, CommentRecord, ExternalChangeEvent } from "../shared/types";
import { readVersionText, recordSnapshot } from "./history";
import {
  acceptCanonProposal,
  atomicWriteFile,
  confinedPath,
  createChapter,
  handleExternalChapterUpdate,
  isOwnWrite,
  loadBook,
  readChapter,
  reorderChapters,
  saveBookTextFile,
  saveChapter,
  saveCharacterSheet,
  saveComments,
  scanLibrary,
  sha256Text
} from "./repo";
import {
  inspectGitBackupState,
  runAudioDoctor,
  runAudioStep,
  runBackupSync,
  runBookBuild,
  runCatalogValidate,
  runPublishRelease,
  runStudioCheck
} from "./studioTools";

function readArg(flag: string): string | null {
  const idx = process.argv.indexOf(flag);
  return idx >= 0 && process.argv[idx + 1] ? process.argv[idx + 1] : null;
}

function resolveInitialRoot(): string {
  const arg = readArg("--library");
  if (arg) return path.resolve(arg);
  if (process.env.BOOK_STUDIO_LIBRARY) return path.resolve(process.env.BOOK_STUDIO_LIBRARY);
  const candidates = [
    path.resolve(process.cwd(), ".."),
    process.cwd(),
    path.resolve(__dirname, "..", "..", ".."),
    path.join(os.homedir(), "code", "books")
  ];
  for (const d of candidates) {
    if (fs.existsSync(path.join(d, "AGENTS.md"))) return d;
  }
  return candidates[0];
}

const port = Number(readArg("--port") ?? 4173);
const distDir = path.resolve(__dirname, "..", "..", "dist");
let repoRoot = resolveInitialRoot();
let autoIntervalMinutes = 2;
let privacyMode: "private-auto" | "public-pull-only" = "private-auto";
let lastClipboardText = "";

const recentEvents: BackupStatus["recentEvents"] = [
  {
    id: "init-1",
    source: "Library Ready",
    time: "Just now",
    summary: "Connected to your Book Studio folder with automatic change tracking."
  }
];

const sseClients = new Set<http.ServerResponse>();

function broadcastSse(eventName: string, payload: unknown) {
  const data = `event: ${eventName}\ndata: ${JSON.stringify(payload)}\n\n`;
  for (const res of sseClients) {
    res.write(data);
  }
}

function pushBackupEvent(source: string, summary: string) {
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  recentEvents.unshift({ id: `ev-${Date.now()}`, source, time, summary });
  if (recentEvents.length > 20) recentEvents.pop();
}

async function emitBackupStatus(override?: Partial<BackupStatus>): Promise<BackupStatus> {
  const base = await inspectGitBackupState(repoRoot, autoIntervalMinutes, privacyMode, recentEvents);
  const full: BackupStatus = { ...base, ...override };
  broadcastSse("backup-status", full);
  return full;
}

let watcher: FSWatcher | null = null;
function startWatcher() {
  if (watcher) void watcher.close();
  watcher = chokidar.watch(repoRoot, {
    ignored: [/(^|[/\\])\../, /node_modules/, /studio-desktop/, /_site/, /\/exports\//],
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 150, pollInterval: 40 }
  });
  watcher.on("change", (absPath) => {
    if (!absPath.endsWith(".md") && !absPath.endsWith(".json")) return;
    let content = "";
    try {
      content = fs.readFileSync(absPath, "utf-8");
    } catch {
      return;
    }
    const hash = sha256Text(content);
    if (isOwnWrite(absPath, hash)) return;

    const rel = path.relative(repoRoot, absPath).split(path.sep).join("/");
    const parts = rel.split("/");
    if (parts.length < 4) return;
    const bookRelPath = parts.slice(0, 3).join("/");
    const fileRelPath = parts.slice(3).join("/");

    let payload: ExternalChangeEvent;
    if (fileRelPath.startsWith("manuscript/") && fileRelPath.endsWith(".md")) {
      const { updatedCount } = handleExternalChapterUpdate(repoRoot, bookRelPath, fileRelPath);
      payload = {
        bookRelPath,
        fileRelPath,
        kind: "chapter",
        updatedCommentCount: updatedCount,
        message:
          updatedCount > 0
            ? `Updated ${path.basename(fileRelPath)} and adjusted ${updatedCount} note anchor(s).`
            : `Updated ${path.basename(fileRelPath)} from outside changes.`
      };
    } else if (fileRelPath === "reviews/comments.json") {
      payload = {
        bookRelPath,
        fileRelPath,
        kind: "comments",
        updatedCommentCount: 0,
        message: "Notes updated from outside changes."
      };
    } else {
      payload = {
        bookRelPath,
        fileRelPath,
        kind: fileRelPath.includes("canon") ? "canon" : "other",
        updatedCommentCount: 0,
        message: `Updated ${fileRelPath}.`
      };
    }

    pushBackupEvent("External Update", payload.message);
    broadcastSse("external-change", payload);
    void emitBackupStatus({ state: "updated", message: "Updated just now" });
  });
}

async function handleApi(method: string, args: unknown[]): Promise<unknown> {
  switch (method) {
    case "getRepoRoot":
      return repoRoot;
    case "chooseRepoFolder":
      return null;
    case "scanLibrary":
      return scanLibrary(repoRoot);
    case "loadBook":
      return loadBook(repoRoot, String(args[0]));
    case "readChapter":
      return readChapter(repoRoot, String(args[0]), String(args[1]));
    case "readVersionText":
      return readVersionText(repoRoot, String(args[0]), String(args[1]), String(args[2])) ?? "";
    case "saveChapter": {
      const res = saveChapter(
        repoRoot,
        String(args[0]),
        String(args[1]),
        String(args[2]),
        args[3] as CommentRecord[] | undefined
      );
      void emitBackupStatus({ state: "saved", message: "All changes saved" });
      return res;
    }
    case "saveNamedMilestone": {
      const [bookRel, fileRel, label, alsoBackup] = args as [string, string, string, boolean];
      const bookDir = confinedPath(repoRoot, bookRel);
      const absPath = confinedPath(bookDir, fileRel);
      const raw = fs.readFileSync(absPath, "utf-8");
      const versions = recordSnapshot(repoRoot, bookRel, fileRel, raw, {
        author: "You",
        role: "writer",
        summary: String(label || "Saved milestone"),
        force: true
      });
      pushBackupEvent("Milestone Saved", `${path.basename(fileRel)}: ${label}`);
      if (alsoBackup && privacyMode === "private-auto") {
        await runBackupSync(repoRoot, "save-and-share", privacyMode);
      }
      void emitBackupStatus();
      return versions;
    }
    case "restoreVersion": {
      const [bookRel, fileRel, verId] = args as [string, string, string];
      const restored = readVersionText(repoRoot, bookRel, fileRel, verId);
      if (restored === null) throw new Error("Version snapshot not found");
      const bookDir = confinedPath(repoRoot, bookRel);
      atomicWriteFile(confinedPath(bookDir, fileRel), restored);
      recordSnapshot(repoRoot, bookRel, fileRel, restored, {
        author: "You",
        role: "writer",
        summary: `Restored from ${verId}`,
        force: true
      });
      pushBackupEvent("Version Restored", `Created new draft from ${verId}`);
      void emitBackupStatus();
      return readChapter(repoRoot, bookRel, fileRel);
    }
    case "createChapter":
      return createChapter(repoRoot, String(args[0]), String(args[1]));
    case "reorderChapters":
      reorderChapters(repoRoot, String(args[0]), args[1] as string[]);
      return null;
    case "saveBookTextFile":
      saveBookTextFile(repoRoot, String(args[0]), String(args[1]), String(args[2]));
      return null;
    case "saveCharacterSheet":
      saveCharacterSheet(repoRoot, String(args[0]), String(args[1]), args[2] as never);
      return null;
    case "saveComments":
      saveComments(repoRoot, String(args[0]), args[1] as CommentRecord[]);
      void emitBackupStatus();
      return null;
    case "acceptCanonProposal":
      return acceptCanonProposal(repoRoot, String(args[0]), String(args[1]));
    case "getBackupStatus":
      return inspectGitBackupState(repoRoot, autoIntervalMinutes, privacyMode, recentEvents);
    case "setBackupSettings": {
      const settings = args[0] as {
        autoIntervalMinutes: number;
        privacyMode: "private-auto" | "public-pull-only";
      };
      autoIntervalMinutes = settings.autoIntervalMinutes;
      privacyMode = settings.privacyMode;
      return emitBackupStatus();
    }
    case "runBackupNow": {
      const mode = args[0] as "refresh" | "save-and-share";
      const res = await runBackupSync(repoRoot, mode, privacyMode);
      pushBackupEvent(mode === "refresh" ? "Check for Updates" : "Cloud Backup", res.summary);
      return emitBackupStatus({ state: res.ok ? "saved" : "attention", message: res.message });
    }
    case "runStudioCheck":
      return runStudioCheck(repoRoot, String(args[0]));
    case "runBookBuild":
      return runBookBuild(repoRoot, String(args[0]));
    case "runCatalogValidate":
      return runCatalogValidate(repoRoot);
    case "runPublishRelease":
      return runPublishRelease(repoRoot, String(args[0]), Boolean(args[1]));
    case "runAudioDoctor":
      return runAudioDoctor(repoRoot);
    case "runAudioStep":
      return runAudioStep(repoRoot, String(args[0]), args[1] as never);
    case "copyToClipboard":
      lastClipboardText = String(args[0]);
      return lastClipboardText;
    default:
      throw new Error(`Unknown API method: ${method}`);
  }
}

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".json": "application/json; charset=utf-8"
};

startWatcher();

const server = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://127.0.0.1:${port}`);

  if (req.method === "GET" && url.pathname === "/api/events") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive"
    });
    res.write(": connected\n\n");
    sseClients.add(res);
    req.on("close", () => sseClients.delete(res));
    return;
  }

  if (req.method === "POST" && url.pathname.startsWith("/api/")) {
    const method = url.pathname.slice("/api/".length);
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      let args: unknown[] = [];
      try {
        args = body ? (JSON.parse(body) as unknown[]) : [];
      } catch {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Invalid JSON body" }));
        return;
      }
      handleApi(method, args)
        .then((result) => {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ result: result ?? null }));
        })
        .catch((err) => {
          res.writeHead(500, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: err instanceof Error ? err.message : String(err) }));
        });
    });
    return;
  }

  const relAsset = url.pathname === "/" ? "index.html" : url.pathname.replace(/^\/+/, "");
  const candidate = path.resolve(distDir, relAsset);
  if (!candidate.startsWith(distDir) || !fs.existsSync(candidate) || fs.statSync(candidate).isDirectory()) {
    const fallback = path.join(distDir, "index.html");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    fs.createReadStream(fallback).pipe(res);
    return;
  }
  const ext = path.extname(candidate);
  res.writeHead(200, { "Content-Type": MIME[ext] ?? "application/octet-stream" });
  fs.createReadStream(candidate).pipe(res);
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Book Studio local bridge listening on http://127.0.0.1:${port} (library: ${repoRoot})`);
});
