from pathlib import Path
import textwrap

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "final" / "generation"

SUMMARY_FILE = ROOT / "results" / "generation_final_results.csv"
DETAIL_FILE = ROOT / "results" / "generation_final_details.csv"

EXCEL_FILE = OUTPUT_DIR / "generation_evaluation_report.xlsx"
TABLE_FILE = OUTPUT_DIR / "generation_evaluation_table.png"
GRAPH_FILE = OUTPUT_DIR / "generation_evaluation_graph.png"
METHOD_FILE = OUTPUT_DIR / "generation_evaluation_methodology.txt"


def load_font(size, bold=False):
    candidates = (
        ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold else
        ["arial.ttf", "DejaVuSans.ttf"]
    )

    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass

    return ImageFont.load_default()


def create_excel(summary, details):
    workbook = Workbook()

    ws = workbook.active
    ws.title = "Summary"

    ws.append(["Generation Evaluation Metrics", "Average Score"])

    for _, row in summary.iterrows():
        ws.append([row["Metric"], float(row["Average Score"])])

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    thin_border = Border(
        bottom=Side(style="thin", color="D9E2F3")
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row in ws.iter_rows(min_row=2):
        row[1].number_format = "0.000000"
        for cell in row:
            cell.border = thin_border

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 20
    ws.freeze_panes = "A2"

    detail_ws = workbook.create_sheet("Detailed Results")

    for column in details.columns:
        detail_ws.cell(row=1, column=len(detail_ws[1]) + 1, value=column)

    for row in details.itertuples(index=False, name=None):
        detail_ws.append(list(row))

    for cell in detail_ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

    for column_index, column_name in enumerate(details.columns, start=1):
        if column_name in ["question", "ideal_answer", "generated_answer"]:
            width = 55
        else:
            width = 16

        detail_ws.column_dimensions[
            get_column_letter(column_index)
        ].width = width

    detail_ws.freeze_panes = "A2"
    detail_ws.auto_filter.ref = detail_ws.dimensions

    for row in detail_ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

            if cell.column >= 4:
                cell.number_format = "0.000000"

    workbook.save(EXCEL_FILE)


def create_table(summary):
    width = 1400
    row_height = 105
    height = 230 + len(summary) * row_height

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = load_font(42, bold=True)
    header_font = load_font(27, bold=True)
    body_font = load_font(27)

    draw.text(
        (width // 2, 55),
        "Generation Evaluation Results",
        fill="#1F1F1F",
        font=title_font,
        anchor="mm"
    )

    left = 180
    right = width - 180
    top = 150
    col1 = left + 620
    row_height = 105

    draw.rounded_rectangle(
        (left, top, right, top + row_height),
        radius=8,
        fill="#1F4E78"
    )

    draw.text(
        (left + 25, top + row_height // 2),
        "Metric",
        fill="white",
        font=header_font,
        anchor="lm"
    )

    draw.text(
        (col1 + 25, top + row_height // 2),
        "Average Score",
        fill="white",
        font=header_font,
        anchor="lm"
    )

    for index, row in summary.iterrows():
        y1 = top + row_height * (index + 1)
        y2 = y1 + row_height

        fill = "#F2F6FA" if index % 2 == 0 else "#FFFFFF"

        draw.rectangle(
            (left, y1, right, y2),
            fill=fill,
            outline="#D9E2F3",
            width=2
        )

        draw.text(
            (left + 25, (y1 + y2) // 2),
            str(row["Metric"]),
            fill="#222222",
            font=body_font,
            anchor="lm"
        )

        draw.text(
            (col1 + 25, (y1 + y2) // 2),
            f'{float(row["Average Score"]):.6f}',
            fill="#222222",
            font=body_font,
            anchor="lm"
        )

    image.save(TABLE_FILE)


def create_graph(summary):
    width, height = 1600, 1050

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = load_font(42, bold=True)
    label_font = load_font(23)
    value_font = load_font(21, bold=True)

    draw.text(
        (width // 2, 65),
        "Generation Evaluation Metrics",
        fill="#1F1F1F",
        font=title_font,
        anchor="mm"
    )

    left, right = 150, 1480
    top, bottom = 180, 740
    chart_height = bottom - top

    # Y-axis and horizontal grid lines
    for tick in range(6):
        value = tick / 5
        y = bottom - int(value * chart_height)

        draw.line(
            (left, y, right, y),
            fill="#D9D9D9",
            width=2
        )

        draw.text(
            (left - 25, y),
            f"{value:.1f}",
            fill="#333333",
            font=label_font,
            anchor="rm"
        )

    draw.line(
        (left, top, left, bottom),
        fill="#333333",
        width=3
    )
    draw.line(
        (left, bottom, right, bottom),
        fill="#333333",
        width=3
    )

    values = summary["Average Score"].astype(float).tolist()
    labels = summary["Metric"].astype(str).tolist()

    slot_width = (right - left) / len(values)
    bar_width = min(115, slot_width * 0.55)

    for index, (label, value) in enumerate(zip(labels, values)):
        center_x = left + slot_width * (index + 0.5)
        bar_height = int(value * chart_height)

        x1 = int(center_x - bar_width / 2)
        x2 = int(center_x + bar_width / 2)
        y1 = bottom - bar_height

        draw.rectangle(
            (x1, y1, x2, bottom),
            fill="#4472C4"
        )

        value_y = max(top + 15, y1 - 32)

        draw.text(
            (int(center_x), value_y),
            f"{value:.3f}",
            fill="#222222",
            font=value_font,
            anchor="mm"
        )

        draw.text(
            (int(center_x), bottom + 55),
            label,
            fill="#222222",
            font=label_font,
            anchor="mm"
        )

    draw.text(
        (width // 2, 960),
        "Average Score (Scale: 0.0 to 1.0)",
        fill="#333333",
        font=label_font,
        anchor="mm"
    )

    image.save(GRAPH_FILE)


def create_methodology(summary, details):
    content = f"""
GENERATION EVALUATION METHODOLOGY

1. Objective
The objective of this evaluation is to measure the similarity
between answers generated by the Ollama language model and the
reference answers in the evaluation dataset.

2. Evaluation Dataset
Dataset: simple_questions_with_embeddings.csv
Number of evaluated questions: {len(details)}
Reference answer column: ideal_answer

The CSV file was used as a separate evaluation dataset.
The production database was not used or modified.

3. Language Model
Model: llama3.2:latest
Platform: Ollama (local execution)

The model was prompted to answer each interview question
naturally and professionally in approximately 3 to 5 sentences.
Generation used temperature 0.2 and a maximum of 180 predicted tokens.

4. Evaluation Procedure
Each question was passed to the Ollama model.
The generated answer was compared with the corresponding
ideal_answer from the CSV dataset.

The evaluation was performed on all {len(details)} questions.
The generated answers and individual metric scores were saved
in generation_final_details.csv.

5. Evaluation Metrics

Exact Match:
Measures whether the generated answer exactly matches the
reference answer after text normalization.

Token F1:
Measures the overlap between generated and reference answer words,
considering precision and recall.

BLEU:
Measures matching word sequences between generated and
reference answers.

ROUGE-1:
Measures overlap of individual words.

ROUGE-2:
Measures overlap of two-word sequences.

ROUGE-L:
Measures the longest common word sequence between the answers.

6. Final Average Scores

{summary.to_string(index=False)}

7. Interpretation and Limitation
These metrics measure lexical similarity rather than complete
semantic correctness. A generated answer may communicate a
correct idea using different wording and still receive a low score.

Therefore, the scores should be interpreted as automatic text
similarity measurements and not as a complete measure of
interview-answer quality.

The evaluation used a separate CSV dataset and local Ollama
generation. It did not directly measure live production-system
generation performance.
"""

    METHOD_FILE.write_text(content.strip(), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(SUMMARY_FILE)
    details = pd.read_csv(DETAIL_FILE)

    if len(details) != 40:
        raise ValueError(
            f"Expected 40 detailed results, found {len(details)}."
        )

    if len(summary) != 6:
        raise ValueError(
            f"Expected 6 summary metrics, found {len(summary)}."
        )

    create_excel(summary, details)
    create_table(summary)
    create_graph(summary)
    create_methodology(summary, details)

    print("\n========== GENERATION REPORT FILES CREATED ==========")
    for path in [
        EXCEL_FILE,
        TABLE_FILE,
        GRAPH_FILE,
        METHOD_FILE
    ]:
        print(path)


if __name__ == "__main__":
    main()
