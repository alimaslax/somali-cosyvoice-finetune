"""Replace Figure 3 with a dependency-free range and median chart."""

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


summary = json.loads((ROOT / "data/omar_dataset_summary.json").read_text())
by_recording: dict[str, list[float]] = defaultdict(list)
with (ROOT / "data/omar_wpm.csv").open(newline="") as handle:
    for row in csv.DictReader(handle):
        if row["wpm"]:
            by_recording[row["recording"]].append(float(row["wpm"]))

names, minimums, first_quartiles, medians, third_quartiles, maximums = ([] for _ in range(6))
for item in summary["top_recordings_by_hours"][:10]:
    recording = item["recording"]
    values = by_recording[recording]
    names.append(recording[:42] + ("…" if len(recording) > 42 else ""))
    minimums.append(min(values))
    first_quartiles.append(percentile(values, .25))
    medians.append(percentile(values, .5))
    third_quartiles.append(percentile(values, .75))
    maximums.append(max(values))


def ranges(starts: list[float], ends: list[float]) -> tuple[list, list]:
    x, y = [], []
    for name, start, end in zip(names, starts, ends):
        x.extend((start, end, None))
        y.extend((name, name, None))
    return x, y


full_x, full_y = ranges(minimums, maximums)
iqr_x, iqr_y = ranges(first_quartiles, third_quartiles)
charts_path = ROOT / "assets/charts.json"
charts = json.loads(charts_path.read_text())
layout = charts[2]["layout"]
layout.update({
    "hovermode": False,
    "showlegend": True,
    "legend": {"orientation": "h", "y": 1.12, "x": 0},
})
charts[2] = {
    "data": [
        {"type": "scatter", "x": full_x, "y": full_y, "mode": "lines", "hoverinfo": "skip",
         "line": {"color": "#65717a", "width": 2}, "name": "Observed range"},
        {"type": "scatter", "x": iqr_x, "y": iqr_y, "mode": "lines", "hoverinfo": "skip",
         "line": {"color": "#8ebfc8", "width": 10}, "name": "Middle 50%"},
        {"type": "scatter", "x": medians, "y": names, "mode": "markers", "hoverinfo": "skip",
         "marker": {"color": "#f0f1f3", "size": 8, "line": {"color": "#16171a", "width": 2}},
         "name": "Median"},
    ],
    "layout": layout,
}
charts_path.write_text(json.dumps(charts, separators=(",", ":")))
print("Rebuilt Figure 3 as a non-interactive range and median chart")
