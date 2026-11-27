import { contextBridge, ipcRenderer } from "electron";
import type { BackupStatus, ExternalChangeEvent, StudioApi } from "../shared/types";

const api: StudioApi = {
  getRepoRoot: () => ipcRenderer.invoke("studio:getRepoRoot"),
  chooseRepoFolder: () => ipcRenderer.invoke("studio:chooseRepoFolder"),
  scanLibrary: () => ipcRenderer.invoke("studio:scanLibrary"),
  loadBook: (bookRelPath) => ipcRenderer.invoke("studio:loadBook", bookRelPath),
  readChapter: (bookRelPath, chapterRelPath) =>
    ipcRenderer.invoke("studio:readChapter", bookRelPath, chapterRelPath),
  readVersionText: (bookRelPath, fileRelPath, versionId) =>
    ipcRenderer.invoke("studio:readVersionText", bookRelPath, fileRelPath, versionId),
  saveChapter: (bookRelPath, chapterRelPath, rawMarkdown, updatedComments) =>
    ipcRenderer.invoke(
      "studio:saveChapter",
      bookRelPath,
      chapterRelPath,
      rawMarkdown,
      updatedComments
    ),
  saveNamedMilestone: (bookRelPath, fileRelPath, label, alsoCommit) =>
    ipcRenderer.invoke("studio:saveNamedMilestone", bookRelPath, fileRelPath, label, alsoCommit),
  restoreVersion: (bookRelPath, fileRelPath, versionId) =>
    ipcRenderer.invoke("studio:restoreVersion", bookRelPath, fileRelPath, versionId),
  createChapter: (bookRelPath, title) =>
    ipcRenderer.invoke("studio:createChapter", bookRelPath, title),
  reorderChapters: (bookRelPath, chapters) =>
    ipcRenderer.invoke("studio:reorderChapters", bookRelPath, chapters),
  saveBookTextFile: (bookRelPath, fileRelPath, content) =>
    ipcRenderer.invoke("studio:saveBookTextFile", bookRelPath, fileRelPath, content),
  saveCharacterSheet: (bookRelPath, charRelPath, fields) =>
    ipcRenderer.invoke("studio:saveCharacterSheet", bookRelPath, charRelPath, fields),
  saveComments: (bookRelPath, comments) =>
    ipcRenderer.invoke("studio:saveComments", bookRelPath, comments),
  acceptCanonProposal: (bookRelPath, proposalId) =>
    ipcRenderer.invoke("studio:acceptCanonProposal", bookRelPath, proposalId),
  getBackupStatus: () => ipcRenderer.invoke("studio:getBackupStatus"),
  setBackupSettings: (settings) => ipcRenderer.invoke("studio:setBackupSettings", settings),
  runBackupNow: (mode) => ipcRenderer.invoke("studio:runBackupNow", mode),
  runStudioCheck: (bookRelPath) => ipcRenderer.invoke("studio:runStudioCheck", bookRelPath),
  runBookBuild: (bookRelPath) => ipcRenderer.invoke("studio:runBookBuild", bookRelPath),
  runCatalogValidate: () => ipcRenderer.invoke("studio:runCatalogValidate"),
  runPublishRelease: (bookRelPath, includeAudio) =>
    ipcRenderer.invoke("studio:runPublishRelease", bookRelPath, includeAudio),
  runAudioDoctor: () => ipcRenderer.invoke("studio:runAudioDoctor"),
  runAudioStep: (bookRelPath, step) =>
    ipcRenderer.invoke("studio:runAudioStep", bookRelPath, step),
  copyToClipboard: (text) => ipcRenderer.invoke("studio:copyToClipboard", text),
  onExternalChange: (cb) => {
    const listener = (_: unknown, payload: ExternalChangeEvent) => cb(payload);
    ipcRenderer.on("studio:external-change", listener);
    return () => ipcRenderer.removeListener("studio:external-change", listener);
  },
  onBackupStatus: (cb) => {
    const listener = (_: unknown, payload: BackupStatus) => cb(payload);
    ipcRenderer.on("studio:backup-status", listener);
    return () => ipcRenderer.removeListener("studio:backup-status", listener);
  }
};

contextBridge.exposeInMainWorld("bookStudio", api);
