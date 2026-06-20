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

Regardless of input format, the ingester produces a markdown file with YAML (a human-readable metadata format) annotations following the [record format specification](record-format.md). See [architecture decision record 0019](../decisions/0019-record-interchange-format.md) for why this format was chosen over alternatives including DoclingDocument.

Each output record contains:

- YAML frontmatter with document metadata (title, date, source type, source URL, content hash)
- Content as markdown text
- Block annotations (YAML fenced with `---`) for structural markers: page boundaries, speaker turns, images, redactions
- Inline annotations (`{{YAML}}`) for mid-sentence markers: redactions, illegible text, actions

For audio/video specifically, the frontmatter includes a speaker roster and the content uses speaker turn annotations with timestamps. For documents, page boundary annotations mark where each page begins.

### Image extraction

Images embedded in the source are extracted alongside the record. EPUBs are supported today; PDF figure extraction and video keyframes will follow.

Each image is content-hashed and saved to `media/{record_hash}/{img_hash}.{ext}` in the ingests repository. The body annotation references the image by bare filename (`<!-- image: file: abc123.png alt: "..." -->`); the consumer resolves the full path from the record's location. See the [record format specification](record-format.md) for the exact annotation form and rationale.

Alt text from the source (`<img alt="">`) is preserved when present. A factual `description` is added later by a vision pass or human review, not at ingestion time.

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
| PDF extraction | Vision-capable artificial intelligence model | PDFs sent directly to a vision model for comprehension-based text extraction. Handles both born-digital and scanned PDFs in a single pipeline. Avoids the layout-mangling problems of raw text extraction (pdftotext) and the structural errors of character-level optical character recognition (Tesseract) |
| Ebook conversion | Calibre | Converts between ebook formats, open source |
| Web scraping | trafilatura | Extracts article text and metadata from HTML. Fetch chain (HTTP, Wayback Machine, Patchright) handled by the acquire layer |

Self-hosted open source tooling is preferred for independence and cost control. The vision model for PDF extraction is the exception - it calls an external application programming interface.

## Deep linking

Claims extracted from audio/video records carry timestamp metadata. When a claim appears in an assembled article, the source link points to the specific moment in the recording:

- YouTube: `https://youtube.com/watch?v=VIDEO_ID&t=SECONDS`
- Podcast players that support chapter markers or timestamp URLs

A reader can click a source citation and hear the exact words that the claim was extracted from.

For documents, claims link to page numbers or section references where available.
