"""
Aggregates a raw k6 CSV (--out csv=raw.csv) into a per-second summary
with columns split by scenario:

  second, messages_rps, file_rps, messages_errors, file_errors, messages_vus, file_vus

Usage:
  python aggregate.py raw.csv chart_data.csv
"""

import csv
import sys
from collections import defaultdict

FILE_CONSTANT_VUS = 2  # matches file_constant scenario config

def aggregate(src: str, dst: str) -> None:
    reqs: defaultdict[str, defaultdict[int, int]] = defaultdict(
        lambda: defaultdict[int, int](int)
    )
    errors: defaultdict[str, defaultdict[int, float]] = defaultdict(
        lambda: defaultdict[int, float](float)
    )
    total_vus: dict[int, int] = {}  # k6 vus metric is global, no scenario tag

    with open(src, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name     = row["metric_name"]
            sec      = int(row["timestamp"])
            value    = float(row["metric_value"])
            scenario = row.get("scenario", "")

            if name == "http_reqs":
                reqs[scenario][sec] += 1
            elif name == "http_req_failed":
                errors[scenario][sec] += value
            elif name == "vus":
                total_vus[sec] = int(value)

    all_seconds: list[int] = sorted(
        {sec for v in reqs.values() for sec in v} | set(total_vus)
    )

    with open(dst, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "second",
            "messages_rps", "file_rps",
            "messages_errors", "file_errors",
            "messages_vus", "file_vus",
        ])
        last_total = 0
        for sec in all_seconds:
            last_total = total_vus.get(sec, last_total)
            file_vus     = min(FILE_CONSTANT_VUS, last_total)
            messages_vus = max(0, last_total - FILE_CONSTANT_VUS)
            writer.writerow([
                sec,
                reqs["messages_load"].get(sec, 0),
                reqs["file_constant"].get(sec, 0),
                errors["messages_load"].get(sec, 0),
                errors["file_constant"].get(sec, 0),
                messages_vus,
                file_vus,
            ])

    print(f"Written {len(all_seconds)} rows to {dst}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "raw.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "chart_data.csv"
    aggregate(src, dst)
