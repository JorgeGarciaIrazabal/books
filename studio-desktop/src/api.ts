import type { BackupStatus, ExternalChangeEvent, StudioApi } from "../shared/types";

async function postApi<T>(method: string, ...args: unknown[]): Promise<T> {
  const res = await fetch(`/api/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args)
  });
  const data = (await res.json()) as { result?: T; error?: string };
  if (!res.ok || data.error) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data.result as T;
}

function createHttpStudioApi(): StudioApi {
  let sharedSource: EventSource | null = null;
  const ensureSource = () => {
    if (!sharedSource) sharedSource = new EventSource("/api/events");
    return sharedSource;
  };

  return {
    getRepoRoot: () => postApi("getRepoRoot"),
    chooseRepoFolder: () => postApi("chooseRepoFolder"),
    scanLibrary: () => postApi("scanLibrary"),
    loadBook: (bookRelPath) => postApi("loadBook", bookRelPath),
    readChapter: (bookRelPath, chapterRelPath) => postApi("readChapter", bookRelPath, chapterRelPath),
    readVersionText: (bookRelPath, fileRelPath, versionId) =>
      postApi("readVersionText", bookRelPath, fileRelPath, versionId),
    saveChapter: (bookRelPath, chapterRelPath, rawMarkdown, updatedComments) =>
      postApi("saveChapter", bookRelPath, chapterRelPath, rawMarkdown, updatedComments),
    saveNamedMilestone: (bookRelPath, fileRelPath, label, alsoCommit) =>
      postApi("saveNamedMilestone", bookRelPath, fileRelPath, label, alsoCommit),
    restoreVersion: (bookRelPath, fileRelPath, versionId) =>
      postApi("restoreVersion", bookRelPath, fileRelPath, versionId),
    createChapter: (bookRelPath, title) => postApi("createChapter", bookRelPath, title),
    reorderChapters: (bookRelPath, chapters) => postApi("reorderChapters", bookRelPath, chapters),
    saveBookTextFile: (bookRelPath, fileRelPath, content) =>
      postApi("saveBookTextFile", bookRelPath, fileRelPath, content),
    saveCharacterSheet: (bookRelPath, charRelPath, fields) =>
      postApi("saveCharacterSheet", bookRelPath, charRelPath, fields),
    saveComments: (bookRelPath, comments) => postApi("saveComments", bookRelPath, comments),
    acceptCanonProposal: (bookRelPath, proposalId) =>
      postApi("acceptCanonProposal", bookRelPath, proposalId),
    getBackupStatus: () => postApi("getBackupStatus"),
    setBackupSettings: (settings) => postApi("setBackupSettings", settings),
    runBackupNow: (mode) => postApi("runBackupNow", mode),
    runStudioCheck: (bookRelPath) => postApi("runStudioCheck", bookRelPath),
    runBookBuild: (bookRelPath) => postApi("runBookBuild", bookRelPath),
    runCatalogValidate: () => postApi("runCatalogValidate"),
    runPublishRelease: (bookRelPath, includeAudio) =>
      postApi("runPublishRelease", bookRelPath, includeAudio),
    runAudioDoctor: () => postApi("runAudioDoctor"),
    runAudioStep: (bookRelPath, step) => postApi("runAudioStep", bookRelPath, step),
    copyToClipboard: async (text) => {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text).catch(() => undefined);
      }
      await postApi("copyToClipboard", text);
    },
    onExternalChange: (cb) => {
      const es = ensureSource();
      const handler = (ev: MessageEvent) => {
        cb(JSON.parse(ev.data) as ExternalChangeEvent);
      };
      es.addEventListener("external-change", handler);
      return () => es.removeEventListener("external-change", handler);
    },
    onBackupStatus: (cb) => {
      const es = ensureSource();
      const handler = (ev: MessageEvent) => {
        cb(JSON.parse(ev.data) as BackupStatus);
      };
      es.addEventListener("backup-status", handler);
      return () => es.removeEventListener("backup-status", handler);
    }
  };
}

let cachedHttpApi: StudioApi | null = null;

export function getStudioApi(): StudioApi {
  if (typeof window !== "undefined" && window.bookStudio) {
    return window.bookStudio;
  }
  if (!cachedHttpApi) {
    cachedHttpApi = createHttpStudioApi();
  }
  return cachedHttpApi;
}
