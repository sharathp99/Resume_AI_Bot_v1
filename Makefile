PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .[dev]

run-api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run app/ui/streamlit_app.py

run-all:
	docker compose up --build

test:
	pytest

lint:
	$(PYTHON) -m compileall app

reindex:
	$(PYTHON) scripts/reindex.py --role data_engineer
