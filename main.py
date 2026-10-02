"""
Ana Giris Noktasi (Unified Entry Point)
---------------------------------------
Kullanim:
    python main.py cli  video.mp4 [--threshold 30] [--split]
    python main.py web
"""

import sys
import argparse


def run_cli(args):
    from scene_cut_detector import detect_scene_cuts

    print(f"[CLI] Video: {args.video}")
    result = detect_scene_cuts(
        video_path=args.video,
        threshold=args.threshold,
        min_scene_duration=args.min_duration,
        output_dir=args.output,
        save_frames=not args.no_save
    )

    # --- Sahneleri de kes ---
    if args.split:
        from scene_splitter import split_scenes

        scenes_dir = args.scenes_dir
        split_scenes(
            video_path=args.video,
            cuts=result["cuts"],
            output_dir=scenes_dir,
            prefix="scene"
        )
        print(f"\n[CLI] Sahneler kaydedildi -> {scenes_dir}/")

    print(f"\nOzet: {len(result['cuts'])} kesme, "
          f"{result['duration']:.2f} sn, {result['fps']:.2f} FPS")
    return 0


def run_web(args):
    from app import app

    print(f"[WEB] Sunucu baslatiliyor: http://{args.host}:{args.port}")
    print("[WEB] Durdurmak icin Ctrl+C")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Video Sahne Kesici - Birlesik giris noktasi"
    )
    sub = parser.add_subparsers(dest="mode", help="Calisma modu")

    # ---- CLI ----
    p_cli = sub.add_parser("cli", help="Komut satirinda video analiz et")
    p_cli.add_argument("video", help="Analiz edilecek video dosyasi")
    p_cli.add_argument("-t", "--threshold", type=float, default=30.0,
                       help="Ortalama fark esigi (varsayilan: 30)")
    p_cli.add_argument("-d", "--min-duration", type=float, default=0.5,
                       help="Iki cut arasi min sure sn (varsayilan: 0.5)")
    p_cli.add_argument("-o", "--output", default="output",
                       help="Kesme kareleri klasoru (varsayilan: output)")
    p_cli.add_argument("--no-save", action="store_true",
                       help="Kesme karelerini diske kaydetme")
    p_cli.add_argument("--split", action="store_true",
                       help="Videoyu ayrica sahnelere bol (scene_001.mp4 ...)")
    p_cli.add_argument("--scenes-dir", default="scenes",
                       help="Sahnelerin kayit klasoru (varsayilan: scenes)")
    p_cli.set_defaults(func=run_cli)

    # ---- Web ----
    p_web = sub.add_parser("web", help="Flask web arayuzunu baslat")
    p_web.add_argument("--host", default="127.0.0.1")
    p_web.add_argument("--port", type=int, default=5000)
    p_web.add_argument("--debug", action="store_true")
    p_web.set_defaults(func=run_web)

    return parser


def main():
    parser = build_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        print("\nOrnek kullanim:")
        print("  python main.py cli video.mp4 --split")
        print("  python main.py web")
        return 0

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())