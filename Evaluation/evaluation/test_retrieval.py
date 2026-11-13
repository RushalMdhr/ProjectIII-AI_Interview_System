
from .adapter import retrieve
import pandas as pd

DATA_FILE = "data/common_questions.xlsx"

data = pd.read_excel(DATA_FILE)

# Select one question to inspect
query = data.iloc[0]["question"]

print("\nQUERY:")
print(query)

response = retrieve(query, top_k=5)

print("\nTOP 5 RETRIEVED QUESTIONS:")
print("=" * 70)

for rank, result in enumerate(response["results"], start=1):

    print(f"\nRank: {rank}")
    print("Question:", result["question"])
    print("Score:", result.get("score", 0))

    if result["question"].strip().lower() == query.strip().lower():
        print("Exact match: YES")
    else:
        print("Exact match: NO")
