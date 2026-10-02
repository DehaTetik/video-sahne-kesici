"""
Sahne Kesici (Scene Splitter)
-----------------------------
detect_scene_cuts() ile bulunan kesme noktalarını kullanarak
videoyu ayrı ayrı sahne dosyalarına böler.

Her sahne: scene_001.mp4, scene_002.mp4, ...
"""

import os
import cv2


def split_scenes(video_path: str,
                 cuts: list,
                 output_dir: str = "scenes",
                 prefix: str = "scene") -> list:
    """
    Videoyu, verilen cut listesine göre parçalara böler.

    Parametreler
    ------------
    video_path : str
        Kaynak video dosyası.
    cuts : list
        detect_scene_cuts() dönüşündeki 'cuts' listesi.
        Her eleman: {"frame": int, "timestamp": float, "score": float}
    output_dir : str
        Sahnelerin kaydedileceği klasör.
    prefix : str
        Dosya isim ön eki (scene_001.mp4).

    Dönüş
    -----
    list : Kaydedilen sahne dosyalarının yolları.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video bulunamadi: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Video acilamadi: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Kesme kare numaralarını topla ve sırala
    cut_frames = sorted({0} | {c["frame"] for c in cuts} | {total_frames})

    # Sahne aralıklarını oluştur: [(0, 150), (150, 320), ...]
    segments = []
    for i in range(len(cut_frames) - 1):
        start = cut_frames[i]
        end = cut_frames[i + 1]
        if end > start:  # boş sahne olmasın
            segments.append((start, end))

    print(f"[SPLIT] {len(segments)} sahne kesilecek.")

    # VideoWriter için codec (mp4v = geniş uyumlu)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    saved = []
    for idx, (start, end) in enumerate(segments, start=1):
        out_name = f"{prefix}_{idx:03d}.mp4"
        out_path = os.path.join(output_dir, out_name)

        writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        for _ in range(start, end):
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)
        writer.release()

        duration = (end - start) / fps
        print(f"[SPLIT] {out_name}  |  "
              f"kare {start}-{end}  |  {duration:.2f} sn")

        saved.append(out_path)

    cap.release()
    print(f"[SPLIT] Toplam {len(saved)} sahne kaydedildi -> {output_dir}/")
    return saved