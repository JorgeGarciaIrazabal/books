import { describe, expect, it } from "vitest";
import {
  extractBaseUrlFromText,
  formatReleaseVersion,
  githubPagesUrlFromRemote,
  isNewerVersion,
  parseReleaseVersion,
  resolvePublishedBookUrls
} from "../shared/version";

describe("version parsing and release comparison", () => {
  it("parses release tags with optional prefixes", () => {
    expect(parseReleaseVersion("0.1.1")).toEqual([0, 1, 1]);
    expect(parseReleaseVersion("v0.1.2")).toEqual([0, 1, 2]);
    expect(parseReleaseVersion("desktop-v1.4.9")).toEqual([1, 4, 9]);
    expect(parseReleaseVersion("invalid")).toBeNull();
    expect(formatReleaseVersion("desktop-v0.1.2")).toBe("0.1.2");
  });

  it("compares semantic versions correctly", () => {
    expect(isNewerVersion("desktop-v0.1.2", "0.1.1")).toBe(true);
    expect(isNewerVersion("v0.2.0", "0.1.9")).toBe(true);
    expect(isNewerVersion("1.0.0", "0.9.9")).toBe(true);
    expect(isNewerVersion("desktop-v0.1.1", "0.1.1")).toBe(false);
    expect(isNewerVersion("0.1.0", "0.1.1")).toBe(false);
  });
});

describe("published GitHub Pages URL resolution", () => {
  it("extracts base URLs from manifest descriptions and git remotes", () => {
    expect(
      extractBaseUrlFromText(
        "Public library published at https://JorgeGarciaIrazabal.github.io/books/."
      )
    ).toBe("https://JorgeGarciaIrazabal.github.io/books");
    expect(
      githubPagesUrlFromRemote("https://github.com/JorgeGarciaIrazabal/books.git")
    ).toBe("https://JorgeGarciaIrazabal.github.io/books");
    expect(githubPagesUrlFromRemote("git@github.com:JorgeGarciaIrazabal/books.git")).toBe(
      "https://JorgeGarciaIrazabal.github.io/books"
    );
  });

  it("builds reader and audiobook URLs only for published books", () => {
    expect(
      resolvePublishedBookUrls(
        "https://JorgeGarciaIrazabal.github.io/books/",
        "the-hot-potato-of-corporate-castle",
        true,
        "audiobook-the-hot-potato-of-corporate-castle.html"
      )
    ).toEqual({
      libraryUrl: "https://JorgeGarciaIrazabal.github.io/books/",
      readerUrl:
        "https://JorgeGarciaIrazabal.github.io/books/reader.html?book=the-hot-potato-of-corporate-castle",
      audiobookUrl:
        "https://JorgeGarciaIrazabal.github.io/books/audiobook-the-hot-potato-of-corporate-castle.html"
    });

    expect(
      resolvePublishedBookUrls(
        "https://JorgeGarciaIrazabal.github.io/books",
        "the-ninth-lock",
        false
      )
    ).toEqual({
      libraryUrl: "https://JorgeGarciaIrazabal.github.io/books/",
      readerUrl: null,
      audiobookUrl: null
    });
  });
});
