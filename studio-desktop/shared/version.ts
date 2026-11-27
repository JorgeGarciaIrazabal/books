export function parseReleaseVersion(raw: string): [number, number, number] | null {
  const cleaned = String(raw || "")
    .trim()
    .replace(/^desktop-v/i, "")
    .replace(/^v/i, "")
    .split("-")[0];
  const match = cleaned.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) return null;
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

export function formatReleaseVersion(raw: string): string {
  const parsed = parseReleaseVersion(raw);
  return parsed ? `${parsed[0]}.${parsed[1]}.${parsed[2]}` : raw.trim();
}

export function isNewerVersion(candidate: string, current: string): boolean {
  const candParts = parseReleaseVersion(candidate);
  const currParts = parseReleaseVersion(current);
  if (!candParts || !currParts) return false;
  for (let i = 0; i < 3; i += 1) {
    if (candParts[i] !== currParts[i]) {
      return candParts[i] > currParts[i];
    }
  }
  return false;
}

export function extractBaseUrlFromText(text: string): string | null {
  const match = String(text || "").match(/https?:\/\/[^\s"'<>]+/);
  if (!match) return null;
  return match[0].replace(/[.,;)]+$/, "").replace(/\/+$/, "");
}

export function githubPagesUrlFromRemote(remoteUrl: string): string | null {
  const raw = String(remoteUrl || "").trim();
  let match = raw.match(/^https?:\/\/github\.com\/([^/]+)\/(.+?)(?:\.git)?\/?$/i);
  if (!match) {
    match = raw.match(/^git@github\.com:([^/]+)\/(.+?)(?:\.git)?$/i);
  }
  if (!match) return null;
  const owner = match[1];
  const repo = match[2];
  return `https://${owner}.github.io/${repo}`;
}

export function resolvePublishedBookUrls(
  baseUrl: string | null,
  bookId: string,
  isPublicEdition: boolean,
  audiobookHref?: string | null
): {
  libraryUrl: string | null;
  readerUrl: string | null;
  audiobookUrl: string | null;
} {
  if (!baseUrl) {
    return { libraryUrl: null, readerUrl: null, audiobookUrl: null };
  }
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const libraryUrl = `${normalizedBase}/`;
  if (!isPublicEdition) {
    return { libraryUrl, readerUrl: null, audiobookUrl: null };
  }
  const encodedId = encodeURIComponent(bookId);
  const readerUrl = `${normalizedBase}/reader.html?book=${encodedId}`;
  const cleanAudioHref = audiobookHref ? audiobookHref.replace(/^\/+/, "") : null;
  const audiobookUrl = cleanAudioHref ? `${normalizedBase}/${cleanAudioHref}` : null;
  return { libraryUrl, readerUrl, audiobookUrl };
}
