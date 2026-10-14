# LabelCheck

Standalone alcohol label verification prototype for the Treasury take-home exercise.

## Run locally

Requires Python 3 to serve static files, and Node 18+ for tests. No API keys or npm install required for the app.

```sh
python3 -m http.server 8000 --directory docs
# Open http://localhost:8000
node --test tests/*.test.mjs
```

## Review workflow

Upload PNG, JPEG or WebP labels (15 MB each). Select a label and enter its application details. Run selected OCR or review the queue. Each label retains separate application values. For batches, upload the images then import a JSON array matching exact filenames; see docs/batch-example.json. Sample matching and mismatched PNG labels run through the same real OCR pipeline as user images. Review warning typography against the image and record confirmation. Export results as JSON before closing the page. Input values update existing comparisons immediately without rerunning OCR.

## Engineering approach

Buildless HTML/CSS/ES modules; Tesseract.js 6.0.1 with Tesseract.js-core 6.0.0 and bundled English LSTM data. All recognition and comparison happen in a browser Web Worker; images and application values are never uploaded to an OCR API. Worker, WASM and language data are served from the same origin to avoid third-party runtime endpoint dependencies. The browser caches English language data; no review records are persisted.

Local neural OCR extracts text. Deterministic rules compare expected values. Brand/type/producer/origin checks require expected token sequences, tolerating case and punctuation differences, but do not infer regulatory field positions. ABV compares numeric percentages. Net contents accepts equivalent mL/L and US fluid-ounce quantities with 0.2% conversion tolerance. Warning text comparison ignores case and whitespace only, preserves wording and punctuation, and separately checks heading capitals. A confidence threshold of 75 routes otherwise matching readings to human review. Missing/unreadable values never silently pass. Display values for text fields reflect the matched application phrase; the full raw OCR reading is available for inspection. OCR confidence is heuristic, not a probability of compliance.

## Scope and limitations

- Target: approximately five seconds per label. Initial engine loading and slow devices may exceed it; this is not guaranteed. The UI reports per-image OCR/comparison timing separately from total queue time including engine initialization.
- Warning boldness, non-bold body, separate continuous paragraph and physical type size require visual review. The prototype does not automate font-style checks. A human confirmation is explicitly marked in the results.
- No complete category-specific regulatory engine: beverage category is recorded for reviewer context. All supplied fields are compared, and blank fields stay under review. ABV exceptions for wine/beer are not automatically determined.
- User can rotate images; there is no perspective correction or guaranteed glare/blur recovery. Unreadable values require review.
- Sequential batches reuse one worker to limit memory. No 200-300-item throughput guarantee. Large images are resized to at most 1900 pixels on the longest side; small print may become unreadable.
- Text-match presence does not prove field assignment or legal compliance. No automatic approvals or COLA integration.
- Browser refresh loses queue state. Export includes readings and application details, not images.
- Uploaded names and OCR readings are escaped or rendered as text. MIME and size checks are client-side; files are not accepted by a backend.
- Private Sites deployment is suitable for owner review. Reviewer access and a reviewer-accessible repository must be arranged before submitting the assignment.

## Source organization

- docs/index.html / style.css: responsive review interface.
- docs/app.mjs: queue, uploads, OCR worker, batch import/export and review controls.
- docs/verify.mjs: pure comparison logic.
- tests/verify.test.mjs: meaningful comparison regressions.
- docs/vendor: locally bundled OCR runtime/data and license notices.
- docs/samples: clean synthetic positive and ABV mismatch fixtures.

## Regulatory reference

TTB health warning guidance: https://www.ttb.gov/regulated-commodities/beverage-alcohol/distilled-spirits/ds-labeling-home/ds-health-warning (accessed October 13, 2026).

No claim of production authorization, official TTB affiliation, or comprehensive legal compliance.

## Verification performed

Nine comparison regression tests pass. Actual Tesseract OCR read both bundled PNGs at confidence 95: the matching fixture matched supplied fields and the ABV mismatch fixture flagged 40% versus 45%. Container timings were approximately 0.71s and 0.63s (1.58s total including initialization), not browser benchmarks. Browser visual/end-to-end QA was unavailable in this environment; deployment success does not establish browser compatibility or real-photo performance.
