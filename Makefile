# Laboratorio FDSI-GP-06. Todo se ejecuta sobre el venv local del proyecto.
PY ?= .venv/bin/python
N_T01 ?= 20
N_T02 ?= 100
PROFILE ?= unsecure

.PHONY: help setup model info test t01 t02 metrics chat clean-data evidence

help:
	@echo "make setup     crea el entorno e instala dependencias"
	@echo "make model     descarga el modelo en Ollama"
	@echo "make info      perfil activo e identidad del modelo"
	@echo "make test      suite de pytest (rapida, con backend stub)"
	@echo "make t01       T01 instruccion dormida  (N_T01=$(N_T01) sesiones nuevas)"
	@echo "make t02       T02 fuga entre usuarios  (N_T02=$(N_T02) sondeos)"
	@echo "make metrics   recalcula M1 y M2 de todas las corridas"
	@echo "make chat      conversacion interactiva (para el video demo)"
	@echo "make evidence  resumen de la evidencia registrada"

setup:
	uv venv --python 3.11
	uv pip install -e ".[dev]"

model:
	ollama pull llama3.1:8b-instruct-q4_K_M

info:
	$(PY) -m memlab.cli info

test:
	$(PY) -m pytest -q

t01:
	$(PY) experiments/run_t01.py --n $(N_T01) --profile $(PROFILE)

t02:
	$(PY) experiments/run_t02.py --n $(N_T02) --profile $(PROFILE)

metrics:
	$(PY) experiments/compute_metrics.py --all

chat:
	$(PY) -m memlab.cli chat --user A

evidence:
	@ls -1 evidence/runs 2>/dev/null || echo "sin corridas todavia"

clean-data:
	rm -rf data
