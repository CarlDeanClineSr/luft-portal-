# Makefile for LUFT Capsule Figures
# Regenerates figures whenever the CSV log updates

DATA = cme_heartbeat_log_2025_12.csv
SCRIPT = cme_heartbeat_analysis.py
FIGURES = figure1_saturation.png figure2_hysteresis.png figure3_magnetic.png figure4_phase.png

all: $(FIGURES)

$(FIGURES): $(DATA) $(SCRIPT)
	@echo "Regenerating figures from $(DATA)..."
	python3 $(SCRIPT)

clean:
	rm -f $(FIGURES)

rebuild:
	$(MAKE) clean
	$(MAKE) all
