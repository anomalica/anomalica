# Ingester

The ingester converts raw source material into structured text that the digester can process. It handles any non-text format: audio, video, ebooks, scanned documents, PDFs. The digester does not need to know what format a record originated from - it receives structured text with metadata regardless.

## Source material and copyright

The ingester processes privately acquired source material. Original text, audio, and video are not stored in the knowledge graph, published on the site, or made available to users. Only extracted claims with source attribution appear in the output.

This is analogous to academic referencing. A researcher reads sources, extracts facts, cites them, and writes new work. The facts themselves are not copyrightable - the specific expression an author uses is, but an atomic factual claim ("radar contact was maintained for 12 minutes") is a fact, not expression. The assembled articles are new works that cite their sources, not reproductions or derivatives of the source material.

## Input formats

| Format | Approach |
|--------|----------|
| Audio/video (YouTube, podcasts) | Download, transcribe, diarise, identify speakers |
| EPUB (ebooks) | Extract text directly (EPUB is zipped HTML) |
| MOBI/AZW3 (Kindle) | Convert to EPUB via Calibre, then extract text |
| PDF (born-digital or scanned) | Send to vision-capable AI model for comprehension-based extraction |
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

Regardless of input format, the ingester produces a markdown file with YAML annotations following the [record format specification](record-format.md). See [ADR 0012](../decisions/0012-record-interchange-format.md) for why this format was chosen over alternatives including DoclingDocument.

Each output record contains:

- YAML frontmatter with document metadata (title, date, source type, source URL, content hash)
- Content as markdown text
- Block annotations (YAML fenced with `---`) for structural markers: page boundaries, speaker turns, images, redactions
- Inline annotations (`{{YAML}}`) for mid-sentence markers: redactions, illegible text, actions

For audio/video specifically, the frontmatter includes a speaker roster and the content uses speaker turn annotations with timestamps. For documents, page boundary annotations mark where each page begins.

## Tooling

### Audio/video

| Stage | Tool | Notes |
|-------|------|-------|
| Transcription | WhisperX 3.8+ with Whisper Large V3 Turbo | WhisperX wraps faster-whisper for transcription, wav2vec2 for word-level timestamp alignment, and pyannote for diarisation. Whisper Large V3 Turbo (809M params) is the practical sweet spot: 99+ languages, 6x faster than Large V3, ~6 GB VRAM |
| Diarisation | pyannote community-1 (pyannote.audio 4.0) | Replaces pyannote 3.1. Uses VBx clustering and WeSpeaker embeddings. Improved accuracy across all benchmarks. CC-BY-4.0 licence |
| Speaker identification | WeSpeaker ECAPA-TDNN embeddings + cosine similarity | pyannote community-1 uses WeSpeaker internally, so we reuse the same embeddings for speaker identification. Matches are suggestions requiring human confirmation |
| Download | yt-dlp, podcast RSS parsers | Handles YouTube, podcast feeds, and other sources |

### Documents

| Stage | Tool | Notes |
|-------|------|-------|
| PDF extraction | Vision-capable AI model | PDFs sent directly to a vision model for comprehension-based text extraction. Handles both born-digital and scanned PDFs in a single pipeline. Avoids the layout-mangling problems of raw text extraction (pdftotext) and the structural errors of character-level OCR (Tesseract) |
| Ebook conversion | Calibre | Converts between ebook formats, open source |
| Web scraping | trafilatura | Extracts article text and metadata from HTML. Fetch chain (HTTP, Wayback Machine, Patchright) handled by the acquire layer |

Self-hosted open source tooling is preferred for independence and cost control. The vision model for PDF extraction is the exception - it calls an external API.

## Deep linking

Claims extracted from audio/video records carry timestamp metadata. When a claim appears in an assembled article, the source link points to the specific moment in the recording:

- YouTube: `https://youtube.com/watch?v=VIDEO_ID&t=SECONDS`
- Podcast players that support chapter markers or timestamp URLs

A reader can click a source citation and hear the exact words that the claim was extracted from.

For documents, claims link to page numbers or section references where available.
