export interface ParsedChapterMarkdown {
  title: string;
  bodyMarkdown: string;
  blocks: string[];
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Strip inline Markdown markers to obtain the exact plain text visible inside a ProseMirror block.
 */
export function markdownInlineToPlainText(line: string): string {
  return line
    .replace(/^#{1,6}\s+/, "")
    .replace(/^>\s+/, "")
    .replace(/\*\*\*(.+?)\*\*\*/g, "$1")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/_(.+?)_/g, "$1")
    .replace(/`(.+?)`/g, "$1");
}

function inlineMarkdownToHtml(text: string): string {
  let html = escapeHtml(text);
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/(^|[^*])\*([^*]+?)\*(?!\*)/g, "$1<em>$2</em>");
  html = html.replace(/(^|\s)_([^_]+?)_(?=\s|$|[.,!?;:'"”’])/g, "$1<em>$2</em>");
  return html;
}

export function splitChapterMarkdown(rawMarkdown: string): ParsedChapterMarkdown {
  const normalized = rawMarkdown.replace(/\r\n/g, "\n");
  const lines = normalized.split("\n");
  let title = "";
  let bodyStart = 0;

  while (bodyStart < lines.length && lines[bodyStart].trim() === "") {
    bodyStart++;
  }
  if (bodyStart < lines.length && lines[bodyStart].startsWith("# ")) {
    title = lines[bodyStart].slice(2).trim();
    bodyStart++;
    while (bodyStart < lines.length && lines[bodyStart].trim() === "") {
      bodyStart++;
    }
  }

  const bodyMarkdown = lines.slice(bodyStart).join("\n").trimEnd();
  const blocks = extractBodyBlocks(bodyMarkdown);
  return { title, bodyMarkdown, blocks };
}

export function extractBodyBlocks(bodyMarkdown: string): string[] {
  if (!bodyMarkdown.trim()) return [""];
  const rawBlocks = bodyMarkdown.split(/\n{2,}/);
  const blocks: string[] = [];
  for (const raw of rawBlocks) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      blocks.push("");
      continue;
    }
    blocks.push(markdownInlineToPlainText(trimmed.replace(/\n/g, " ")));
  }
  return blocks.length ? blocks : [""];
}

export function bodyMarkdownToEditorHtml(bodyMarkdown: string): string {
  if (!bodyMarkdown.trim()) return "<p></p>";
  const rawBlocks = bodyMarkdown.split(/\n{2,}/);
  const htmlBlocks: string[] = [];
  for (const raw of rawBlocks) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      htmlBlocks.push("<hr />");
      continue;
    }
    if (trimmed.startsWith("### ")) {
      htmlBlocks.push(`<h3>${inlineMarkdownToHtml(trimmed.slice(4))}</h3>`);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      htmlBlocks.push(`<h2>${inlineMarkdownToHtml(trimmed.slice(3))}</h2>`);
      continue;
    }
    if (trimmed.startsWith("> ")) {
      const inner = trimmed
        .split("\n")
        .map((l) => inlineMarkdownToHtml(l.replace(/^>\s?/, "")))
        .join(" ");
      htmlBlocks.push(`<blockquote><p>${inner}</p></blockquote>`);
      continue;
    }
    htmlBlocks.push(`<p>${inlineMarkdownToHtml(trimmed.replace(/\n/g, " "))}</p>`);
  }
  return htmlBlocks.join("") || "<p></p>";
}

interface PMNodeLike {
  type?: string;
  attrs?: Record<string, unknown>;
  text?: string;
  marks?: Array<{ type?: string }>;
  content?: PMNodeLike[];
}

function serializeInline(nodes: PMNodeLike[] | undefined): string {
  if (!nodes) return "";
  return nodes
    .map((n) => {
      if (n.type === "hardBreak") return "\n";
      const text = n.text ?? "";
      if (!text) return "";
      const marks = new Set((n.marks ?? []).map((m) => m.type ?? ""));
      let out = text;
      const hasBold = marks.has("bold");
      const hasItalic = marks.has("italic");
      if (hasBold && hasItalic) out = `***${out}***`;
      else if (hasBold) out = `**${out}**`;
      else if (hasItalic) out = `*${out}*`;
      return out;
    })
    .join("");
}

/**
 * Lossless, craft-disciplined Markdown serialization from TipTap JSON.
 * Never injects em dashes, smart-quote rewrites, or comment markup.
 */
export function editorJsonToChapterMarkdown(title: string, doc: PMNodeLike): string {
  const sections: string[] = [];
  if (title.trim()) {
    sections.push(`# ${title.trim()}`);
  }
  for (const node of doc.content ?? []) {
    if (node.type === "horizontalRule") {
      sections.push("---");
    } else if (node.type === "heading") {
      const level = Math.min(6, Math.max(2, Number(node.attrs?.level ?? 2)));
      sections.push(`${"#".repeat(level)} ${serializeInline(node.content)}`);
    } else if (node.type === "blockquote") {
      const inner = (node.content ?? []).map((c) => `> ${serializeInline(c.content)}`).join("\n");
      sections.push(inner);
    } else if (node.type === "paragraph") {
      const line = serializeInline(node.content);
      sections.push(line);
    }
  }
  // Drop trailing blank paragraphs added only as editor tail
  while (sections.length > 1 && sections[sections.length - 1] === "") {
    sections.pop();
  }
  return sections.join("\n\n") + "\n";
}

export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}
