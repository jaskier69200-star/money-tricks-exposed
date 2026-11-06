"""Make the two bass hits of the punch cards with FFmpeg alone, so that no sound in this public repo is someone else's.

    python tools/make_sfx.py   → assets/sfx/impact-bass-1.mp3 and impact-bass-2.mp3
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import find_ffmpeg  # noqa: E402

# file: seconds, base pitch (Hz), how far above it the hit starts (Hz), decay, drive (saturation: a phone speaker
# cannot play pure sub-bass, the harmonics are what it hears)
HITS = {"impact-bass-1.mp3": (2.1, 50, 70, 0.3, 3.0), "impact-bass-2.mp3": (2.6, 42, 90, 0.2, 3.5)}


def expression(seconds, base, sweep, decay, drive):
    tone = f"tanh({drive}*sin(2*PI*({base}*t+{sweep}*(1-exp(-14*t))/14)))*exp(-{decay}*t)"
    knock = "0.45*sin(2*PI*(160*t+600*(1-exp(-60*t))/60))*exp(-25*t)"
    crack = "0.6*(2*random(0)-1)*exp(-40*t)"  # the first instant: what makes it a hit rather than a hum
    envelope = f"min(1,t/0.004)*min(1,({seconds}-t)/0.5)"
    return f"({tone}+{knock}+{crack})*{envelope}*1.4"


def main():
    for name, (seconds, *shape) in HITS.items():
        source = f"aevalsrc='{expression(seconds, *shape)}':s=44100:d={seconds}"
        subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", source, "-af", "alimiter=limit=0.95:level=false",
                        "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", str(ROOT / "assets" / "sfx" / name)], check=True)
        print(name, seconds, "s")


if __name__ == "__main__":
    main()
