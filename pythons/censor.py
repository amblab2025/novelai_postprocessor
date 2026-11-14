"""
Anime image penis censoring script.

Draws a thin black line over the glans area of detected penises.

Usage:
    python censor.py /path/to/png_folder

Output is written to a subfolder named `_02_censored`.
"""

import glob
import os
import sys
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw
from imgutils.detect import detect_censors


OUTPUT_FOLDER_NAME = "_02_censored"


def make_thin_line(
    box: Tuple[int, int, int, int],
    thickness: int,
    offset_ratio: float,
    width_ratio: float,
    img_width: int,
    img_height: int,
) -> Tuple[int, int, int, int]:
    """
    Create a short thin horizontal line over the glans area.
    offset_ratio: 0.0 = top of box, higher = lower. 0.1-0.25 recommended for glans.
    width_ratio: how much of the box width to cover (0.4-0.7 recommended).
    """
    x0, y0, x1, y1 = box
    box_w = x1 - x0
    box_h = y1 - y0

    # Vertical position (glans is usually toward the top of the detection box)
    center_y = y0 + int(box_h * offset_ratio)
    half_thick = max(1, thickness // 2)

    line_y0 = max(0, center_y - half_thick)
    line_y1 = min(img_height, center_y + half_thick + 1)

    # Horizontal: shorter than the full box, centered
    line_w = int(box_w * width_ratio)
    center_x = (x0 + x1) // 2
    line_x0 = max(0, center_x - line_w // 2)
    line_x1 = min(img_width, center_x + line_w // 2)

    return line_x0, line_y0, line_x1, line_y1


def censor_image(
    input_path: Path,
    output_path: Path,
    thickness: int = 7,
    offset_ratio: float = 0.18,
    width_ratio: float = 0.55,
    conf_threshold: float = 0.25,
) -> int:
    """
    Detect penises and draw a thin black line over the glans.
    Returns the number of regions censored.
    """
    image = Image.open(input_path).convert("RGB")
    img_width, img_height = image.size

    detections = detect_censors(
        image,
        level="s",
        conf_threshold=conf_threshold,
    )

    lines: List[Tuple[int, int, int, int]] = []
    for box, label, score in detections:
        if label == "penis":
            line = make_thin_line(
                box, thickness, offset_ratio, width_ratio, img_width, img_height
            )
            lines.append(line)

    if lines:
        draw = ImageDraw.Draw(image)
        for line in lines:
            draw.rectangle(line, fill="black")

    image.save(output_path, "PNG")
    return len(lines)


def main(
    parent_folder_path,
    thickness=7,
    offset_ratio=0.18,
    width_ratio=0.55,
    conf=0.25,
) -> None:
    output_folder_path = os.path.join(parent_folder_path, OUTPUT_FOLDER_NAME)
    os.makedirs(output_folder_path, exist_ok=True)

    image_paths = []
    for ext in ("*.png",):
        image_paths.extend(glob.glob(os.path.join(parent_folder_path, ext)))

    if not image_paths:
        print(f"No .png images found in {parent_folder_path}")
        return

    print(f"Processing {len(image_paths)} images...")
    print(f"Output folder: {output_folder_path}")
    print(
        f"Thickness: {thickness}px | Offset: {offset_ratio} | "
        f"Width ratio: {width_ratio} | Confidence: {conf}"
    )

    total_censored = 0
    for img_path in image_paths:
        stem = Path(img_path).stem
        output_file_name = f"{stem}_censored.png"
        output_file_path = os.path.join(output_folder_path, output_file_name)
        try:
            count = censor_image(
                img_path,
                output_file_path,
                thickness=thickness,
                offset_ratio=offset_ratio,
                width_ratio=width_ratio,
                conf_threshold=conf,
            )
            total_censored += count
            status = f"{count} region(s)" if count else "no detection"
            print(f"  {img_path} -> {status}")
        except Exception as e:
            print(f"  ERROR processing {img_path}: {e}")

    print(f"\nDone. {len(image_paths)} images processed, {total_censored} regions censored.")
    print(f"Results saved to: {output_folder_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python censor.py <parent_folder_path>")
        exit(1)

    parent_folder_path = sys.argv[1]
    thickness = int(input("thickness (default = 7) = ") or 7)
    offset_ratio = float(input("offset_ratio (default = 0.18) = ") or 0.18)
    width_ratio = float(input("width_ratio (default = 0.55) = ") or 0.55)
    conf = float(input("conf (default = 0.25) = ") or 0.25)
    main(
        parent_folder_path=parent_folder_path,
        thickness=thickness,
        offset_ratio=offset_ratio,
        width_ratio=width_ratio,
        conf=conf,
    )
