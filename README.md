# Somali Duplex Dashboard

Somali Duplex is a Somali text-to-speech research and data pipeline. Its goal is
to build a model that learns Somali pronunciation, phrasing, prosody, and
natural speaker characteristics from authorised native Somali recordings paired
with accurate Somali transcripts.

This repository is a static HTML dashboard for exploring that work. Its charts use bundled Plotly.js and its samples use native HTML audio players. No application server, Docker runtime, or API is needed. The
dashboard is intended to make the corpus and training journey legible: what
audio has been collected, where it is in the processing pipeline, how much
verified material is available, and how model experiments perform.

## Project goal

The target is not English speech delivered with a Somali accent. It is a model
that can turn written Somali into clear, natural Somali speech. The project
uses a pretrained multilingual speech model as a starting point, then adapts
it with clean Somali speech and transcript pairs. A corpus of roughly 100
hours is a useful first target; larger, well-reviewed corpora support stronger
quality and broader voice coverage.

## End-to-end pipeline

```text
Authorised Somali recordings
          |
          v
Source collection and rights review
          |
          v
Silero VAD segmentation (20–30 second speech clips)
          |
          v
DeepFilterNet 3 denoising and loudness normalisation
          |
          v
Mono 24 kHz, 16-bit FLAC + metadata
          |
          v
Transcription, timestamp review, and speaker/quality checks
          |
          v
Optional punctuation recovery from real word pauses
          |
          v
Versioned train / development / test datasets
          |
          v
CosyVoice 3 fine-tuning and held-out evaluation
```

### 1. Collection and preparation

Recordings must be Somali-language material that the project is authorised to
process and train on. The preferred sources are clean, intelligible speech with
reliable transcripts: studio podcasts, narration, and formal broadcast speech
are useful complements when their speakers and usage rights are understood.

Raw recordings are segmented with Silero VAD, then processed in one local pass
with DeepFilterNet 3 and loudness normalisation. Final data is published as
mono, 24 kHz, 16-bit lossless FLAC clips with `metadata.json`. Temporary VAD
WAV files are discarded. The processing job skips already-complete sources and
refuses partial or conflicting output, protecting dataset integrity.

### 2. Transcripts and review

Each final clip needs a transcript that matches what was actually spoken. The
project can review transcript tasks in Label Studio, which serves source FLAC
files alongside the corresponding CosyVoice transcript data. Audio, text,
speaker attribution, and splits should be checked before a clip becomes
training data.

Timing information can also improve phrasing. The optional pause-alignment
workflow derives punctuation from real word timestamps without changing the
audio or rewriting Somali words. It uses normal punctuation such as commas,
periods, question marks, and ellipses—never unsupported pause tags—and stages
all edits for audit and human review before building a new dataset version.

### 3. Model adaptation

The planned base model is `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`. Somali text
tokenizes losslessly in its existing tokenizer, but that alone does not prove
Somali pronunciation quality. The model must learn Somali speech patterns from
the reviewed corpus.

The first fine-tuning experiment fully adapts CosyVoice's LLM and Flow
modules, while keeping the HiFT/HiFi-GAN vocoder frozen. This focuses training
on Somali text-to-speech mapping, timing, prosody, and acoustics while
preserving stable 24 kHz waveform synthesis. Training belongs on a Linux CUDA
machine; this Mac workspace is used for data work, inspection, and inference.

### 4. Evaluation and promotion

Every candidate model is compared with the base model on a held-out Somali
test set. Evaluation combines transcript fidelity, native-speaker
pronunciation review, naturalness and pause quality, speaker similarity, and
waveform checks for clipping, noise, or instability. A checkpoint is promoted
only when it improves Somali intelligibility without materially degrading voice
quality.

## Dashboard scope

The static dashboard is the reporting layer for Somali Duplex. As the data
products are connected, it can present collection and processing status,
duration and speaker coverage, transcription-review progress, dataset-version
comparisons, and evaluation results. It is deliberately separate from the
audio-processing and training jobs: the dashboard observes the pipeline rather
than modifying raw recordings or checkpoints.

### Omar dataset analysis

The corpus section reports a complete scan of the processed Omar transcript
tree: corpus hours, timed-word coverage, WPM distribution, low/medium/high pace
bands, pause statistics, source-level variation, technical FLAC compliance,
and the punctuation-normalization audit. Rebuild its checked analysis artifacts
with:

```bash
cd /Users/mali/ai/somali-duplex-plotly
.venv/bin/python scripts/analyze_omar_dataset.py
```

The analyzer writes one row per WPM-eligible clip to `data/omar_wpm.csv` and an
aggregate report to `data/omar_dataset_summary.json`. Audio-event-only JSON
records remain part of total corpus hours but are excluded from pace labeling.

## Static build and preview

```bash
python3 scripts/build_static.py
python3 -m http.server 8080 --directory dist
```

Open `http://localhost:8080`. The build uses only Python's standard library and
copies the HTML, CSS, JavaScript, chart data, and nine WAV samples into `dist/`.
Python serves only this optional local preview; GitHub Pages serves the published
files. All asset URLs are relative, so project URLs work under a repository path.
Plotly.js 3.1.0 is bundled locally under its MIT license; no CDN is needed.

## Publish on GitHub Pages

In the repository's **Settings → Pages**, choose **GitHub Actions** as the source.
The workflow in `.github/workflows/pages.yml` builds and deploys pushes to the active
`cosy-voice` branch; it can also be run manually. The resulting
URL for the existing remote is `https://alimaslax.github.io/somali-duplex-plotly/`.
Only `dist/` is uploaded, including the samples displayed on the dashboard.

## Edit the dashboard

- `index.html`: content and audio comparison table.
- `assets/dashboard.css`: dark report layout and responsive styles.
- `assets/dashboard.js`: lazy chart rendering and single-sample playback.
- `assets/charts.json`: precomputed Plotly figures containing the original analysis.
- `assets/audio/`: the nine reference samples.

Normal edits need only the static build. For a fresh analysis report, the optional
`scripts/refresh_static_report.py` exporter uses the preserved `research_page.py`
layout and checked `data/` artifacts; it requires the legacy Dash, pandas, and
Plotly packages. It overwrites the generated HTML, chart JSON, CSS, and bundled
Plotly.js, so apply content/style customizations afterward. The old Dash pages
and Docker files are retained as migration references and are not deployed.

## Related workspaces

- `/Users/mali/ai/sod-code` contains the collection, audio processing,
  transcript-review, and CosyVoice training documentation and scripts.
- `/Users/mali/ai/sod-audio` holds the private audio dataset and associated
  metadata.
- `/Users/mali/ai/CosyVoice` contains the local CosyVoice runtime and model
  assets used for inference and training experiments.

## License

This repository is licensed under the [MIT License](LICENSE).
