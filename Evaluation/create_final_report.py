from pathlib import Path
import shutil
import pandas as pd

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results"
FINAL = ROOT / "final"

FINAL.mkdir(exist_ok=True)

# Copy the final CSV files
shutil.copy2(
    SOURCE / "retrieval_final_results.csv",
    FINAL / "retrieval_final_results.csv"
)

shutil.copy2(
    SOURCE / "retrieval_final_details.csv",
    FINAL / "retrieval_final_details.csv"
)

# Load evaluation results
summary = pd.read_csv(SOURCE / "retrieval_final_results.csv")
details = pd.read_csv(SOURCE / "retrieval_final_details.csv")

# Create workbook
wb = Workbook()

# Summary sheet
ws = wb.active
ws.title = "Summary"

ws["A1"] = "RETRIEVAL EVALUATION RESULTS"
ws["A1"].font = Font(size=16, bold=True)
ws.merge_cells("A1:B1")

ws["A2"] = "Evaluation Dataset: 40 Common Interview Questions"
ws.merge_cells("A2:B2")

ws.append([])
ws.append(["Metric", "Average Score"])

for row in summary.itertuples(index=False):
    ws.append([row[0], float(row[1])])

# Format summary table
for cell in ws[4]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")

for row in ws.iter_rows(min_row=5, max_row=9, min_col=2, max_col=2):
    for cell in row:
        cell.number_format = "0.000000"

for column, width in {"A": 30, "B": 20}.items():
    ws.column_dimensions[column].width = width

# Add bar chart
chart = BarChart()
chart.type = "bar"
chart.style = 10
chart.title = "Retrieval Evaluation Metrics"
chart.y_axis.title = "Metrics"
chart.x_axis.title = "Average Score"
chart.height = 8
chart.width = 16
chart.x_axis.scaling.max = 1

data = Reference(ws, min_col=2, min_row=4, max_row=9)
categories = Reference(ws, min_col=1, min_row=5, max_row=9)

chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)
chart.legend = None
chart.dataLabels = DataLabelList()
chart.dataLabels.showVal = True

ws.add_chart(chart, "D4")

# Detailed results sheet
detail_ws = wb.create_sheet("Detailed Results")

for row in [list(details.columns)] + details.values.tolist():
    detail_ws.append(row)

for cell in detail_ws[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")

detail_ws.freeze_panes = "A2"
detail_ws.auto_filter.ref = detail_ws.dimensions

detail_ws.column_dimensions["A"].width = 75

for col in range(2, detail_ws.max_column + 1):
    detail_ws.column_dimensions[
        detail_ws.cell(1, col).column_letter
    ].width = 22

# Save workbook
output = FINAL / "retrieval_evaluation_report.xlsx"
wb.save(output)

print("\n========== FINAL RETRIEVAL PACKAGE CREATED ==========")
print("Final folder:", FINAL)
print("Summary table: retrieval_final_results.csv")
print("Detailed results: retrieval_final_details.csv")
print("Excel table and graph: retrieval_evaluation_report.xlsx")
print("\nAll files created successfully.")
