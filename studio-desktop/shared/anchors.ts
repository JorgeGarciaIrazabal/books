import type { CommentRecord } from "./types";
import { splitChapterMarkdown } from "./markdown";

export interface ProjectedRange {
  start: number;
  end: number;
  quote: string;
  orphaned: boolean;
}

export interface OccurrenceStats {
  paragraphNum: number;
  occurrence: number | null;
  totalOccurrences: number;
}

/**
 * Character-level LCS projection with common prefix/suffix trimming.
 * Automatically shifts and updates a comment range even when text inside the span is rewritten.
 */
export function projectRangeThroughDiff(
  oldText: string,
  newText: string,
  start: number,
  end: number
): ProjectedRange {
  if (oldText === newText) {
    const s = Math.max(0, Math.min(newText.length, start));
    const e = Math.max(s, Math.min(newText.length, end));
    const quote = newText.slice(s, e);
    return { start: s, end: e, quote, orphaned: quote.trim().length === 0 };
  }

  let pre = 0;
  const minLen = Math.min(oldText.length, newText.length);
  while (pre < minLen && oldText[pre] === newText[pre]) pre++;

  let oldEnd = oldText.length;
  let newEnd = newText.length;
  while (oldEnd > pre && newEnd > pre && oldText[oldEnd - 1] === newText[newEnd - 1]) {
    oldEnd--;
    newEnd--;
  }

  const oldMid = oldText.slice(pre, oldEnd);
  const newMid = newText.slice(pre, newEnd);
  const n = oldMid.length;
  const m = newMid.length;

  const mapIdx = new Int32Array(oldText.length + 1);
  for (let k = 0; k <= pre; k++) mapIdx[k] = k;

  if (n * m <= 90000) {
    const dp = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        dp[i][j] =
          oldMid[i] === newMid[j] ? 1 + dp[i + 1][j + 1] : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
    let i = 0;
    let j = 0;
    while (i < n && j < m) {
      if (oldMid[i] === newMid[j]) {
        mapIdx[pre + i] = pre + j;
        i++;
        j++;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        mapIdx[pre + i] = pre + j;
        i++;
      } else {
        j++;
      }
    }
    while (i <= n) {
      mapIdx[pre + i] = pre + m;
      i++;
    }
  } else {
    for (let i = 0; i <= n; i++) {
      mapIdx[pre + i] = pre + Math.min(m, Math.round((i / Math.max(1, n)) * m));
    }
  }

  const deltaAfter = newText.length - oldText.length;
  for (let k = oldEnd; k <= oldText.length; k++) mapIdx[k] = k + deltaAfter;

  const clampedStart = Math.max(0, Math.min(oldText.length, start));
  const clampedEnd = Math.max(clampedStart, Math.min(oldText.length, end));
  const projStart = Math.max(0, Math.min(newText.length, mapIdx[clampedStart]));
  let projEnd = Math.max(projStart, Math.min(newText.length, mapIdx[clampedEnd]));

  if (clampedStart >= pre && clampedEnd <= oldEnd && projStart === projEnd && newMid.length > 0) {
    const wordStart = Math.max(pre, projStart);
    const wordEnd = Math.min(newEnd, wordStart + newMid.length);
    projEnd = Math.max(projStart, wordEnd);
  }

  const quote = newText.slice(projStart, projEnd);
  return {
    start: projStart,
    end: projEnd,
    quote,
    orphaned: quote.trim().length === 0
  };
}

/**
 * Computes which occurrence (#k of N) a comment sits on within the chapter.
 */
export function computeOccurrenceStats(
  blocks: string[],
  blockIndex: number | undefined,
  startOffset: number | undefined,
  quote: string
): OccurrenceStats {
  const pNum = typeof blockIndex === "number" && blockIndex >= 0 ? blockIndex + 1 : 1;
  if (!quote) return { paragraphNum: pNum, occurrence: null, totalOccurrences: 0 };

  let total = 0;
  let occ: number | null = null;
  blocks.forEach((blk, idx) => {
    let from = 0;
    while (true) {
      const found = blk.indexOf(quote, from);
      if (found === -1) break;
      total++;
      if (idx === blockIndex && found === startOffset) {
        occ = total;
      }
      from = found + Math.max(1, quote.length);
    }
  });
  return { paragraphNum: pNum, occurrence: occ, totalOccurrences: total };
}

function suffixPrefixOverlap(a: string | undefined, b: string): number {
  if (!a || !b) return 0;
  const tailA = a.slice(-24);
  const tailB = b.slice(-24);
  let matches = 0;
  const minLen = Math.min(tailA.length, tailB.length);
  const denom = Math.max(8, Math.max(tailA.length, tailB.length));
  for (let i = 1; i <= minLen; i++) {
    if (tailA[tailA.length - i] === tailB[tailB.length - i]) matches++;
  }
  return matches / denom;
}

function prefixOverlap(a: string | undefined, b: string): number {
  if (!a || !b) return 0;
  const headA = a.slice(0, 24);
  const headB = b.slice(0, 24);
  let matches = 0;
  const minLen = Math.min(headA.length, headB.length);
  const denom = Math.max(8, Math.max(headA.length, headB.length));
  for (let i = 0; i < minLen; i++) {
    if (headA[i] === headB[i]) matches++;
  }
  return matches / denom;
}

/**
 * 4-Tier Re-Anchoring Waterfall for external disk edits & file reloads:
 *   Tier 1: Exact offset + blockIndex fast path
 *   Tier 2: Disambiguated context scoring across duplicate occurrences
 *   Tier 3: Diff-projection from prior snapshot (survives rewrites inside the span)
 *   Tier 4: Graceful block-pinned orphan fallback (preserves originalQuote)
 */
export function reanchorMarkdownComment(
  comment: CommentRecord,
  oldMarkdown: string | null,
  newMarkdown: string,
  newSha256: string
): CommentRecord {
  if (comment.target.kind !== "markdown") return comment;

  const { blocks } = splitChapterMarkdown(newMarkdown);
  const a = comment.anchor;
  const quote = a.quote || a.originalQuote;
  if (!quote) return comment;

  // Tier 1: Exact blockIndex + startOffset + endOffset fast path
  if (
    typeof a.blockIndex === "number" &&
    typeof a.startOffset === "number" &&
    typeof a.endOffset === "number" &&
    blocks[a.blockIndex] !== undefined
  ) {
    const exact = blocks[a.blockIndex].slice(a.startOffset, a.endOffset);
    if (exact === quote) {
      const stats = computeOccurrenceStats(blocks, a.blockIndex, a.startOffset, quote);
      return {
        ...comment,
        anchor: {
          ...a,
          occurrence: stats.occurrence ?? a.occurrence,
          fileSha256: newSha256,
          orphaned: false
        }
      };
    }
  }

  // Tier 2: Disambiguated context scoring across all matching occurrences
  interface Candidate {
    blockIndex: number;
    startOffset: number;
    endOffset: number;
    occurrence: number;
    ctxScore: number;
    score: number;
  }
  const candidates: Candidate[] = [];
  let occCounter = 0;
  blocks.forEach((blk, bIdx) => {
    let from = 0;
    while (true) {
      const idx = blk.indexOf(quote, from);
      if (idx === -1) break;
      occCounter++;
      const endIdx = idx + quote.length;
      const candPrefix = blk.slice(Math.max(0, idx - 36), idx);
      const candSuffix = blk.slice(endIdx, Math.min(blk.length, endIdx + 36));

      const ctxScore =
        0.5 * suffixPrefixOverlap(a.prefix, candPrefix) +
        0.5 * prefixOverlap(a.suffix, candSuffix);
      const blockProx =
        typeof a.blockIndex === "number"
          ? 1 / (1 + Math.abs(bIdx - a.blockIndex))
          : 0.5;
      const offsetProx =
        typeof a.startOffset === "number"
          ? 1 / (1 + Math.abs(idx - a.startOffset) / 40)
          : 0.5;
      const occBonus = a.occurrence === occCounter ? 0.05 : 0;

      candidates.push({
        blockIndex: bIdx,
        startOffset: idx,
        endOffset: endIdx,
        occurrence: occCounter,
        ctxScore,
        score: 0.6 * ctxScore + 0.25 * blockProx + 0.15 * offsetProx + occBonus
      });
      from = idx + Math.max(1, quote.length);
    }
  });

  if (candidates.length > 0) {
    candidates.sort((x, y) => y.score - x.score);
    const best = candidates[0];
    // Do not jump a comment onto an unrelated duplicate phrase if context doesn't match and we can diff-project.
    const canDiffProject = Boolean(oldMarkdown && typeof a.blockIndex === "number");
    if (!canDiffProject || best.ctxScore >= 0.45) {
      const blk = blocks[best.blockIndex];
      return {
        ...comment,
        anchor: {
          ...a,
          blockIndex: best.blockIndex,
          startOffset: best.startOffset,
          endOffset: best.endOffset,
          occurrence: best.occurrence,
          prefix: blk.slice(Math.max(0, best.startOffset - 36), best.startOffset),
          suffix: blk.slice(best.endOffset, Math.min(blk.length, best.endOffset + 36)),
          fileSha256: newSha256,
          orphaned: false
        }
      };
    }
  }

  // Tier 3: Snapshot diff-projection when the commented text itself was rewritten externally
  if (oldMarkdown && typeof a.blockIndex === "number") {
    const oldBlocks = splitChapterMarkdown(oldMarkdown).blocks;
    const oldBlk = oldBlocks[a.blockIndex];
    const newBlk = blocks[Math.min(a.blockIndex, blocks.length - 1)];
    if (oldBlk !== undefined && newBlk !== undefined && typeof a.startOffset === "number" && typeof a.endOffset === "number") {
      const proj = projectRangeThroughDiff(oldBlk, newBlk, a.startOffset, a.endOffset);
      if (!proj.orphaned) {
        const targetIdx = Math.min(a.blockIndex, blocks.length - 1);
        const stats = computeOccurrenceStats(blocks, targetIdx, proj.start, proj.quote);
        return {
          ...comment,
          anchor: {
            ...a,
            blockIndex: targetIdx,
            startOffset: proj.start,
            endOffset: proj.end,
            quote: proj.quote,
            occurrence: stats.occurrence ?? undefined,
            prefix: newBlk.slice(Math.max(0, proj.start - 36), proj.start),
            suffix: newBlk.slice(proj.end, Math.min(newBlk.length, proj.end + 36)),
            fileSha256: newSha256,
            autoUpdated: proj.quote !== a.originalQuote,
            orphaned: false
          }
        };
      }
    }
  }

  // Tier 4: Graceful block-pinned orphan fallback (never silently dropped)
  return {
    ...comment,
    anchor: {
      ...a,
      fileSha256: newSha256,
      orphaned: true
    }
  };
}
