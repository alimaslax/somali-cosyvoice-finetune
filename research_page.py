from __future__ import annotations

import json
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html


ROOT = Path(__file__).resolve().parent
SUMMARY = json.loads((ROOT / "data" / "omar_dataset_summary.json").read_text(encoding="utf-8"))
CLIPS = pd.read_csv(ROOT / "data" / "omar_wpm.csv")

INK = "#e6e7eb"
MUTED = "#a7abb4"
GRID = "rgba(255,255,255,.12)"


def figure_style(figure: go.Figure, height: int) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 54, "r": 18, "t": 22, "b": 52},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": MUTED, "size": 12},
        hovermode=False,
        showlegend=False,
    )
    figure.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    figure.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return figure


def wpm_distribution() -> go.Figure:
    rates = SUMMARY["speaking_rate"]
    low, high = rates["low_boundary_wpm"], rates["high_boundary_wpm"]
    figure = go.Figure(go.Histogram(
        x=CLIPS["wpm"], xbins={"start": 0, "end": 250, "size": 5},
        marker={"color": "#93a5b1", "line": {"width": 0}},
        hovertemplate="%{x:.0f} WPM bin<br>%{y:,} clips<extra></extra>",
    ))
    figure.add_vrect(x0=0, x1=low, fillcolor="#7cc4cf", opacity=.12, line_width=0)
    figure.add_vrect(x0=low, x1=high, fillcolor="#b8c0c9", opacity=.10, line_width=0)
    figure.add_vrect(x0=high, x1=250, fillcolor="#edb27c", opacity=.12, line_width=0)
    for boundary, label, anchor in ((low, "LOW", "right"), (high, "HIGH", "left")):
        figure.add_vline(x=boundary, line_width=1.4, line_dash="dot", line_color="#d0d7dd")
        figure.add_annotation(x=boundary, y=1, yref="paper", text=label, showarrow=False,
                              yshift=14, xanchor=anchor,
                              font={"family": "SFMono-Regular, Consolas, monospace", "size": 10, "color": "#d0d7dd"})
    figure.update_xaxes(title="Overall speaking rate (words per minute)", range=[0, 250], dtick=25)
    figure.update_yaxes(title="Clips")
    return figure_style(figure, 410)


def duration_scatter() -> go.Figure:
    figure = go.Figure()
    colours = {"Low": "#9fcbd3", "Medium": "#b7bbc3", "High": "#e9b47e"}
    for tier in ("Low", "Medium", "High"):
        subset = CLIPS[CLIPS["wpm_tier"] == tier]
        figure.add_trace(go.Scattergl(
            x=subset["duration_seconds"], y=subset["wpm"], mode="markers", name=tier,
            marker={"size": 5, "color": colours[tier], "opacity": .48},
            customdata=subset[["word_count", "recording", "utterance"]],
            hovertemplate=(f"{tier} · %{{y:.1f}} WPM<br>%{{x:.1f}} sec · %{{customdata[0]}} words"
                           "<br>%{customdata[1]} / %{customdata[2]}<extra></extra>"),
        ))
    figure.add_vrect(x0=20, x1=30, fillcolor="#d6e0e5", opacity=.07, line_width=0)
    figure.update_layout(showlegend=True, legend={"orientation": "h", "y": 1.10, "x": 0})
    figure.update_xaxes(title="Clip duration (seconds)")
    figure.update_yaxes(title="Words per minute", range=[0, 260])
    return figure_style(figure, 390)


def source_range_plot() -> go.Figure:
    figure = go.Figure()
    recordings = []
    minimums = []
    first_quartiles = []
    medians = []
    third_quartiles = []
    maximums = []
    for item in SUMMARY["top_recordings_by_hours"][:10]:
        recording = item["recording"]
        values = CLIPS.loc[CLIPS["recording"] == recording, "wpm"]
        recordings.append(recording[:42] + ("…" if len(recording) > 42 else ""))
        minimums.append(values.min())
        first_quartiles.append(values.quantile(.25))
        medians.append(values.median())
        third_quartiles.append(values.quantile(.75))
        maximums.append(values.max())

    def range_coordinates(starts, ends):
        x, y = [], []
        for name, start, end in zip(recordings, starts, ends):
            x.extend([start, end, None])
            y.extend([name, name, None])
        return x, y

    full_x, full_y = range_coordinates(minimums, maximums)
    iqr_x, iqr_y = range_coordinates(first_quartiles, third_quartiles)
    figure.add_trace(go.Scatter(
        x=full_x, y=full_y, mode="lines", hoverinfo="skip",
        line={"color": "#65717a", "width": 2}, name="Observed range",
    ))
    figure.add_trace(go.Scatter(
        x=iqr_x, y=iqr_y, mode="lines", hoverinfo="skip",
        line={"color": "#8ebfc8", "width": 10}, name="Middle 50%",
    ))
    figure.add_trace(go.Scatter(
        x=medians, y=recordings, mode="markers", hoverinfo="skip",
        marker={"color": "#f0f1f3", "size": 8, "line": {"color": "#16171a", "width": 2}},
        name="Median",
    ))
    figure.update_xaxes(title="Words per minute", range=[40, 220])
    figure.update_yaxes(autorange="reversed", tickfont={"size": 10})
    figure.update_layout(
        showlegend=True,
        legend={"orientation": "h", "y": 1.12, "x": 0},
    )
    return figure_style(figure, 500)


def figure_block(number: str, title: str, text: str, figure: go.Figure) -> html.Figure:
    return html.Figure([
        html.Figcaption([
            html.H3([html.Span(number, className="figure-number"), title]),
            html.P(text),
        ]),
        dcc.Graph(
            figure=figure,
            config={"displayModeBar": False, "responsive": True, "staticPlot": True},
        ),
    ], className="paper-figure")


def audio_cell(audio_file: str | None, label: str) -> html.Td:
    if not audio_file:
        return html.Td("—", className="pace-audio-cell pace-audio-empty")
    return html.Td(
        html.Audio(src=dash.get_asset_url(audio_file), controls=True, preload="metadata", **{"aria-label": label}),
        className="pace-audio-cell",
    )


def pace_sample_row(text: str, slow: str | None, medium: str | None, fast: str | None) -> html.Tr:
    return html.Tr([
        html.Th(html.Q(text), scope="row", className="pace-sample-text"),
        audio_cell(slow, "Slow sample"),
        audio_cell(medium, "Medium sample"),
        audio_cell(fast, "Fast sample"),
    ])


def layout() -> html.Main:
    corpus = SUMMARY["corpus"]
    rates = SUMMARY["speaking_rate"]
    pauses = SUMMARY["pauses"]
    audio = SUMMARY["audio"]
    punctuation = SUMMARY["punctuation_normalization"]
    return html.Main(html.Article([
        html.Header([
            html.H1("Somali Voice Training"),
            html.P([
                html.Strong("Abstract. "),
                f"This report presents the data and adaptation strategy used to specialize CosyVoice 3 for Somali speech synthesis. "
                f"The training corpus was assembled from a fully audited collection of {corpus['json_files_discovered']:,} Omar transcript records, with aligned audio evaluated for timing, speaking rate, signal compliance, and transcript integrity before inclusion. "
                "Fine-tuning updates the LLM and Flow modules so the model can learn Somali pronunciation, phrasing, prosody, and acoustic realization; the pretrained HiFT/HiFi-GAN vocoder remains frozen to preserve stable 24 kHz waveform generation. "
                "This separation concentrates learning capacity on language- and acoustics-specific adaptation while retaining a controlled synthesis backend for reproducible evaluation."
            ], className="paper-abstract"),
        ], className="paper-header"),
        html.Nav([html.Strong("Contents"), html.Ul([
            html.Li(html.A("Generated audio", href="#samples")),
            html.Li(html.A("Corpus and pace", href="#corpus")),
            html.Li(html.A("Data processing and cleaning", href="#processing")),
        ])], className="paper-toc"),
        html.Section([
            html.H2("1. Generated audio"),
            html.P("These samples are pure model generations from random Somali excerpts drawn from news and books. The excerpts are not part of the training set or validation set, and no reference audio was supplied or followed during synthesis. Each text is generated independently at the available slow, medium, and fast pace conditions."),
            html.Div(html.Table([
                html.Thead(html.Tr([html.Th("Text"), html.Th("Slow"), html.Th("Medium"), html.Th("Fast")])),
                html.Tbody([
                    pace_sample_row(
                        "Aanadii Negeeye waa buug waddo cusub u furaya bandhigga xikmadda iyo suugaanta soomaalida oo ilaa hadda si wayn la isugu soo tebin jirey tix ahaan.",
     "audio/omar-adanni-slow.wav",
                        "audio/omar-adanni-medium.wav",
                        "audio/omar-adanni-fast.wav",
                    ),
                    pace_sample_row(
                        "Waxay ahayd wax yar ka hor salaaddii Maqrib, markii Faarax gurigooda ay gabadh dhallinyaro ah oo wejigeeda qarinaysa albaabka soo garaacday.",
                        "audio/omar-garaacday-slow.wav",
                        "audio/omar-garaacday-medium.wav",
                        "audio/omar-garaacday-fast.wav",
                    ),
                    pace_sample_row(
                        "Hooyadii Dhool wax badan ma ay sugin ninkii wadku ka qaaday nin kale oo illawsiiya oo dhinaca gogosheeda bannaanaaday u buuxiya.",
                        "audio/omar-hooyadii-slow.wav",
                        "audio/omar-hooyadii-medium.wav",
                        "audio/omar-hooyadii-fast.wav",
                    ),
                ]),
            ]), className="audio-table-wrap"),
        ], id="samples"),
        html.Section([
            html.H2("2. Corpus and pace"),
            html.P(
                f"The processed corpus contains {corpus['total_hours']:.2f} hours across {corpus['valid_clips']:,} clips from {corpus['recording_sources']:,} recording folders. "
                f"The median experienced pace is {rates['median_wpm']:.1f} words per minute; {corpus['wpm_eligible_hours']:.2f} hours have usable timed-word data. "
                f"The pace analysis uses total clip duration, so it includes pauses and hesitation rather than measuring articulation alone."
            ),
            html.P([
                "The project source corpus is downloaded from the private Hugging Face dataset ",
                html.Code("levenberg/omar-somali-asr"),
                ". The local derived training build is deliberately separate: it packages reviewed audio and punctuation-aware text for CosyVoice 3 while preserving an audit trail back to those source records.",
            ]),
            figure_block("Figure 1.", "Distribution of experienced speaking pace.",
                         f"The middle half of clips falls between {rates['low_boundary_wpm']:.1f} and {rates['high_boundary_wpm']:.1f} WPM. "
                         f"The {rates['outlier_clips']} Tukey outliers remain review items rather than automatic pace labels.", wpm_distribution()),
            figure_block("Figure 2.", "Clip duration and speaking rate.",
                         f"{corpus['clips_20_to_30_percentage']:.2f}% of clips are in the 20–30 second target window. The plot exposes unusually short, long, or dense records for inspection.", duration_scatter()),
            html.P("Speaking rate varies substantially across the largest recording folders. Corpus-level thresholds are useful descriptive references, but each clip is retained with its timing record so pace labels can be reviewed in context."),
            figure_block(
                "Figure 3.",
                "Within-source variation in speaking pace.",
                "For each of the ten largest recording folders, the thin line shows the observed WPM range, the thick segment shows the middle 50%, and the white point marks the median.",
                source_range_plot(),
            ),
        ], id="corpus"),
        html.Section([
            html.H2("3. Data processing and cleaning"),
            html.P(
                "The source recordings are segmented with Silero VAD into coherent speech units, then denoised with DeepFilterNet 3 and loudness-normalised in a local batch workflow. "
                f"Published clips are mono 24 kHz, 16-bit PCM FLAC: all {audio['audio_files_scanned']:,} matched files meet this contract, and their JSON and FLAC durations differ by at most {audio['max_json_audio_duration_delta_seconds']:.4f} seconds. "
                "Temporary segmentation WAV files are not included in the published corpus."
            ),
            html.P(
                f"Transcript processing preserves the source text and treats timing as evidence. Timed lexical words are compared with the canonical transcript before punctuation is proposed; mismatches are review flags. "
                f"Inter-word gaps of 0.30 seconds propose commas and gaps of 0.75 seconds propose periods, producing {punctuation['total_proposed_commas'] + punctuation['total_proposed_periods']:,} proposed marks across {punctuation['review_manifest_count']:,} auditable review records. "
                f"The observed median gap is {pauses['median_interword_gap_seconds']:.2f} seconds; no SSML tags, pause tokens, or invented Somali words are introduced."
            ),
            html.P(
                "The resulting CosyVoice 3 training dataset, Omar punctuation + pace instruction dataset V1, pairs each included clip with a truthful natural-language pace instruction. "
                "These instructions are training labels, not commands inferred at synthesis time: each one is assigned from the observed overall WPM for its source clip. "
                "The derived dataset retains the punctuation-V1 transcript and original FLAC audio while adding the instruction, numeric WPM, and pace tier as explicit fields."
            ),
            html.Table([
                html.Tbody([
                    html.Tr([html.Th("Audio"), html.Td("Segment → denoise → loudness-normalise → mono 24 kHz PCM-16 FLAC")]),
                    html.Tr([html.Th("Text"), html.Td("Compare timed words to transcript → propose ordinary punctuation → human-review derived copy")]),
                    html.Tr([html.Th("Slow · < 120.9 WPM"), html.Td("You are a helpful assistant. Speak slowly and deliberately.")]),
                    html.Tr([html.Th("Medium · 120.9–154.5 WPM"), html.Td("You are a helpful assistant. Speak at a natural, moderate pace.")]),
                    html.Tr([html.Th("Fast · > 154.5 WPM"), html.Td("You are a helpful assistant. Speak at a fast pace.")]),
                    html.Tr([html.Th("Provenance"), html.Td("Keep original source material immutable; version derived transcripts, manifests, and audits separately")]),
                ])
            ], className="method-note"),
        ], id="processing"),
        html.Footer("Reproducibility · Generated from data/omar_wpm.csv and data/omar_dataset_summary.json by scripts/analyze_omar_dataset.py.", className="paper-footer"),
    ], className="github-paper"), className="single-page")
