#!/usr/bin/env python3
"""
Just detect objects in an image!

Outputs a json-formatted list:

e.g. [ {"label": "bird", "coords": {"tl": [1,2], "br": [3,4]}}, ...]

Comes mostly right from https://pytorch.org/vision/stable/models.html#object-detection
"""

import argparse
import json
import sys

import torch
from torchvision.io.image import decode_image
from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn_v2,
    FasterRCNN_ResNet50_FPN_V2_Weights,
)
from torchvision.utils import draw_bounding_boxes
from torchvision.transforms.functional import to_pil_image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="Path to input image")
    ap.add_argument(
        "outfile",
        default="-",
        nargs="?",
        help="File to output results to (or - for stdout, default)",
    )
    ap.add_argument(
        "--save-tagged-image-as",
        default=None,
        help="File to save an image with detected objects marked",
    )
    args = ap.parse_args()

    torch.hub.set_dir("./torch_cache")

    img = decode_image(args.image)

    # Step 1: Initialize model with the best available weights
    weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    model = fasterrcnn_resnet50_fpn_v2(weights=weights, box_score_thresh=0.15)
    model.eval()

    # Step 2: Initialize the inference transforms
    preprocess = weights.transforms()

    # Step 3: Apply inference preprocessing transforms
    batch = [preprocess(img)]

    # Step 4: Use the model and visualize the prediction
    prediction = model(batch)[0]
    labels = [weights.meta["categories"][i] for i in prediction["labels"]]

    if args.save_tagged_image_as:
        box = draw_bounding_boxes(
            img,
            boxes=prediction["boxes"],
            labels=labels,
            colors="red",
            width=4,
            font_size=30,
        )
        im = to_pil_image(box.detach())
        im.save(args.save_tagged_image_as)

    result = []
    for i, coords in enumerate(prediction["boxes"]):
        x0, y0, x1, y1 = [int(x) for x in coords.tolist()]
        result.append(
            {
                "label": labels[i],
                "coords": {
                    "tl": {"x": x0, "y": y0},
                    "br": {"x": x1, "y": y1},
                },
            }
        )

    if args.outfile == "-":
        json.dump(result, sys.stdout)
    else:
        with open(args.outfile, "w", encoding="utf-8") as file:
            json.dump(result, file)


if __name__ == "__main__":
    main()
