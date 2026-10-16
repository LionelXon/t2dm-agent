.PHONY: test run

test:
	pytest -q

run:
	uvicorn src.api.main:app --reload

eval:
	HF_HUB_OFFLINE=1 python -m src.eval.run_eval

rules:
	python -m src.eval.run_rules_eval

redteam:
	HF_HUB_OFFLINE=1 python -m src.eval.run_redteam

serve:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

all: test rules
	HF_HUB_OFFLINE=1 python -m src.eval.run_eval
	HF_HUB_OFFLINE=1 python -m src.eval.run_redteam