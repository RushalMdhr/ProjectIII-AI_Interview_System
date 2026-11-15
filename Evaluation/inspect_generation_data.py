import pandas as pd

files = [
    "data/candidate_answers_ollama_evaluation.xlsx",
    "data/common_questions.xlsx",
    "data/common_questions_improved.xlsx",
]

for file in files:
    print("\n" + "=" * 80)
    print("FILE:", file)

    excel = pd.ExcelFile(file)
    print("Sheets:", excel.sheet_names)

    for sheet in excel.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        print("\nSheet:", sheet)
        print("Shape:", df.shape)
        print("Columns:", df.columns.tolist())
        print(df.head(3).to_string(index=False))
