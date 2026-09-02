# Ingester

The ingester converts raw source material into structured text that the digester can process. It handles any non-text format: audio, video, ebooks, scanned documents, PDFs. The digester does not need to know what format a record originated from - it receives structured text with metadata regardless.

## Source material and copyright

The ingester processes source material whose copyright status varies - some public domain or openly licensed, some copyrighted. Original text, audio, and video are not stored in the knowledge graph (a structured database of interconnected facts) or published on the site; only extracted claims with source attribution appear in that output. Access to an ingested record itself is gated by its copyright status: openly-available material is served freely through the workbench, copyrighted material only to someone who proves possession of the original. Anomalica is not a redistribution channel for copyrighted works.

This is analogous to academic referencing. A researcher reads sources, extracts facts, cites them, and writes new work. The facts themselves are not copyrightable - the specific expression an author uses is, but an atomic factual claim ("radar contact was maintained for 12 minutes") is a fact, not expression. The assembled articles are new works that cite their sources, not reproductions or derivatives of the source material.

## Input formats

| Format | Approach |
|--------|----------|
| Audio/video (YouTube, podcasts) | Download, transcribe, diarise, identify speakers |
| EPUB (ebooks) | Extract text directly (EPUB is zipped HTML) |
| MOBI/AZW3 (Kindle) | Convert to EPUB via Calibre, then extract text |
| PDF (born-digital or scanned) | Send to vision-capable artificial intelligence model for comprehension-based extraction |
| Web pages, news articles | Scrape and extract text |
| Plain text, markdown | Pass through with metadata |

## Audio/video pipeline

```
audio/video source -> download -> transcription -> speaker diarisation -> speaker identification -> structured transcript
```

### Download

Source material is fetched from its origin. For YouTube videos and podcasts, tools like yt-dlp and podcast RSS feed parsers handle retrieval. The raw audio/video is stored alongside metadata (URL, date, title, channel/feed).

### Transcription with timestamps

Speech is converted to text with word-level timestamps. This enables precise linking from claims back to specific moments in the source material.

### Speaker diarisation

The transcript is segmented by speaker. Diarisation identifies when speakers change but does not identify *who* they are - it produces labels like "Speaker A" and "Speaker B."

### Speaker identification

Speaker embeddings (voice fingerprints) are compared against a database of known voice profiles. When a match is found, the generic speaker label is replaced with the identified person. This enables automatic attribution across recordings - once a voice is identified in one episode, it is recognised in all future recordings.

New voices that do not match any known profile are flagged for manual identification. Once identified, their voice profile is added to the database.

## Output

Regardless of input format, the ingester produces a markdown file with YAML (a human-readable metadata format) annotations following the [record format specification](ingest-format.md). See [architecture decision record 0019](../decisions/0019-record-interchange-format.md) for why this format was chosen over alternatives including DoclingDocument.

Each output record contains:

- YAML frontmatter with document metadata (title, date, source type, source URL, content hash)
- Content as markdown text
- Block annotations (YAML fenced with `---`) for structural markers: page boundaries, speaker turns, images, redactions
- Inline annotations (`{{YAML}}`) for mid-sentence markers: redactions, illegible text, actions

For audio/video specifically, the frontmatter includes a speaker roster and the content uses speaker turn annotations with timestamps. For documents, page boundary annotations mark where each page begins.

### Re-extraction: refresh in place

A record's extraction generation is `processing.pipeline_version`, a per-media-type integer the ingester bumps when extraction output changes enough to warrant re-processing existing records ([decision 0040](../decisions/0040-pipeline-versioning-and-supersession.md)). A record declaring a lower generation than the current one for its type is stale.

Re-processing an archived source goes through the normal entry point - `./ingest --force --source-url URL records/{hash}.{ext}` - which is what the scheduler's reprocess lane drives. For a web page or an EPUB whose archived bytes already have a live record, the handler refreshes that record **in place** under its existing identity rather than minting a second record; a PDF record's path already is its source hash, so its re-extraction was always in place. In every case the human's work carries over (`shared/refresh.py`): stored media files, a reviewer's `irrelevant` regions and inline highlight, note, link and citation markers are re-placed around the same prose, and a reviewed record gains a `review_carryover` stamp so the workbench asks for a look rather than showing it as reviewed. A refresh that would lose prose refuses, leaves the record untouched, fails the run and writes a `refresh_refused` block (when, why) into the record's frontmatter so the reviewer sees it: no loss at all is tolerated on a reviewed record (a dateline, byline or title heading the frontmatter carries does not count), and only a footer's worth on an unreviewed one. Nobody runs a tool to bring the corpus up to date; the scheduler picks up stale web and ebook records on its own, and each run either refreshes or refuses visibly. PDF re-extraction is model-driven and stays behind the spend gate.

The current generation per type is the registry in `shared/pipeline_version.py`, published to the store as `store/_pipeline_versions.yaml`; each bump's reason is recorded beside its number there. As of 2026-09-02: web 6 (emphasis unwrapped before extraction so records carry no bold or italic; dropped pictures placed by the block of text that follows them; recirculation widgets stripped) and ebook 5 (printed chapter numbers, drop-cap letters rejoined, footnotes resolved to markers, a notes document dropped only once its notes were pulled into the citing chapters).

### Image extraction

Images embedded in the source are extracted alongside the record. EPUBs are supported today; PDF figure extraction and video keyframes will follow.

Each image is content-hashed and saved to `media/{record_hash}/{img_hash}.{ext}` in the ingests repository. The body annotation references the image by bare filename (`<!-- image: file: abc123.png alt: "..." -->`); the consumer resolves the full path from the record's location. See the [record format specification](ingest-format.md) for the exact annotation form and rationale.

Alt text from the source (`<img alt="">`) is preserved when present. A factual `description` is added later by a vision pass or human review, not at ingestion time.

For web pages the text extractor drops some content images - above all an article's lead picture, which sits before any text and usually has neither alt nor caption. The handler harvests content-region images from the page itself and puts each dropped one back just before the text that followed it in the page (its caption, the next paragraph), folding a caption the extractor left as loose prose into the annotation; a lead picture heads the body. An image whose surrounding text the extractor rejected (a donate banner's, a related-posts strip's) is rejected with it, and icons, avatars and tracking pixels are filtered by their declared size.

## Tooling

### Audio/video

| Stage | Tool | Notes |
|-------|------|-------|
| Transcription | WhisperX 3.8+ with Whisper Large V3 Turbo | WhisperX wraps faster-whisper for transcription, wav2vec2 for word-level timestamp alignment, and pyannote for diarisation. Whisper Large V3 Turbo (809M params) is the practical sweet spot: 99+ languages, 6x faster than Large V3, ~6 GB of GPU memory |
| Diarisation | pyannote community-1 (pyannote.audio 4.0) | Replaces pyannote 3.1. Uses VBx clustering and WeSpeaker embeddings. Improved accuracy across all benchmarks. CC-BY-4.0 licence |
| Speaker identification | WeSpeaker ECAPA-TDNN embeddings + cosine similarity | pyannote community-1 uses WeSpeaker internally, so we reuse the same embeddings for speaker identification. Matches are suggestions requiring human confirmation |
| Download | yt-dlp, podcast RSS parsers | Handles YouTube, podcast feeds, and other sources |

### Documents

| Stage | Tool | Notes |
|-------|------|-------|
| PDF extraction | GPT-5.6 Luna vision (metered, gated) | Pages are rendered to images and sent to the vision model for comprehension-based text extraction. Handles both born-digital and scanned PDFs in a single pipeline. Avoids the layout-mangling problems of raw text extraction (pdftotext) and the structural errors of character-level optical character recognition (Tesseract) |
| Ebook conversion | Calibre | Converts between ebook formats, open source |
| Web scraping | trafilatura | Extracts article text and metadata from HTML. Fetch chain (HTTP, Wayback Machine, Patchright) handled by the acquire layer |

Self-hosted open source tooling is preferred for independence and cost control. AI-based extraction is the exception - it calls an external application programming interface.

### Model default and the spend gate

Any ingestion path that does **not** run the local Whisper model defaults to `openai/gpt-5.6-luna` (via OpenRouter) rather than the Claude subscription - a deliberate, recorded exception to the project's subscription-default rule (see the operating rules in the meta-repo `CLAUDE.md`), because subscription vision is worse and dearer for scanned documents and Luna is watermark-free. Today that means PDF only: audio/video transcribe with the local Whisper model (no metered spend), and web/ebook extraction is rule-based and calls no model. A future ebook or web AI path inherits this default rather than re-opening the question.

Because that default is metered, PDF ingestion runs behind a strict pre-flight spend gate: it prints a page-based cost estimate and refuses unless the run is explicitly confirmed (`--confirm-spend` / `INGEST_SPEND_CONFIRMED=1`). Nothing auto-approves - `INGEST_SPEND_CEILING_USD` defaults to `0.00`, and that default is part of the decision, not a tunable: a non-zero ceiling is an operator's deliberate choice to let small per-doc runs proceed unattended, and even then it bounds **one** run, never a batch. Aggregate (batch) approval is the scheduler's responsibility. `INGEST_USE_API=0` forces the unmetered subscription path. The OpenRouter account balance is the final hard cap.

## Deep linking

Claims extracted from audio/video records carry timestamp metadata. When a claim appears in an assembled article, the source link points to the specific moment in the recording:

- YouTube: `https://youtube.com/watch?v=VIDEO_ID&t=SECONDS`
- Podcast players that support chapter markers or timestamp URLs

A reader can click a source citation and hear the exact words that the claim was extracted from.

For documents, claims link to page numbers or section references where available.
