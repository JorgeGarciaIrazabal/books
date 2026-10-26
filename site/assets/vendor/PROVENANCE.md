# Vendored reader libraries

The browser reader on this site renders EPUB books entirely on the visitor's
device. To avoid any runtime CDN or third-party request, the reader libraries
are vendored here, pinned to the exact versions below.

| File | Package | Version | License | Upstream source |
| --- | --- | --- | --- | --- |
| epub.min.js | EPUB.js | 0.3.93 | FreeBSD (BSD 2-Clause), full text in LICENSE-epubjs.txt | https://cdn.jsdelivr.net/npm/epubjs@0.3.93/dist/epub.min.js |
| jszip.min.js | JSZip | 3.10.1 | MIT or GPLv3 dual license, full text in LICENSE-jszip.txt | https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js |

EPUB.js requires JSZip to be included first when opening archived `.epub`
files, so reader.html loads `jszip.min.js` before `epub.min.js`.

## Integrity (sha256)

epub.min.js: 06eae15745107b4aa508c95538275251f69bfb9f1175621fc458d9f42ed082d4
jszip.min.js: acc7e41455a80765b5fd9c7ee1b8078a6d160bbbca455aeae854de65c947d59e

The automated checks in tests/test_catalog.py verify these checksums on every
build, so a changed library file fails the build until PROVENANCE.md and the
review are updated together.