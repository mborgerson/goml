#!/usr/bin/env python3
"""
Get off my lawn!

Stop pesky birds from eating your new ryegrass seed! Turn the sprinklers on
when any birds are seen by your IP camera.
"""

import argparse
import json
import logging
import os
import pprint
import shutil
import subprocess
import tempfile
import time

from datetime import datetime
from pathlib import Path


log = logging.getLogger(__name__)


DETECTOR_CONTAINER_IMAGE = "detector"
SPRINKLER_CONTAINER_IMAGE = "sprinkler"
SUNRISE = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
SUNSET = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0)


def capture_picture(camera_url: str, crop: str | None = None) -> Path:
    """Capture an image from the camera at `camera_url` and return captured picture path."""
    picture_path = Path("/tmp/capture.jpg")
    log.info("Capturing image to %s...", picture_path)

    subprocess.run(
        f"ffmpeg -y -i {camera_url} -ss 00:00:01.000 "
        + (f"-vf crop={crop} " if crop else "")
        + f"-vframes 1 -f image2 -update true {picture_path}",
        shell=True
    )

    return picture_path


def detect_objects_in_picture(picture_path: Path) -> list[dict]:
    """Detect and return a list of objects in the image at `picture_path`."""
    log.info("Analyzing image...")
    picture_path = picture_path.resolve()
    torch_cache_path = Path("torch_cache")

    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as detections_file:
        subprocess.run(
            "docker run --rm "
            + f"-v {torch_cache_path.resolve()}:/app/torch_cache "
            + f"-v {picture_path}:{picture_path}:ro "
            + f"-v {detections_file.name}:/app/detections.json "
            + DETECTOR_CONTAINER_IMAGE
            + f" python detect.py {picture_path} /app/detections.json",
            shell=True,
        )
        try:
            result = json.load(detections_file)
        except:
            result = []

        if result:
            log.info("Detected:\n%s", pprint.pformat(result, indent=1))
        else:
            log.info("No objects detected")

        return result


def run_sprinklers(config_path: Path) -> None:
    """Turn on the sprinklers for a bit."""
    log.info("Activating sprinklers!")

    subprocess.run(
        "docker run --rm "
        + f"-v {config_path.resolve()}:/app/config.js "
        + SPRINKLER_CONTAINER_IMAGE,
        shell=True,
    )


def main():
    logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log.setLevel(logging.INFO)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--camera", required=True, help="Camera URL")
    ap.add_argument("--camera-crop", default=None, help="Camera crop (out_w:out_h:x:y)")
    default_sprinkler_config_path = "bhyve-config.js"
    ap.add_argument(
        "--sprinkler-config",
        default=default_sprinkler_config_path,
        help=f"Path to sprinkler config (default {default_sprinkler_config_path})",
    )
    default_interval = 60 * 5
    ap.add_argument(
        "--interval",
        default=default_interval,
        type=int,
        help=f"Seconds to wait between checks (default {default_interval})",
    )
    args = ap.parse_args()

    while True:
        if SUNRISE <= datetime.now() <= SUNSET:
            picture_path = capture_picture(args.camera, args.camera_crop)
            objects = detect_objects_in_picture(picture_path)
            if any(object["label"] == "bird" for object in objects):
                os.makedirs("events", exist_ok=True)
                shutil.copyfile(picture_path,
                                os.path.join("events", f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"))
                run_sprinklers(Path(args.sprinkler_config))
        else:
            log.info("ZzZzz..")

        log.info("Waiting for %d seconds before checking again...", args.interval)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
