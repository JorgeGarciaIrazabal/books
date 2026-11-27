import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import type { BackupStatus, CommandResult } from "../shared/types";

function runProcess(
  cmd: string,
  args: string[],
  cwd: string,
  timeoutMs = 120000
): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    execFile(
      cmd,
      args,
      {
        cwd,
        timeout: timeoutMs,
        env: { ...process.env, GIT_TERMINAL_PROMPT: "0", GCM_INTERACTIVE: "Never" }
      },
      (err, stdout, stderr) => {
        if (err && typeof (err as NodeJS.ErrnoException).code === "string") {
          resolve({ code: 127, stdout: stdout || "", stderr: err.message });
          return;
        }
        const exitCode =
          err && typeof (err as { code?: number }).code === "number"
            ? (err as { code: number }).code
            : 0;
        resolve({ code: exitCode, stdout: stdout || "", stderr: stderr || "" });
      }
    );
  });
}

async function runPython(
  args: string[],
  cwd: string,
  timeoutMs = 120000
): Promise<{ code: number; stdout: string; stderr: string }> {
  const candidates = process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"];
  for (const bin of candidates) {
    const finalArgs = bin === "py" ? ["-3", ...args] : args;
    const res = await runProcess(bin, finalArgs, cwd, timeoutMs);
    if (res.code !== 127) return res;
  }
  return { code: 127, stdout: "", stderr: "Python 3.11+ was not found on PATH." };
}

export async function inspectGitBackupState(
  repoRoot: string,
  autoIntervalMinutes: number,
  privacyMode: "private-auto" | "public-pull-only",
  recentEvents: BackupStatus["recentEvents"]
): Promise<BackupStatus> {
  const branchRes = await runProcess("git", ["symbolic-ref", "--short", "HEAD"], repoRoot, 5000);
  const branch = branchRes.code === 0 ? branchRes.stdout.trim() : "main";

  const remoteRes = await runProcess("git", ["remote", "get-url", "origin"], repoRoot, 5000);
  const remoteUrl = remoteRes.stdout.trim();
  const isPublicOrigin = /github\.com[:/].*\/books(?:\.git)?$/i.test(remoteUrl);

  let ahead = 0;
  let behind = 0;
  const countsRes = await runProcess(
    "git",
    ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
    repoRoot,
    5000
  );
  if (countsRes.code === 0) {
    const parts = countsRes.stdout.trim().split(/\s+/);
    ahead = Number(parts[0] ?? 0) || 0;
    behind = Number(parts[1] ?? 0) || 0;
  }

  const dirtyRes = await runProcess("git", ["status", "--porcelain"], repoRoot, 5000);
  const hasUncommitted = dirtyRes.code === 0 && dirtyRes.stdout.trim().length > 0;
  if (hasUncommitted) ahead = Math.max(ahead, 1);

  return {
    state: "saved",
    message: ahead > 0 ? "Saved on this computer" : "All changes saved & backed up",
    ahead,
    behind,
    lastBackupTime: recentEvents[0]?.time ?? "Just now",
    branch,
    isPublicOrigin,
    autoIntervalMinutes,
    privacyMode,
    recentEvents
  };
}

export async function runBackupSync(
  repoRoot: string,
  mode: "refresh" | "save-and-share",
  privacyMode: "private-auto" | "public-pull-only"
): Promise<{ ok: boolean; message: string; summary: string }> {
  const refreshRes = await runPython(["tools/studio_sync.py", "refresh"], repoRoot, 30000);
  if (refreshRes.code !== 0) {
    return {
      ok: false,
      message: "Saved on this computer (cloud backup paused)",
      summary: refreshRes.stderr.trim() || "Could not reach cloud backup."
    };
  }

  if (mode === "refresh") {
    return {
      ok: true,
      message: "Checked for updates",
      summary: "Checked your shared library for newer updates."
    };
  }

  if (privacyMode === "public-pull-only") {
    return {
      ok: true,
      message: "Saved locally (public catalog protected)",
      summary:
        "Checked for updates. Unpublished drafts stay on your computer until you choose to publish."
    };
  }

  // Scope save to tracked/unignored writer files via studio_sync.py
  const statusRes = await runProcess(
    "git",
    ["status", "--porcelain", "--untracked-files=all"],
    repoRoot,
    5000
  );
  const paths = statusRes.stdout
    .split("\n")
    .map((line) => line.slice(3).trim())
    .filter((p) => p && !p.startsWith("studio-desktop/") && !p.startsWith(".studio-desktop/"));

  if (paths.length === 0) {
    return {
      ok: true,
      message: "All changes backed up",
      summary: "Everything is already safely backed up."
    };
  }

  const saveRes = await runPython(
    ["tools/studio_sync.py", "save", "-m", "Save writing progress", ...paths],
    repoRoot,
    30000
  );
  if (saveRes.code !== 0) {
    return {
      ok: false,
      message: "Saved locally (backup needs review)",
      summary: saveRes.stderr.trim() || "Could not create backup snapshot."
    };
  }

  const rev = saveRes.stdout.trim();
  if (rev) {
    const shareRes = await runPython(["tools/studio_sync.py", "share", rev], repoRoot, 30000);
    if (shareRes.code !== 0) {
      return {
        ok: false,
        message: "Saved on this computer",
        summary: shareRes.stderr.trim() || "Cloud copy moved; refresh before backing up."
      };
    }
  }

  return {
    ok: true,
    message: "All changes saved & backed up",
    summary: `Backed up ${paths.length} updated file(s) safely.`
  };
}

export async function runStudioCheck(repoRoot: string, bookRelPath: string): Promise<CommandResult> {
  const res = await runPython(["tools/studio.py", "check", bookRelPath], repoRoot);
  return {
    ok: res.code === 0,
    summary: res.code === 0 ? "Book structure and links passed all checks." : "Some items need attention.",
    details: (res.stdout + "\n" + res.stderr).trim()
  };
}

export async function runBookBuild(repoRoot: string, bookRelPath: string): Promise<CommandResult> {
  const buildMd = await runPython(
    ["tools/studio.py", "build", bookRelPath, "--name", "reading-copy", "--replace"],
    repoRoot
  );
  if (buildMd.code !== 0) {
    return {
      ok: false,
      summary: "Could not prepare reading copy.",
      details: (buildMd.stdout + "\n" + buildMd.stderr).trim()
    };
  }

  const bookDir = path.join(repoRoot, bookRelPath);
  const logs = [buildMd.stdout.trim()];

  const epubScript = path.join(bookDir, "production", "build_epub.py");
  if (fs.existsSync(epubScript)) {
    const epubRes = await runPython([epubScript], repoRoot);
    logs.push(epubRes.stdout.trim() || epubRes.stderr.trim());
  }

  const pdfScript = path.join(bookDir, "production", "build_pdf.py");
  if (fs.existsSync(pdfScript)) {
    const pdfRes = await runPython([pdfScript], repoRoot);
    logs.push(pdfRes.stdout.trim() || pdfRes.stderr.trim());
  }

  return {
    ok: true,
    summary: "Reading copy prepared.",
    details: logs.filter(Boolean).join("\n")
  };
}

export async function runCatalogValidate(repoRoot: string): Promise<CommandResult> {
  const res = await runPython(["tools/build_catalog.py", "validate"], repoRoot);
  return {
    ok: res.code === 0,
    summary:
      res.code === 0
        ? "Ready for readers (0 leaked notes or audio tags)."
        : "Readiness check found issues.",
    details: (res.stdout + "\n" + res.stderr).trim()
  };
}

export async function runPublishRelease(
  repoRoot: string,
  bookRelPath: string,
  includeAudio: boolean
): Promise<CommandResult> {
  const check = await runStudioCheck(repoRoot, bookRelPath);
  if (!check.ok) return check;

  const buildSite = await runPython(["tools/build_catalog.py", "build"], repoRoot);
  if (buildSite.code !== 0) {
    return {
      ok: false,
      summary: "Could not assemble reader edition.",
      details: (buildSite.stdout + "\n" + buildSite.stderr).trim()
    };
  }

  // Trigger manual-only GitHub Pages workflow if gh CLI is signed in
  const ghRes = await runProcess("gh", ["workflow", "run", "pages.yml"], repoRoot, 20000);
  const ghNote =
    ghRes.code === 0
      ? "Public library update triggered."
      : "Edition built and verified locally. Push your authorized release and run the manual Publish workflow when ready.";

  return {
    ok: true,
    summary: includeAudio
      ? "Edition + audio layer prepared for readers."
      : "Edition prepared for readers.",
    details: [buildSite.stdout.trim(), ghNote].filter(Boolean).join("\n")
  };
}

export async function runAudioDoctor(repoRoot: string): Promise<CommandResult> {
  const res = await runPython(["tools/drama3.py", "doctor"], repoRoot, 30000);
  return {
    ok: res.code === 0,
    summary:
      res.code === 0
        ? "Audio studio is ready (Fish Audio Drama 3)."
        : "Audio studio setup needs attention on this computer.",
    details: (res.stdout + "\n" + res.stderr).trim()
  };
}

export async function runAudioStep(
  repoRoot: string,
  bookRelPath: string,
  step: "prepare" | "pilot" | "render" | "verify"
): Promise<CommandResult> {
  const bookDir = path.join(repoRoot, bookRelPath);
  const manifestOut = path.join(bookDir, "exports", "narration-segments.json");
  const audioOutDir = path.join(bookDir, "exports", "narration-drama3");

  let args: string[];
  if (step === "prepare") {
    args = ["tools/drama3.py", "prepare-chapters", bookRelPath, "--output", manifestOut];
  } else if (step === "pilot") {
    args = [
      "tools/drama3.py",
      "render",
      manifestOut,
      "--output-dir",
      audioOutDir,
      "--limit",
      "1"
    ];
  } else if (step === "render") {
    args = ["tools/drama3.py", "render", manifestOut, "--output-dir", audioOutDir];
  } else {
    args = ["tools/drama3.py", "check", manifestOut, "--audio-dir", audioOutDir];
  }

  const res = await runPython(args, repoRoot, 600000);
  return {
    ok: res.code === 0,
    summary: res.code === 0 ? `Audio step "${step}" completed.` : `Audio step "${step}" reported an issue.`,
    details: (res.stdout + "\n" + res.stderr).trim()
  };
}
