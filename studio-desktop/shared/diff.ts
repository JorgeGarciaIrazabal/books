export interface DiffToken {
  type: "same" | "ins" | "del";
  text: string;
}

function pushToken(out: DiffToken[], type: DiffToken["type"], text: string) {
  if (!text) return;
  const last = out[out.length - 1];
  if (last && last.type === type) {
    last.text += text;
  } else {
    out.push({ type, text });
  }
}

/**
 * Word-level Myers/LCS diff for readable prose change inspection.
 */
export function diffWords(oldText: string, newText: string): DiffToken[] {
  if (oldText === newText) return [{ type: "same", text: newText }];
  if (!oldText) return [{ type: "ins", text: newText }];
  if (!newText) return [{ type: "del", text: oldText }];

  const a = oldText.split(/(\s+)/);
  const b = newText.split(/(\s+)/);

  // Trim identical leading/trailing tokens so long paragraphs stay O(delta^2)
  let pre = 0;
  while (pre < a.length && pre < b.length && a[pre] === b[pre]) pre++;
  let aEnd = a.length;
  let bEnd = b.length;
  while (aEnd > pre && bEnd > pre && a[aEnd - 1] === b[bEnd - 1]) {
    aEnd--;
    bEnd--;
  }

  const aMid = a.slice(pre, aEnd);
  const bMid = b.slice(pre, bEnd);
  const n = aMid.length;
  const m = bMid.length;

  const out: DiffToken[] = [];
  if (pre > 0) pushToken(out, "same", a.slice(0, pre).join(""));

  if (n * m <= 60000) {
    const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        dp[i][j] =
          aMid[i] === bMid[j] ? 1 + dp[i + 1][j + 1] : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
    let i = 0;
    let j = 0;
    while (i < n && j < m) {
      if (aMid[i] === bMid[j]) {
        pushToken(out, "same", aMid[i]);
        i++;
        j++;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        pushToken(out, "del", aMid[i++]);
      } else {
        pushToken(out, "ins", bMid[j++]);
      }
    }
    while (i < n) pushToken(out, "del", aMid[i++]);
    while (j < m) pushToken(out, "ins", bMid[j++]);
  } else {
    pushToken(out, "del", aMid.join(""));
    pushToken(out, "ins", bMid.join(""));
  }

  if (aEnd < a.length) pushToken(out, "same", a.slice(aEnd).join(""));
  return out;
}
