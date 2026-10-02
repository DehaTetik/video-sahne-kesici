"""
Flask Web Arayuzu
------------------
Kullanici video yukler -> sunucu detect_scene_cuts() calistirir
-> sonuclar JSON olarak doner -> index.html'de gosterilir.
"""

import os
import uuid
from flask import (Flask, render_template, request, jsonify,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename

from scene_cut_detector import detect_scene_cuts

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXT = {"mp4", "avi", "mov", "mkv", "webm"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024


def allowed_file(name: str) -> bool:
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    if "video" not in request.files:
        return jsonify({"ok": False, "error": "Video dosyasi gonderilmedi."}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "Dosya adi bos."}), 400

    if not allowed_file(file.filename):
        return jsonify({"ok": False,
                        "error": "Desteklenmeyen format."}), 400

    try:
        threshold = float(request.form.get("threshold", 30))
        min_dur = float(request.form.get("min_duration", 0.5))
    except ValueError:
        return jsonify({"ok": False, "error": "Esik degeri sayi olmali."}), 400

    safe_name = secure_filename(file.filename)
    unique = uuid.uuid4().hex[:8]
    stored_name = f"{unique}_{safe_name}"
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
    file.save(video_path)

    out_dir = os.path.join(app.config["OUTPUT_FOLDER"], unique)
    os.makedirs(out_dir, exist_ok=True)

    try:
        result = detect_scene_cuts(
            video_path=video_path,
            threshold=threshold,
            min_scene_duration=min_dur,
            output_dir=out_dir,
            save_frames=True
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    frames = []
    for fname in sorted(os.listdir(out_dir)):
        frames.append({
            "name": fname,
            "url": url_for("serve_output", sub=unique, filename=fname)
        })

    return jsonify({
        "ok": True,
        "fps": round(result["fps"], 3),
        "total_frames": result["total_frames"],
        "duration": round(result["duration"], 3),
        "cut_count": len(result["cuts"]),
        "cuts": result["cuts"],
        "frames": frames
    })


@app.route("/output/<sub>/<path:filename>")
def serve_output(sub, filename):
    return send_from_directory(os.path.join(app.config["OUTPUT_FOLDER"], sub), filename)


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)