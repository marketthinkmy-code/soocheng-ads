# -*- coding: utf-8 -*-
"""READ-ONLY: download the two new SC videos via the service account, print duration and dump small JPEG frames
(base64, one every STEP seconds) so the pairing «Drive file ↔ script (Video 3 / Video 4)» and on-screen content
(subtitles, the IG-result pop-up) can be verified before any build. Nothing is written to Meta / Notion."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

from adbot.clients.drive import DriveClient
from adbot.settings import REPO_ROOT, load_settings

FILES = ["1v_J3jEexvznTRG5OICdafVWMuwART0Et", "1blBpVRCN97pVUVf1S5ZCw1M-wt1vlpjM", "1rl11onKtFkAeJd7tpmlK_zGczLjWNwKM", "17NYqm825oTTtVwqJ592laPn1G5AjAvMq", "1Lb4N4XKHbu17L--dDnN2yBvqgQuBmV5-"]  # 11/10 SA-readable copies of SC SEP 01-A02 / 02-A02 / 03-A02 / 04# / 05-A02
STEP = 3
if not shutil.which("ffmpeg"):
    subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "ffmpeg"], check=True)
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
d = DriveClient(s.secrets.google_sa_json)
tmp = Path("/tmp/vf")
for fid in FILES:
    p = d.download_file(fid, tmp / f"{fid}.mp4")
    meta = json.loads(subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(p)],
                                     capture_output=True, text=True).stdout)
    dur = float(meta["format"]["duration"])
    v = next(x for x in meta["streams"] if x["codec_type"] == "video")
    print(f"FILE {fid} · {dur:.1f}s · {v['width']}x{v['height']} · {p.stat().st_size} bytes")
    out = tmp / fid
    out.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "fps=1/2,scale=270:-2", "-q:v", "7", str(out / "f%03d.jpg")], check=True)
    for f in sorted(out.glob("f*.jpg")):
        print(f"FRAME {fid} {f.stem} {base64.b64encode(f.read_bytes()).decode()}")
print("FRAMES DONE (read-only)")
