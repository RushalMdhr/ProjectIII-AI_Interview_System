from pathlib import Path
import csv
import shutil
from PIL import Image, ImageDraw, ImageFont

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results"
FINAL = ROOT / "final"
FINAL.mkdir(exist_ok=True)

summary_file = SOURCE / "retrieval_final_results.csv"
details_file = SOURCE / "retrieval_final_details.csv"

if not summary_file.exists() or not details_file.exists():
    raise FileNotFoundError(
        "The retrieval result CSV files are missing from the results folder."
    )

# Read the latest retrieval results
with open(summary_file, newline="", encoding="utf-8-sig") as f:
    summary = list(csv.DictReader(f))

with open(details_file, newline="", encoding="utf-8-sig") as f:
    details = list(csv.DictReader(f))

metrics = [
    (row["Metric"], float(row["Average Score"]))
    for row in summary
]

# Copy original CSV files into final folder
shutil.copy2(summary_file, FINAL / "retrieval_final_results.csv")
shutil.copy2(details_file, FINAL / "retrieval_final_details.csv")

# Font setup for PNG images
def get_font(size, bold=False):
    candidates = (
        ["arialbd.ttf", "Arial Bold.ttf"]
        if bold else ["arial.ttf", "Times New Roman.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()

# -------------------------------------------------
# 1. CREATE REPORT-STYLE METRICS TABLE PNG
# -------------------------------------------------
W, H = 950, 440
table_img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(table_img)

title_font = get_font(29, True)
heading_font = get_font(23, True)
body_font = get_font(22)

draw.text((W // 2, 35), "Table: Retrieval Evaluation Metrics",
          fill="black", font=title_font, anchor="mt")

x1, x2 = 170, 780
top = 115
row_h = 52

draw.line((x1, top, x2, top), fill="black", width=2)
draw.text((x1 + 15, top + 12), "Metric", fill="black", font=heading_font)
draw.text((x2 - 15, top + 12), "Average Score",
          fill="black", font=heading_font, anchor="ra")
draw.line((x1, top + row_h, x2, top + row_h), fill="black", width=1)

for i, (name, score) in enumerate(metrics):
    y = top + row_h * (i + 1)
    draw.text((x1 + 15, y + 12), name, fill="black", font=body_font)
    draw.text((x2 - 15, y + 12), f"{score:.6f}",
              fill="black", font=body_font, anchor="ra")
    draw.line((x1, y + row_h, x2, y + row_h),
              fill="black", width=1)

table_path = FINAL / "retrieval_evaluation_table.png"
table_img.save(table_path, dpi=(200, 200))

# -------------------------------------------------
# 2. CREATE SEPARATE VERTICAL BAR GRAPH PNG
# -------------------------------------------------
W, H = 1200, 760
graph = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(graph)

title_font = get_font(30, True)
label_font = get_font(19)
value_font = get_font(17, True)

d.text((W // 2, 35), "Retrieval Metrics",
       fill="black", font=title_font, anchor="mt")

left, right = 115, 1120
top, bottom = 125, 570
plot_h = bottom - top

# Y-axis grid and labels, from 0.0 to 1.0
for tick in range(6):
    value = tick / 5
    y = bottom - int(value * plot_h)
    d.line((left, y, right, y), fill="#D9D9D9", width=1)
    d.text((left - 18, y), f"{value:.1f}",
           fill="black", font=label_font, anchor="rm")

# Axes
d.line((left, top, left, bottom), fill="black", width=2)
d.line((left, bottom, right, bottom), fill="black", width=2)

# Bars
count = len(metrics)
slot = (right - left) / count
bar_width = 105

for i, (name, score) in enumerate(metrics):
    center = left + slot * (i + 0.5)
    bar_top = bottom - int(score * plot_h)

    d.rectangle(
        (center - bar_width / 2, bar_top,
         center + bar_width / 2, bottom),
        fill="#2864E8"
    )

    d.text((center, bar_top - 15), f"{score:.3f}",
           fill="black", font=value_font, anchor="ms")

    # Rotated category labels, similar to the report screenshot
    label_layer = Image.new("RGBA", (300, 45), (255, 255, 255, 0))
    label_draw = ImageDraw.Draw(label_layer)
    label_draw.text((5, 5), name, fill="black", font=label_font)
    rotated = label_layer.rotate(45, expand=True)
    graph.paste(
        rotated,
        (int(center - 12), bottom + 15),
        rotated
    )

d.text((W // 2, 720), "Average Score",
       fill="black", font=label_font, anchor="mt")

graph_path = FINAL / "retrieval_evaluation_graph.png"
graph.save(graph_path, dpi=(200, 200))

# -------------------------------------------------
# 3. CREATE EXCEL WORKBOOK WITH TABLE AND GRAPH
# -------------------------------------------------
wb = Workbook()
ws = wb.active
ws.title = "Retrieval Summary"

ws["A1"] = "RETRIEVAL EVALUATION RESULTS"
ws["A1"].font = Font(size=16, bold=True)
ws.merge_cells("A1:B1")

ws["A2"] = "Evaluation Dataset: 40 Common Interview Questions"
ws.merge_cells("A2:B2")

ws.append([])
ws.append(["Metric", "Average Score"])

for name, score in metrics:
    ws.append([name, score])

for cell in ws[4]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")

for row in range(5, 5 + len(metrics)):
    ws.cell(row, 2).number_format = "0.000000"

ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 20

chart = BarChart()
chart.type = "col"
chart.style = 10
chart.title = "Retrieval Metrics"
chart.y_axis.title = "Average Score"
chart.x_axis.title = "Metrics"
chart.y_axis.scaling.min = 0
chart.y_axis.scaling.max = 1
chart.height = 9
chart.width = 17
chart.legend = None

data = Reference(ws, min_col=2, min_row=4, max_row=4 + len(metrics))
categories = Reference(ws, min_col=1, min_row=5,
                       max_row=4 + len(metrics))
chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)
chart.dataLabels = DataLabelList()
chart.dataLabels.showVal = True
ws.add_chart(chart, "D4")

# Detailed results sheet
detail_ws = wb.create_sheet("Detailed Results")

headers = list(details[0].keys())
detail_ws.append(headers)

for row in details:
    detail_ws.append([
        float(row[h]) if h != "question" else row[h]
        for h in headers
    ])

for cell in detail_ws[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")

detail_ws.freeze_panes = "A2"
detail_ws.auto_filter.ref = detail_ws.dimensions
detail_ws.column_dimensions["A"].width = 75

for col in range(2, len(headers) + 1):
    detail_ws.column_dimensions[
        detail_ws.cell(1, col).column_letter
    ].width = 22

excel_path = FINAL / "retrieval_evaluation_report.xlsx"
wb.save(excel_path)

# -------------------------------------------------
# 4. SAVE METHODOLOGY NOTES
# -------------------------------------------------
methodology = """RETRIEVAL EVALUATION

Dataset:
40 common interview questions from the evaluation CSV.

Method:
Each question was used as a query. Its own row was excluded,
leaving 39 candidate questions. Cosine similarity was used
to rank candidates, and the top five were evaluated.

Relevance rule:
A candidate was considered relevant if it shared at least
one category or keyword with the query.

Metrics:
Similarity Score, Precision@5, Recall@5,
Mean Reciprocal Rank (MRR), and F1 Score.

This is an offline embedding-based evaluation using the CSV
dataset, not a measurement of the live backend retrieval path.
"""

(FINAL / "retrieval_evaluation_methodology.txt").write_text(
    methodology, encoding="utf-8"
)

print("\nFINAL RETRIEVAL PACKAGE CREATED")
print("--------------------------------")
for file in sorted(FINAL.iterdir()):
    print(file.name)
print("\nAll files saved in:", FINAL.resolve())
