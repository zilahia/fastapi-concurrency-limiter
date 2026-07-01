BASE_URL ?= http://localhost:8000

PYTHON := python3

.PHONY: run smoke stress summary csv chart plot

# Full staged load test
run:
	k6 run benchmark.js

# Quick sanity check: 1 VU for 10s
smoke:
	k6 run --vus 1 --duration 10s benchmark.js

chart:
	k6 run --out csv=raw.csv benchmark.js
	$(PYTHON) aggregate.py raw.csv chart_data.csv

# Generate chart.png from existing chart_data.csv and open it
plot:
	$(PYTHON) plot.py chart_data.csv chart.png
	xdg-open chart.png

# Full pipeline: run k6, aggregate, plot, open
all: chart plot
