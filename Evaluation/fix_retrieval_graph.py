from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import pandas as pd
import math

# Read actual retrieval results
df = pd.read_csv("final/retrieval_final_results.csv")
metrics = df["Metric"].tolist()
scores = df["Average Score"].tolist()

W, H = 1200, 850
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

def get_font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()

title_font = get_font(28, True)
label_font = get_font(18)
value_font = get_font(17, True)

# Title
draw.text((W // 2, 35), "Retrieval Metrics",
          fill="black", font=title_font, anchor="mt")

# Plot area
left, right = 120, 1120
top, bottom = 120, 520
plot_height = bottom - top

# Y-axis ticks and gridlines
for tick in range(6):
    value = tick / 5
    y = bottom - int(value * plot_height)

    draw.line((left, y, right, y), fill="#D0D0D0", width=1)
    draw.text((left - 18, y), f"{value:.1f}",
              fill="black", font=label_font, anchor="rm")

# Axes
draw.line((left, top, left, bottom), fill="black", width=2)
draw.line((left, bottom, right, bottom), fill="black", width=2)

# Draw bars
slot = (right - left) / len(metrics)
bar_width = 110

for i, (name, score) in enumerate(zip(metrics, scores)):
    center = left + slot * (i + 0.5)
    bar_top = bottom - int(score * plot_height)

    draw.rectangle(
        (center - bar_width / 2, bar_top,
         center + bar_width / 2, bottom),
        fill="#2864E8"
    )

    # Value above each bar
    draw.text((center, bar_top - 12), f"{score:.3f}",
              fill="black", font=value_font, anchor="ms")

    # Rotated X-axis label
    label_box = Image.new("RGBA", (300, 40), (255, 255, 255, 0))
    label_draw = ImageDraw.Draw(label_box)
    label_draw.text((5, 5), name, fill="black", font=label_font)

    rotated = label_box.rotate(45, expand=True)

    paste_x = int(center - rotated.width / 2)
    paste_y = bottom + 12

    img.paste(rotated, (paste_x, paste_y), rotated)

# Save graph
output = Path("final/retrieval_evaluation_graph.png")
img.save(output, dpi=(200, 200))

print("Graph successfully updated:")
print(output.resolve())
