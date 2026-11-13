# AI Interview Evaluation

A small Python project for evaluating AI-generated interview responses.

## Structure

- `data/`: input datasets such as `test_data.csv`
- `evaluation/`: metrics, adapters, evaluation pipeline, and judge utilities
- `results/`: generated evaluation outputs

## Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

Add evaluation examples to `data/test_data.csv`, then implement or run the modules in `evaluation/` as the project grows.
