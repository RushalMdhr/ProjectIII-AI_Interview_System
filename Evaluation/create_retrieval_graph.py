from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import pandas as pd

df = pd.read_csv("final/retrieval_final_results.csv")

label_map = {
    "Similarity Score": "similarity_score",
    "Precision@5": "precision@5",
    "Recall@5": "recall@5",
    "Mean Reciprocal Rank": "mrr",
    "F1 Score": "f1",
}

labels = [label_map.get(x, x.lower()) for x in df["Metric"]]
scores = df["Average Score"].astype(float).tolist()

W, H = 1400, 1000
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

def font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()

title_font = font(30)
tick_font = font(20)
label_font = font(19)

# Plot area with extra space below for labels
left, right = 150, 1280
top, bottom = 140, 590

# Title
draw.text(
    ((left + right) // 2, 75),
    "Retrieval metrics",
    fill="black",
    font=title_font,
    anchor="mm"
)

# Plot border
draw.rectangle(
    (left, top, right, bottom),
    outline="black",
    width=2
)

# Y-axis: 0.0 to 1.0
for i in range(6):
    value = i / 5
    y = bottom - int(value * (bottom - top))

    draw.line((left - 7, y, left, y), fill="black", width=2)
    draw.text(
        (left - 18, y),
        f"{value:.1f}",
        fill="black",
        font=tick_font,
        anchor="rm"
    )

# Bars
slot = (right - left) / len(labels)
bar_width = 125

for i, (label, score) in enumerate(zip(labels, scores)):
    center = left + slot * (i + 0.5)
    bar_top = bottom - int(score * (bottom - top))

    draw.rectangle(
        (
            int(center - bar_width / 2),
            bar_top,
            int(center + bar_width / 2),
            bottom
        ),
        fill="#2864E8"
    )

    # Create exact-size label image
    bbox = label_font.getbbox(label)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    label_img = Image.new(
        "RGBA",
        (text_w + 16, text_h + 16),
        (255, 255, 255, 0)
    )
    label_draw = ImageDraw.Draw(label_img)
    label_draw.text(
        (8 - bbox[0], 8 - bbox[1]),
        label,
        fill="black",
        font=label_font
    )

    # Rotate and place fully inside the image
    rotated = label_img.rotate(45, expand=True)

    x = int(center - rotated.width / 2)
    y = bottom + 28

    img.paste(rotated, (x, y), rotated)

# Save
output = Path("final/retrieval_evaluation_graph.png")
img.save(output, dpi=(200, 200))

print("Updated graph:", output.resolve())
print("Image dimensions:", img.size)
print("All five labels:", labels)
