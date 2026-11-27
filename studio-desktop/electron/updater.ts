import { execFile } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import https from "node:https";
import os from "node:os";
import path from "node:path";
import { app, shell } from "electron";
import { autoUpdater } from "electron-updater";
import type { AppUpdateStatus, CommandResult } from "../shared/types";
import { formatReleaseVersion, isNewerVersion } from "../shared/version";

const GITHUB_OWNER = "JorgeGarciaIrazabal";
const GITHUB_REPO = "books";
const RELEASES_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases/latest`;
const RELEASES_PAGE_URL = `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases`;
const ALLOWED_ASSET_PREFIX = `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases/download/`;

interface GitHubReleaseAsset {
  name?: string;
  browser_download_url?: string;
}

interface GitHubReleaseResponse {
  tag_name?: string;
  html_url?: string;
  assets?: GitHubReleaseAsset[];
}

type UpdateInstallKind = AppUpdateStatus["installKind"];

function detectInstallKind(): UpdateInstallKind {
  if (!app.isPackaged) return "manual";
  if (process.platform === "win32") return "native";
  if (process.platform === "linux") {
    if (process.env.APPIMAGE) return "native";
    if (app.getAppPath().startsWith("/opt/")) return "deb";
  }
  return "manual";
}

function nowTimeLabel(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

let status: AppUpdateStatus = {
  state: "idle",
  currentVersion: app.getVersion(),
  canAutoInstall: false,
  installKind: detectInstallKind(),
  message: `Book Studio v${app.getVersion()}`
};

let statusListener: ((next: AppUpdateStatus) => void) | null = null;
let initialized = false;
let checkInFlight: Promise<AppUpdateStatus> | null = null;
let downloadedDebPath: string | null = null;
let startupTimer: NodeJS.Timeout | null = null;
let intervalTimer: NodeJS.Timeout | null = null;

function updateState(patch: Partial<AppUpdateStatus>): AppUpdateStatus {
  status = { ...status, ...patch };
  statusListener?.(status);
  return status;
}

export function getAppUpdateStatus(): AppUpdateStatus {
  return status;
}

export async function openSafeExternalUrl(rawUrl: string): Promise<void> {
  const parsed = new URL(rawUrl);
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    throw new Error("Only web links can be opened externally.");
  }
  await shell.openExternal(parsed.toString());
}

function fetchJson<T>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        headers: {
          "User-Agent": `Book-Studio-Desktop/${app.getVersion()}`,
          Accept: "application/vnd.github+json"
        },
        timeout: 15000
      },
      (res) => {
        if ((res.statusCode ?? 0) >= 300 && (res.statusCode ?? 0) < 400 && res.headers.location) {
          res.resume();
          fetchJson<T>(res.headers.location).then(resolve, reject);
          return;
        }
        if (res.statusCode !== 200) {
          res.resume();
          reject(new Error(`Update server returned HTTP ${res.statusCode}`));
          return;
        }
        let body = "";
        res.setEncoding("utf-8");
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            resolve(JSON.parse(body) as T);
          } catch (err) {
            reject(err);
          }
        });
      }
    );
    req.on("timeout", () => {
      req.destroy(new Error("Timed out checking for updates"));
    });
    req.on("error", reject);
  });
}

function downloadFileWithProgress(
  url: string,
  destPath: string,
  onPercent: (pct: number) => void,
  redirectsLeft = 5
): Promise<void> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
      reject(new Error("Unsupported download URL scheme"));
      return;
    }
    const client = parsed.protocol === "https:" ? https : http;
    const req = client.get(
      parsed.toString(),
      {
        headers: { "User-Agent": `Book-Studio-Desktop/${app.getVersion()}` },
        timeout: 120000
      },
      (res) => {
        if ((res.statusCode ?? 0) >= 300 && (res.statusCode ?? 0) < 400 && res.headers.location) {
          res.resume();
          if (redirectsLeft <= 0) {
            reject(new Error("Too many redirects while downloading update"));
            return;
          }
          downloadFileWithProgress(res.headers.location, destPath, onPercent, redirectsLeft - 1).then(
            resolve,
            reject
          );
          return;
        }
        if (res.statusCode !== 200) {
          res.resume();
          reject(new Error(`Failed to download update (HTTP ${res.statusCode})`));
          return;
        }
        const total = Number(res.headers["content-length"] ?? 0);
        let received = 0;
        let lastPct = -1;
        const out = fs.createWriteStream(destPath);
        res.on("data", (chunk: Buffer) => {
          received += chunk.length;
          if (total > 0) {
            const pct = Math.min(99, Math.round((received / total) * 100));
            if (pct !== lastPct) {
              lastPct = pct;
              onPercent(pct);
            }
          }
        });
        res.pipe(out);
        out.on("finish", () => {
          out.close(() => {
            onPercent(100);
            resolve();
          });
        });
        out.on("error", (err) => {
          out.close();
          try {
            fs.unlinkSync(destPath);
          } catch {
            // ignore
          }
          reject(err);
        });
      }
    );
    req.on("timeout", () => req.destroy(new Error("Timed out downloading update")));
    req.on("error", reject);
  });
}

function isValidDebArchive(filePath: string): boolean {
  try {
    const fd = fs.openSync(filePath, "r");
    const buf = Buffer.alloc(8);
    const read = fs.readSync(fd, buf, 0, 8, 0);
    fs.closeSync(fd);
    return read === 8 && buf.toString("ascii") === "!<arch>\n";
  } catch {
    return false;
  }
}

async function checkViaGitHubApi(kind: "deb" | "manual"): Promise<AppUpdateStatus> {
  updateState({
    state: "checking",
    installKind: kind,
    message: "Checking for app updates…"
  });

  try {
    const release = await fetchJson<GitHubReleaseResponse>(RELEASES_API_URL);
    const current = app.getVersion();
    const latestTag = release.tag_name ?? "";
    const latestVersion = formatReleaseVersion(latestTag);
    const releaseUrl = release.html_url || RELEASES_PAGE_URL;
    const checkedAt = nowTimeLabel();

    if (!latestVersion || !isNewerVersion(latestVersion, current)) {
      return updateState({
        state: "up-to-date",
        currentVersion: current,
        latestVersion: latestVersion || current,
        releaseUrl,
        canAutoInstall: false,
        downloadPercent: undefined,
        checkedAt,
        message: `You're up to date (v${current})`
      });
    }

    if (kind === "deb") {
      const debAsset = (release.assets ?? []).find(
        (a) =>
          typeof a.name === "string" &&
          a.name.endsWith(".deb") &&
          typeof a.browser_download_url === "string" &&
          a.browser_download_url.startsWith(ALLOWED_ASSET_PREFIX)
      );
      if (debAsset?.browser_download_url) {
        updateState({
          state: "downloading",
          latestVersion,
          releaseUrl,
          downloadPercent: 0,
          canAutoInstall: false,
          checkedAt,
          message: `Downloading Book Studio v${latestVersion}…`
        });

        const targetDeb = path.join(os.tmpdir(), `book-studio-desktop-${latestVersion}.deb`);
        await downloadFileWithProgress(debAsset.browser_download_url, targetDeb, (pct) => {
          updateState({
            state: "downloading",
            downloadPercent: pct,
            message: `Downloading Book Studio v${latestVersion} (${pct}%)…`
          });
        });

        if (!isValidDebArchive(targetDeb)) {
          throw new Error("Downloaded update file did not match package format.");
        }
        downloadedDebPath = targetDeb;
        return updateState({
          state: "downloaded",
          latestVersion,
          releaseUrl,
          downloadPercent: 100,
          canAutoInstall: true,
          checkedAt,
          message: `Book Studio v${latestVersion} is ready to install`
        });
      }
    }

    return updateState({
      state: "available",
      latestVersion,
      releaseUrl,
      canAutoInstall: false,
      downloadPercent: undefined,
      checkedAt,
      message: `Book Studio v${latestVersion} is available`
    });
  } catch (err) {
    return updateState({
      state: "error",
      canAutoInstall: false,
      downloadPercent: undefined,
      checkedAt: nowTimeLabel(),
      message: err instanceof Error ? `Update check paused: ${err.message}` : "Could not check for updates."
    });
  }
}

function setupNativeUpdater(): void {
  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = true;

  autoUpdater.on("checking-for-update", () => {
    updateState({
      state: "checking",
      installKind: "native",
      message: "Checking for app updates…"
    });
  });

  autoUpdater.on("update-available", (info) => {
    const nextVer = formatReleaseVersion(info.version);
    updateState({
      state: "downloading",
      latestVersion: nextVer,
      releaseUrl: `${RELEASES_PAGE_URL}/tag/desktop-v${nextVer}`,
      downloadPercent: 0,
      canAutoInstall: false,
      checkedAt: nowTimeLabel(),
      message: `Downloading Book Studio v${nextVer}…`
    });
  });

  autoUpdater.on("update-not-available", () => {
    updateState({
      state: "up-to-date",
      latestVersion: app.getVersion(),
      canAutoInstall: false,
      downloadPercent: undefined,
      checkedAt: nowTimeLabel(),
      message: `You're up to date (v${app.getVersion()})`
    });
  });

  autoUpdater.on("download-progress", (progress) => {
    const pct = Math.min(99, Math.max(0, Math.round(progress.percent || 0)));
    updateState({
      state: "downloading",
      downloadPercent: pct,
      message: `Downloading Book Studio v${status.latestVersion ?? "update"} (${pct}%)…`
    });
  });

  autoUpdater.on("update-downloaded", (info) => {
    const nextVer = formatReleaseVersion(info.version);
    updateState({
      state: "downloaded",
      latestVersion: nextVer,
      releaseUrl: `${RELEASES_PAGE_URL}/tag/desktop-v${nextVer}`,
      downloadPercent: 100,
      canAutoInstall: true,
      checkedAt: nowTimeLabel(),
      message: `Book Studio v${nextVer} is ready — restart to update`
    });
  });

  autoUpdater.on("error", (err) => {
    updateState({
      state: "error",
      canAutoInstall: false,
      downloadPercent: undefined,
      checkedAt: nowTimeLabel(),
      message: err?.message ? `Update check paused: ${err.message}` : "Could not check for updates."
    });
  });
}

export function initAppUpdater(onStatusChange: (next: AppUpdateStatus) => void): void {
  statusListener = onStatusChange;
  const kind = detectInstallKind();
  status = {
    ...status,
    currentVersion: app.getVersion(),
    installKind: kind,
    message: `Book Studio v${app.getVersion()}`
  };

  if (!initialized && kind === "native") {
    setupNativeUpdater();
  }
  initialized = true;

  if (app.isPackaged && !startupTimer) {
    startupTimer = setTimeout(() => {
      void checkForAppUpdates();
    }, 10_000);
    startupTimer.unref();

    intervalTimer = setInterval(() => {
      void checkForAppUpdates();
    }, 4 * 60 * 60 * 1000);
    intervalTimer.unref();
  }
}

export function stopAppUpdater(): void {
  if (startupTimer) {
    clearTimeout(startupTimer);
    startupTimer = null;
  }
  if (intervalTimer) {
    clearInterval(intervalTimer);
    intervalTimer = null;
  }
}

export async function checkForAppUpdates(): Promise<AppUpdateStatus> {
  if (checkInFlight) return checkInFlight;

  const kind = detectInstallKind();
  if (kind === "native") {
    checkInFlight = (async () => {
      try {
        await autoUpdater.checkForUpdates();
      } catch (err) {
        updateState({
          state: "error",
          checkedAt: nowTimeLabel(),
          message:
            err instanceof Error ? `Update check paused: ${err.message}` : "Could not check for updates."
        });
      }
      return status;
    })();
  } else {
    checkInFlight = checkViaGitHubApi(kind);
  }

  try {
    return await checkInFlight;
  } finally {
    checkInFlight = null;
  }
}

export async function installAppUpdate(): Promise<CommandResult> {
  const kind = detectInstallKind();
  if (kind === "native" && status.state === "downloaded") {
    setTimeout(() => {
      autoUpdater.quitAndInstall(false, true);
    }, 250);
    return {
      ok: true,
      summary: "Restarting to finish installing the update…",
      details: ""
    };
  }

  if (kind === "deb" && downloadedDebPath && fs.existsSync(downloadedDebPath)) {
    const debPath = downloadedDebPath;
    return new Promise((resolve) => {
      execFile("pkexec", ["apt-get", "install", "-y", debPath], { timeout: 120000 }, (err, stdout, stderr) => {
        if (!err) {
          setTimeout(() => {
            app.relaunch();
            app.exit(0);
          }, 250);
          resolve({
            ok: true,
            summary: "Update installed. Restarting Book Studio…",
            details: stdout.trim()
          });
          return;
        }
        resolve({
          ok: false,
          summary: "Automatic install was cancelled or needs terminal permission.",
          details: (stderr || err.message || `Downloaded package: ${debPath}`).trim()
        });
      });
    });
  }

  const targetUrl = status.releaseUrl || RELEASES_PAGE_URL;
  await openSafeExternalUrl(targetUrl);
  return {
    ok: true,
    summary: "Opened the Book Studio downloads page in your browser.",
    details: targetUrl
  };
}
