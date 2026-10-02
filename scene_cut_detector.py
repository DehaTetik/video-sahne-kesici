"""
Video Sahne Kesici (Scene Cut Detector)
---------------------------------------
Bir videoyu "zaman boyutlu matris dizisi" olarak ele alir.
Ardisik iki kare arasindaki mutlak farki (absdiff) hesaplayarak
kamera acisinin / sahnenin degistigi anlari (cut) tespit eder.
"""

import os
import sys
import argparse
import cv2
import numpy as np


def detect_scene_cuts(video_path: str,
                      threshold: float = 30.0,
                      min_scene_duration: float = 0.5,
                      output_dir: str = "output",
                      save_frames: bool = True) -> dict:
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video bulunamadi: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Video acilamadi: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 25.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    print("=" * 60)
    print(f"Video        : {video_path}")
    print(f"FPS          : {fps:.2f}")
    print(f"Toplam Kare  : {total_frames}")
    print(f"Sure         : {duration:.2f} sn")
    print(f"Esik         : {threshold}")
    print("=" * 60)

    if save_frames:
        os.makedirs(output_dir, exist_ok=True)

    cuts = []
    prev_gray = None
    frame_idx = 0
    min_frame_gap = max(1, int(min_scene_duration * fps))
    last_cut_frame = -min_frame_gap

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            mean_diff = float(np.mean(diff))

            if (mean_diff > threshold and
                    (frame_idx - last_cut_frame) >= min_frame_gap):
                timestamp = frame_idx / fps
                cuts.append({
                    "frame": frame_idx,
                    "timestamp": round(timestamp, 3),
                    "score": round(mean_diff, 3)
                })
                last_cut_frame = frame_idx

                print(f"[CUT] Kare {frame_idx:>6} | "
                      f"{timestamp:7.3f} sn | Skor: {mean_diff:6.2f}")

                if save_frames:
                    out_name = f"cut_{frame_idx:06d}_{timestamp:.3f}s.jpg"
                    out_path = os.path.join(output_dir, out_name)
                    cv2.imwrite(out_path, frame)

        prev_gray = gray
        frame_idx += 1

    cap.release()

    print("-" * 60)
    print(f"Toplam {len(cuts)} sahne kesmesi bulundu.")
    print("=" * 60)

    return {
        "fps": fps,
        "total_frames": total_frames,
        "duration": duration,
        "cuts": cuts
    }


def _cli():
    parser = argparse.ArgumentParser(
        description="Video Sahne Kesici - absdiff tabanli cut detector"
    )
    parser.add_argument("video", help="Analiz edilecek video dosyasi")
    parser.add_argument("-t", "--threshold", type=float, default=30.0,
                        help="Ortalama fark esigi (varsayilan: 30)")
    parser.add_argument("-d", "--min-duration", type=float, default=0.5,
                        help="Iki cut arasi min sure sn (varsayilan: 0.5)")
    parser.add_argument("-o", "--output", default="output",
                        help="Kesme karelerinin kayit klasoru")
    parser.add_argument("--no-save", action="store_true",
                        help="Kesme karelerini diske kaydetme")
    args = parser.parse_args()

    try:
        detect_scene_cuts(
            video_path=args.video,
            threshold=args.threshold,
            min_scene_duration=args.min_duration,
            output_dir=args.output,
            save_frames=not args.no_save
        )
    except Exception as e:
        print(f"Hata: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()