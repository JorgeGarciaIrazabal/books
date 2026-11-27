import { app, BrowserWindow, clipboard, dialog, ipcMain } from "electron";
import fs from "node:fs";
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

interface UserSettings {
  repoRoot?: string;
  autoIntervalMinutes?: number;
  privacyMode?: "private-auto" | "public-pull-only";
}

function getSettingsPath(): string {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings(): UserSettings {
  try {
    const p = getSettingsPath();
    if (!fs.existsSync(p)) return {};
    return JSON.parse(fs.readFileSync(p, "utf-8")) as UserSettings;
  } catch {
    return {};
  }
}

function saveSettings(next: UserSettings): void {
  try {
    const p = getSettingsPath();
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, JSON.stringify(next, null, 2) + "\n", "utf-8");
  } catch {
    // Non-fatal if userData is unavailable
  }
}

function isStudioRepo(dir: string): boolean {
  return (
    fs.existsSync(path.join(dir, "AGENTS.md")) &&
    fs.existsSync(path.join(dir, "tools", "studio.py"))
  );
}

function readLibraryArg(): string | null {
  const idx = process.argv.indexOf("--library");
  if (idx >= 0 && process.argv[idx + 1]) {
    return path.resolve(process.argv[idx + 1]);
  }
  return null;
}

function resolveDefaultRepoRoot(savedRoot?: string): string {
  const cliArg = readLibraryArg();
  const envRoot = process.env.BOOK_STUDIO_LIBRARY ? path.resolve(process.env.BOOK_STUDIO_LIBRARY) : null;
  const candidates = [
    cliArg,
    envRoot,
    savedRoot ?? null,
    path.resolve(process.cwd(), ".."),
    process.cwd(),
    path.resolve(__dirname, "..", "..", ".."),
    path.join(os.homedir(), "code", "books"),
    path.join(os.homedir(), "books")
  ].filter((x): x is string => Boolean(x));

  for (const dir of candidates) {
    if (isStudioRepo(dir)) return dir;
  }
  return cliArg || envRoot || savedRoot || path.resolve(process.cwd(), "..");
}

let repoRoot = process.cwd();
let mainWindow: BrowserWindow | null = null;
let watcher: FSWatcher | null = null;
let backupTimer: NodeJS.Timeout | null = null;

let autoIntervalMinutes = 2;
let privacyMode: "private-auto" | "public-pull-only" = "private-auto";
const recentEvents: BackupStatus["recentEvents"] = [
  {
    id: "init-1",
    source: "Library Ready",
    time: "Just now",
    summary: "Connected to your Book Studio folder with automatic change tracking."
  }
];

function pushBackupEvent(source: string, summary: string) {
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  recentEvents.unshift({
    id: `ev-${Date.now()}`,
    source,
    time,
    summary
  });
  if (recentEvents.length > 20) recentEvents.pop();
}

async function emitBackupStatus(override?: Partial<BackupStatus>) {
  const status = await inspectGitBackupState(repoRoot, autoIntervalMinutes, privacyMode, recentEvents);
  const finalStatus: BackupStatus = { ...status, ...override };
  mainWindow?.webContents.send("studio:backup-status", finalStatus);
  return finalStatus;
}

function startWatcher() {
  if (watcher) {
    void watcher.close();
    watcher = null;
  }
  watcher = chokidar.watch(repoRoot, {
    ignored: [
      /(^|[/\\])\../,
      /node_modules/,
      /studio-desktop/,
      /_site/,
      /\/exports\//
    ],
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 180, pollInterval: 50 }
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
    mainWindow?.webContents.send("studio:external-change", payload);
    void emitBackupStatus({ state: "updated", message: "Updated just now" });
  });
}

function resetBackupTimer() {
  if (backupTimer) {
    clearInterval(backupTimer);
    backupTimer = null;
  }
  if (autoIntervalMinutes <= 0) return;
  backupTimer = setInterval(async () => {
    const mode = privacyMode === "private-auto" ? "save-and-share" : "refresh";
    const res = await runBackupSync(repoRoot, mode, privacyMode);
    if (res.ok) {
      pushBackupEvent("Auto-Backup", res.summary);
    }
    void emitBackupStatus({
      state: res.ok ? "saved" : "offline",
      message: res.message
    });
  }, autoIntervalMinutes * 60 * 1000);
}

function createWindow() {
  const isDev = process.env.NODE_ENV === "development";
  const iconPath = path.join(__dirname, "..", "..", "assets", "icon.png");
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    backgroundColor: "#f6f1e7",
    title: "Book Studio",
    ...(fs.existsSync(iconPath) ? { icon: iconPath } : {}),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    void mainWindow.loadURL("http://localhost:5173");
  } else {
    void mainWindow.loadFile(path.join(__dirname, "..", "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  const saved = loadSettings();
  repoRoot = resolveDefaultRepoRoot(saved.repoRoot);
  if (typeof saved.autoIntervalMinutes === "number") {
    autoIntervalMinutes = saved.autoIntervalMinutes;
  }
  if (saved.privacyMode === "private-auto" || saved.privacyMode === "public-pull-only") {
    privacyMode = saved.privacyMode;
  }
  saveSettings({ repoRoot, autoIntervalMinutes, privacyMode });

  startWatcher();
  resetBackupTimer();

  ipcMain.handle("studio:getRepoRoot", () => repoRoot);
  ipcMain.handle("studio:chooseRepoFolder", async () => {
    if (!mainWindow) return null;
    const res = await dialog.showOpenDialog(mainWindow, {
      properties: ["openDirectory"],
      defaultPath: repoRoot,
      title: "Select Book Studio Library Folder"
    });
    if (res.canceled || res.filePaths.length === 0) return null;
    repoRoot = res.filePaths[0];
    saveSettings({ repoRoot, autoIntervalMinutes, privacyMode });
    startWatcher();
    void emitBackupStatus();
    return repoRoot;
  });

  ipcMain.handle("studio:scanLibrary", () => scanLibrary(repoRoot));
  ipcMain.handle("studio:loadBook", (_, bookRelPath: string) => loadBook(repoRoot, bookRelPath));
  ipcMain.handle("studio:readChapter", (_, bookRelPath: string, chapterRelPath: string) =>
    readChapter(repoRoot, bookRelPath, chapterRelPath)
  );
  ipcMain.handle("studio:readVersionText", (_, bookRelPath: string, fileRelPath: string, versionId: string) =>
    readVersionText(repoRoot, bookRelPath, fileRelPath, versionId) ?? ""
  );
  ipcMain.handle(
    "studio:saveChapter",
    (_, bookRelPath: string, chapterRelPath: string, rawMarkdown: string, updatedComments?: CommentRecord[]) => {
      const res = saveChapter(repoRoot, bookRelPath, chapterRelPath, rawMarkdown, updatedComments);
      void emitBackupStatus({ state: "saved", message: "All changes saved" });
      return res;
    }
  );
  ipcMain.handle(
    "studio:saveNamedMilestone",
    async (_, bookRelPath: string, fileRelPath: string, label: string, alsoCommit: boolean) => {
      const bookDir = confinedPath(repoRoot, bookRelPath);
      const absPath = confinedPath(bookDir, fileRelPath);
      const raw = fs.readFileSync(absPath, "utf-8");
      const versions = recordSnapshot(repoRoot, bookRelPath, fileRelPath, raw, {
        author: "You",
        role: "writer",
        summary: label.trim() || "Saved milestone",
        force: true
      });
      pushBackupEvent("Milestone Saved", `${path.basename(fileRelPath)}: ${label}`);
      if (alsoCommit && privacyMode === "private-auto") {
        await runBackupSync(repoRoot, "save-and-share", privacyMode);
      }
      void emitBackupStatus();
      return versions;
    }
  );
  ipcMain.handle("studio:restoreVersion", (_, bookRelPath: string, fileRelPath: string, versionId: string) => {
    const restoredText = readVersionText(repoRoot, bookRelPath, fileRelPath, versionId);
    if (restoredText === null) throw new Error("Version snapshot not found");
    const bookDir = confinedPath(repoRoot, bookRelPath);
    const absPath = confinedPath(bookDir, fileRelPath);
    atomicWriteFile(absPath, restoredText);
    recordSnapshot(repoRoot, bookRelPath, fileRelPath, restoredText, {
      author: "You",
      role: "writer",
      summary: `Restored from ${versionId}`,
      force: true
    });
    pushBackupEvent("Version Restored", `Created new draft from ${versionId}`);
    void emitBackupStatus();
    return readChapter(repoRoot, bookRelPath, fileRelPath);
  });
  ipcMain.handle("studio:createChapter", (_, bookRelPath: string, title: string) =>
    createChapter(repoRoot, bookRelPath, title)
  );
  ipcMain.handle("studio:reorderChapters", (_, bookRelPath: string, chapters: string[]) =>
    reorderChapters(repoRoot, bookRelPath, chapters)
  );
  ipcMain.handle("studio:saveBookTextFile", (_, bookRelPath: string, fileRelPath: string, content: string) =>
    saveBookTextFile(repoRoot, bookRelPath, fileRelPath, content)
  );
  ipcMain.handle("studio:saveCharacterSheet", (_, bookRelPath: string, charRelPath: string, fields) =>
    saveCharacterSheet(repoRoot, bookRelPath, charRelPath, fields)
  );
  ipcMain.handle("studio:saveComments", (_, bookRelPath: string, comments: CommentRecord[]) => {
    saveComments(repoRoot, bookRelPath, comments);
    void emitBackupStatus();
  });
  ipcMain.handle("studio:acceptCanonProposal", (_, bookRelPath: string, proposalId: string) =>
    acceptCanonProposal(repoRoot, bookRelPath, proposalId)
  );

  ipcMain.handle("studio:getBackupStatus", () =>
    inspectGitBackupState(repoRoot, autoIntervalMinutes, privacyMode, recentEvents)
  );
  ipcMain.handle(
    "studio:setBackupSettings",
    (_, settings: { autoIntervalMinutes: number; privacyMode: "private-auto" | "public-pull-only" }) => {
      autoIntervalMinutes = settings.autoIntervalMinutes;
      privacyMode = settings.privacyMode;
      saveSettings({ repoRoot, autoIntervalMinutes, privacyMode });
      resetBackupTimer();
      return emitBackupStatus();
    }
  );
  ipcMain.handle("studio:runBackupNow", async (_, mode: "refresh" | "save-and-share") => {
    await emitBackupStatus({ state: "syncing", message: "Backing up & checking for updates…" });
    const res = await runBackupSync(repoRoot, mode, privacyMode);
    pushBackupEvent(mode === "refresh" ? "Check for Updates" : "Cloud Backup", res.summary);
    return emitBackupStatus({ state: res.ok ? "saved" : "attention", message: res.message });
  });

  ipcMain.handle("studio:runStudioCheck", (_, bookRelPath: string) => runStudioCheck(repoRoot, bookRelPath));
  ipcMain.handle("studio:runBookBuild", (_, bookRelPath: string) => runBookBuild(repoRoot, bookRelPath));
  ipcMain.handle("studio:runCatalogValidate", () => runCatalogValidate(repoRoot));
  ipcMain.handle("studio:runPublishRelease", (_, bookRelPath: string, includeAudio: boolean) =>
    runPublishRelease(repoRoot, bookRelPath, includeAudio)
  );
  ipcMain.handle("studio:runAudioDoctor", () => runAudioDoctor(repoRoot));
  ipcMain.handle(
    "studio:runAudioStep",
    (_, bookRelPath: string, step: "prepare" | "pilot" | "render" | "verify") =>
      runAudioStep(repoRoot, bookRelPath, step)
  );
  ipcMain.handle("studio:copyToClipboard", (_, text: string) => {
    clipboard.writeText(text);
  });

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (watcher) void watcher.close();
  if (backupTimer) clearInterval(backupTimer);
  if (process.platform !== "darwin") app.quit();
});
