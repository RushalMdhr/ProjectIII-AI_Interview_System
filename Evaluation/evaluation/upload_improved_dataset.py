
import pandas as pd
from pathlib import Path
from langsmith import Client

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "common_questions_improved.xlsx"

DATASET_NAME = "Interview-Common-Questions-40-Improved"

# Load improved Excel dataset
df = pd.read_excel(DATA_FILE)
df = df.dropna(subset=["question", "ideal_answer"])

client = Client()

# Check whether the dataset already exists
try:
    dataset = client.read_dataset(dataset_name=DATASET_NAME)
    print("Dataset already exists:", DATASET_NAME)

    existing = list(
        client.list_examples(dataset_id=dataset.id)
    )

    if len(existing) == 40:
        print("Dataset already contains 40 examples. No upload needed.")
        raise SystemExit

    if len(existing) > 0:
        print("Dataset contains", len(existing), "examples.")
        print("Stopping to avoid duplicate or incomplete uploads.")
        raise SystemExit

except SystemExit:
    raise

except Exception:
    # Create dataset if it does not exist
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Improved 40 common interview questions and ideal answers."
    )

# Prepare examples
inputs = [
    {"query": row["question"]}
    for _, row in df.iterrows()
]

outputs = [
    {"ideal_answer": row["ideal_answer"]}
    for _, row in df.iterrows()
]

# Upload examples
client.create_examples(
    inputs=inputs,
    outputs=outputs,
    dataset_id=dataset.id
)

print("\nSuccessfully uploaded improved dataset!")
print("Dataset:", DATASET_NAME)
print("Total uploaded:", len(inputs))
