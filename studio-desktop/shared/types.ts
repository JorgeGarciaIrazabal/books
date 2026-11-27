export type BookStage =
  | "brief"
  | "structure"
  | "sample"
  | "draft"
  | "development"
  | "line-copy"
  | "continuity-evidence"
  | "production"
  | "released"
  | string;

export interface BookSummary {
  relPath: string; // universe/series/book
  id: string;
  universe: string;
  universeTitle: string;
  series: string;
  seriesTitle: string;
  title: string;
  kind: "fiction" | "nonfiction" | string;
  stage: BookStage;
  language: string;
  chapterCount: number;
  characterCount: number;
  openCommentCount: number;
  coverPath: string | null;
}

export interface ChapterSummary {
  relPath: string; // e.g. manuscript/001-the-reluctant-steward.md
  title: string;
  wordCount: number;
  openComments: number;
  sha256: string;
}

export interface CharacterSheet {
  id: string;
  relPath: string;
  name: string;
  subtitle: string;
  status: string;
  role: string;
  want: string;
  limits: string;
  voice: string;
  sampleLine: string;
  rawMarkdown: string;
}

export interface CanonRecord {
  id: string;
  title: string;
  text: string;
  status: "accepted" | "proposed" | "superseded" | string;
  scope: string;
  sourceFile: string; // relative to book or universe
  provenance?: string;
  storyTime?: string;
  isProposal: boolean;
}

export interface SceneCard {
  id: string;
  chapter: string;
  pov: string;
  place?: string;
  storyTime?: string;
  incoming: string;
  turn: string;
  outgoing: string;
  status?: string;
}

export interface DisclosureRecord {
  id: string;
  topic: string;
  knownBy: string[];
  reader: string;
  when?: string;
  note?: string;
}

export interface EditorialGate {
  id: string;
  checkpoint: string;
  status: "pass" | "revise" | "not-applicable" | string;
  reviewer: string;
  evidence: string;
  openIssues: string[];
}

export interface EditorialIssue {
  id: string;
  severity: string;
  status: string;
  location: string;
  evidence: string;
  suggestion: string;
}

export type CommentTarget =
  | {
      kind: "markdown";
      file: string; // relative to book root, e.g. manuscript/001-the-reluctant-steward.md
    }
  | {
      kind: "record";
      file: string; // e.g. ../../canon.json or canon/proposals.json
      recordId: string;
      recordTitle?: string;
      field?: string;
    };

export interface CommentAnchor {
  quote: string;
  originalQuote: string;
  prefix?: string;
  suffix?: string;
  blockIndex?: number;
  startOffset?: number;
  endOffset?: number;
  occurrence?: number;
  headingHint?: string;
  fileSha256?: string;
  autoUpdated?: boolean;
  orphaned?: boolean;
}

export interface CommentReply {
  author: string;
  body: string;
  createdAt: string;
}

export interface CommentRecord {
  id: string;
  target: CommentTarget;
  anchor: CommentAnchor;
  author: string;
  targetRole: string;
  intent: "revise" | "check-canon" | "critique" | "personal-note" | string;
  body: string;
  status: "open" | "needs-review" | "resolved" | "dismissed" | string;
  createdAt: string;
  thread: CommentReply[];
}

export interface VersionEntry {
  id: string;
  num: number;
  author: string;
  role: "writer" | "external";
  timestamp: string;
  summary: string;
  delta: string;
  sha256: string;
}

export interface ChapterContent {
  relPath: string;
  title: string;
  bodyMarkdown: string;
  rawMarkdown: string;
  blocks: string[];
  sha256: string;
  wordCount: number;
  versions: VersionEntry[];
}

export interface BookDetail {
  summary: BookSummary;
  chapters: ChapterSummary[];
  characters: CharacterSheet[];
  canon: CanonRecord[];
  scenes: SceneCard[];
  disclosures: DisclosureRecord[];
  gates: EditorialGate[];
  issues: EditorialIssue[];
  comments: CommentRecord[];
  briefMarkdown: string;
  styleMarkdown: string;
  outlineMarkdown: string;
  bibleMarkdown: string;
  glossaryMarkdown: string;
  isPublicEdition: boolean;
  hasNarrationConfig: boolean;
}

export interface BackupStatus {
  state: "saved" | "saving" | "syncing" | "updated" | "offline" | "attention";
  message: string;
  ahead: number;
  behind: number;
  lastBackupTime: string;
  branch: string;
  isPublicOrigin: boolean;
  autoIntervalMinutes: number; // 0 = manual
  privacyMode: "private-auto" | "public-pull-only";
  recentEvents: Array<{
    id: string;
    source: string;
    time: string;
    summary: string;
  }>;
}

export interface CommandResult {
  ok: boolean;
  summary: string;
  details: string;
}

export interface ExternalChangeEvent {
  bookRelPath: string;
  fileRelPath: string;
  kind: "chapter" | "comments" | "canon" | "book" | "other";
  updatedCommentCount: number;
  message: string;
}

export interface StudioApi {
  getRepoRoot: () => Promise<string>;
  chooseRepoFolder: () => Promise<string | null>;
  scanLibrary: () => Promise<BookSummary[]>;
  loadBook: (bookRelPath: string) => Promise<BookDetail>;
  readChapter: (bookRelPath: string, chapterRelPath: string) => Promise<ChapterContent>;
  readVersionText: (bookRelPath: string, fileRelPath: string, versionId: string) => Promise<string>;
  saveChapter: (
    bookRelPath: string,
    chapterRelPath: string,
    rawMarkdown: string,
    updatedComments?: CommentRecord[]
  ) => Promise<{ sha256: string; wordCount: number; versions: VersionEntry[] }>;
  saveNamedMilestone: (
    bookRelPath: string,
    fileRelPath: string,
    label: string,
    alsoCommit: boolean
  ) => Promise<VersionEntry[]>;
  restoreVersion: (
    bookRelPath: string,
    fileRelPath: string,
    versionId: string
  ) => Promise<ChapterContent>;
  createChapter: (bookRelPath: string, title: string) => Promise<{ relPath: string }>;
  reorderChapters: (bookRelPath: string, chapters: string[]) => Promise<void>;
  saveBookTextFile: (bookRelPath: string, fileRelPath: string, content: string) => Promise<void>;
  saveCharacterSheet: (
    bookRelPath: string,
    charRelPath: string,
    fields: Pick<CharacterSheet, "role" | "want" | "limits" | "voice" | "sampleLine">
  ) => Promise<void>;
  saveComments: (bookRelPath: string, comments: CommentRecord[]) => Promise<void>;
  acceptCanonProposal: (bookRelPath: string, proposalId: string) => Promise<CanonRecord[]>;
  getBackupStatus: () => Promise<BackupStatus>;
  setBackupSettings: (settings: {
    autoIntervalMinutes: number;
    privacyMode: "private-auto" | "public-pull-only";
  }) => Promise<BackupStatus>;
  runBackupNow: (mode: "refresh" | "save-and-share") => Promise<BackupStatus>;
  runStudioCheck: (bookRelPath: string) => Promise<CommandResult>;
  runBookBuild: (bookRelPath: string) => Promise<CommandResult>;
  runCatalogValidate: () => Promise<CommandResult>;
  runPublishRelease: (bookRelPath: string, includeAudio: boolean) => Promise<CommandResult>;
  runAudioDoctor: () => Promise<CommandResult>;
  runAudioStep: (
    bookRelPath: string,
    step: "prepare" | "pilot" | "render" | "verify"
  ) => Promise<CommandResult>;
  copyToClipboard: (text: string) => Promise<void>;
  onExternalChange: (cb: (event: ExternalChangeEvent) => void) => () => void;
  onBackupStatus: (cb: (status: BackupStatus) => void) => () => void;
}
