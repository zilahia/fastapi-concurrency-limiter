"""
Reads chart_data.csv and saves a PNG with per-scenario RPS and VUs over time.

Usage:
  python plot.py [chart_data.csv] [output.png]
"""

# pyright: reportUnknownMemberType=false
import csv
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

src = sys.argv[1] if len(sys.argv) > 1 else "chart_data.csv"
dst = sys.argv[2] if len(sys.argv) > 2 else "chart.png"

seconds: list[int] = []
messages_rps: list[int] = []
file_rps: list[int] = []
messages_errors: list[int] = []
file_errors: list[int] = []
messages_vus: list[int] = []
file_vus: list[int] = []

with open(src, newline="") as f:
    for row in csv.DictReader(f):
        seconds.append(int(row["second"]))
        messages_rps.append(int(row["messages_rps"]))
        file_rps.append(int(row["file_rps"]))
        messages_errors.append(int(row["messages_errors"]))
        file_errors.append(int(row["file_errors"]))
        messages_vus.append(int(row["messages_vus"]))
        file_vus.append(int(row["file_vus"]))

t0 = seconds[0]
elapsed = [s - t0 for s in seconds]

fig, ax1 = plt.subplots(figsize=(13, 5))
fig.suptitle("k6 Benchmark — localhost:8000", fontweight="bold")  # type: ignore

# RPS lines on left axis
ax1.set_xlabel("Elapsed time (s)")
ax1.set_ylabel("Requests / s")
(l1,) = ax1.plot(elapsed, messages_rps, color="steelblue", linewidth=2, label="/messages req/s")
(l2,) = ax1.plot(elapsed, file_rps, color="seagreen", linewidth=2, label="/file req/s")

if any(e > 0 for e in messages_errors):
    ax1.fill_between(
        elapsed,
        0,
        messages_errors,  # type: ignore[arg-type]
        color="steelblue",
        alpha=0.25,
        label="/messages errors/s",  # type: ignore
    )
if any(e > 0 for e in file_errors):
    ax1.fill_between(elapsed, 0, file_errors, color="seagreen", alpha=0.25, label="/file errors/s")  # type: ignore[arg-type]

ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.grid(axis="y", linestyle="--", alpha=0.4)

# VU lines on right axis
ax2 = ax1.twinx()
ax2.set_ylabel("Virtual Users (VUs)")
(l3,) = ax2.plot(
    elapsed, messages_vus, color="darkorange", linewidth=2, linestyle="--", label="/messages VUs"
)
(l4,) = ax2.plot(
    elapsed, file_vus, color="mediumpurple", linewidth=2, linestyle="--", label="/file VUs"
)

lines = [l1, l2, l3, l4]
ax1.legend(lines, [line.get_label() for line in lines], loc="upper left")

fig.tight_layout()
fig.savefig(dst, dpi=150)
print(f"Saved {dst}")
