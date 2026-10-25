# Reading-edition proof

Final PDF SHA-256: `17f4caeab0fcc0c3dc144f61e11880e72c502edbb0b9e68a368bb2df7911fffc`. Story source hashes and supporting build hashes are in `exports/build-manifest.json`.

The director inspected rendered PDF pages 1, 2, 34, 42, 49 and 50: cover, opening, reveal chapter, lantern-walk chapter, closing story page, and shared questions. Type, margins, headings, original vector decoration and page footers were clear; no clipping or overlap was observed on these pages. After the metadata-only rebuild, all six final rendered pages were compared pixel-for-pixel with the inspected renders and were identical.

`production/verify.py` checked the actual final PDF: exactly fifty 7 × 10 inch pages; all forty-eight story pages contain their full corresponding source page text, in order; no printed page-break markers; title and shared questions present; assembled Markdown includes every story page. Fixed-size build bounds checks succeeded without text shrinking or cropping. The source-manuscript structural check also passed with zero errors. These are completeness/layout checks, not a claim of literary quality.

The separately assigned fresh reader advocate read all twelve source chapters in full and found no concrete revision required; see `reviews/full-reader.md`. The story is 7,464 words in twelve chapters. Source prose was not altered after that review. Final source hashes were checked against both the reader report and build inventory.

Limits: only the six listed pages received visual inspection; all forty-eight story pages received extracted-text completeness checks. No human child/parent read-aloud test, independent copy-editing pass, print proof, or publication release certification was performed. Nothing was published, uploaded, sent or committed.
