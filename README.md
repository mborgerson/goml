Get off my lawn!
================

Stop pesky birds from eating your new ryegrass seed! Turn the sprinklers on
for a few seconds when any birds are seen by your IP camera. It works a hell
of a lot better than those spinning reflectors, and keeps your soil nice and
moist.

* Assumes: you have an RTSP stream and a B-hyve controller
* Needs: docker, ffmpeg
* Run:
```bash
docker build -t detector ./detector
docker build -t sprinkler ./sprinkler
cp sprinkler/config.example.js bhyve-config.js # Edit accordingly
python goml.py --camera="rtsp://..."
```
