#!/usr/bin/env python3
"""
Articulation Mapper, a MIDI patch-name editor for Pro Tools.

A local web GUI for creating and editing .midnam and .middev files
that name MIDI patches and program changes for hardware synths,
sound modules, virtual instruments, and articulation banks.

Usage:
    python app.py
    Then open http://localhost:5000 in your browser.
"""

import json
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify, send_file

from lib.midnam import generate_midnam, parse_midnam
from lib.middev import generate_middev

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
PROJECTS_DIR = DATA_DIR / "projects"

# Pro Tools midnam install path
PROTOOLS_MIDNAM_PATH = Path("/Library/Audio/MIDI Patch Names")

# Ensure data directories exist
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def _safe_child(base: Path, filename: str):
    """Resolve filename inside base, refusing path-traversal attempts."""
    if not filename or "/" in filename or "\\" in filename or "\x00" in filename:
        return None
    candidate = (base / filename).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        return None
    return candidate


@app.before_request
def _block_cross_origin():
    """Reject state-changing requests that don't come from the local UI.

    The app writes to disk, including /Library/Audio/MIDI Patch Names/. Any page
    a user visits while the server is running could otherwise POST to it.
    """
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None
    source = request.headers.get("Origin") or request.headers.get("Referer", "")
    if not source:
        return jsonify({"error": "Missing Origin/Referer"}), 403
    host = urlparse(source).hostname
    if host not in ("127.0.0.1", "localhost"):
        return jsonify({"error": "Cross-origin request blocked"}), 403
    return None


# ── Pages ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Project API ────────────────────────────────────────────────────

@app.route("/api/projects", methods=["GET"])
def list_projects():
    """List all saved projects."""
    projects = []
    for f in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            projects.append({
                "filename": f.name,
                "manufacturer": data.get("manufacturer", ""),
                "model": data.get("model", ""),
                "bank_count": len(data.get("banks", []))
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return jsonify(projects)


@app.route("/api/projects/<filename>", methods=["GET"])
def load_project(filename):
    """Load a specific project."""
    filepath = _safe_child(PROJECTS_DIR, filename)
    if filepath is None or not filepath.exists():
        return jsonify({"error": "Project not found"}), 404
    data = json.loads(filepath.read_text())
    return jsonify(data)


@app.route("/api/projects", methods=["POST"])
def save_project():
    """Save a project. Creates or overwrites."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    manufacturer = data.get("manufacturer", "Unknown")
    model = data.get("model", "Unknown")
    filename = f"{manufacturer} {model}.json".replace("/", "-")

    filepath = _safe_child(PROJECTS_DIR, filename)
    if filepath is None:
        return jsonify({"error": "Invalid manufacturer or model"}), 400
    filepath.write_text(json.dumps(data, indent=2))

    return jsonify({"filename": filepath.name, "message": "Project saved"})


@app.route("/api/projects/<filename>", methods=["DELETE"])
def delete_project(filename):
    """Delete a project."""
    filepath = _safe_child(PROJECTS_DIR, filename)
    if filepath is not None and filepath.exists():
        filepath.unlink()
        return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404


# ── Template API ───────────────────────────────────────────────────

@app.route("/api/templates", methods=["GET"])
def list_templates():
    """List available templates."""
    templates = []
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            templates.append({
                "filename": f.name,
                "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "bank_count": len(data.get("banks", []))
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return jsonify(templates)


@app.route("/api/templates/<filename>", methods=["GET"])
def load_template(filename):
    """Load a specific template."""
    filepath = _safe_child(TEMPLATES_DIR, filename)
    if filepath is None or not filepath.exists():
        return jsonify({"error": "Template not found"}), 404
    data = json.loads(filepath.read_text())
    return jsonify(data)


# ── Export API ─────────────────────────────────────────────────────

@app.route("/api/export/midnam", methods=["POST"])
def export_midnam():
    """Generate and return a midnam XML file."""
    data = request.get_json()
    manufacturer = data.get("manufacturer", "")
    model = data.get("model", "")
    author = data.get("author", "Articulation Mapper")
    banks = data.get("banks", [])

    xml = generate_midnam(manufacturer, model, banks, author)
    filename = f"{manufacturer} {model}.midnam".replace("/", "-")

    # Write to temp file for download
    tmp = BASE_DIR / "data" / filename
    tmp.write_text(xml)
    return send_file(tmp, as_attachment=True, download_name=filename,
                     mimetype="application/xml")


@app.route("/api/export/middev", methods=["POST"])
def export_middev():
    """Generate and return a middev XML file."""
    data = request.get_json()
    manufacturer = data.get("manufacturer", "")
    model = data.get("model", "")
    author = data.get("author", "Articulation Mapper")

    devices = [{"manufacturer": manufacturer, "model": model}]
    xml = generate_middev(devices, author)
    filename = f"{manufacturer}.middev".replace("/", "-")

    tmp = BASE_DIR / "data" / filename
    tmp.write_text(xml)
    return send_file(tmp, as_attachment=True, download_name=filename,
                     mimetype="application/xml")


@app.route("/api/preview/midnam", methods=["POST"])
def preview_midnam():
    """Generate midnam XML and return as text for preview."""
    data = request.get_json()
    manufacturer = data.get("manufacturer", "")
    model = data.get("model", "")
    author = data.get("author", "Articulation Mapper")
    banks = data.get("banks", [])

    xml = generate_midnam(manufacturer, model, banks, author)
    return jsonify({"xml": xml})


@app.route("/api/preview/middev", methods=["POST"])
def preview_middev():
    """Generate middev XML and return as text for preview."""
    data = request.get_json()
    manufacturer = data.get("manufacturer", "")
    model = data.get("model", "")
    author = data.get("author", "Articulation Mapper")

    devices = [{"manufacturer": manufacturer, "model": model}]
    xml = generate_middev(devices, author)
    return jsonify({"xml": xml})


# ── Install to Pro Tools ──────────────────────────────────────────

@app.route("/api/install", methods=["POST"])
def install_to_protools():
    """Install midnam and middev files to Pro Tools path."""
    data = request.get_json()
    manufacturer = data.get("manufacturer", "")
    model = data.get("model", "")
    author = data.get("author", "Articulation Mapper")
    banks = data.get("banks", [])

    # Create manufacturer subfolder
    install_dir = PROTOOLS_MIDNAM_PATH / manufacturer
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return jsonify({
            "error": f"Permission denied writing to {install_dir}. "
                     f"Try running with sudo or check folder permissions."
        }), 403

    # Generate and write midnam
    midnam_xml = generate_midnam(manufacturer, model, banks, author)
    midnam_file = install_dir / f"{manufacturer} {model}.midnam"
    midnam_file.write_text(midnam_xml)

    # Generate and write middev
    devices = [{"manufacturer": manufacturer, "model": model}]
    middev_xml = generate_middev(devices, author)
    middev_file = install_dir / f"{manufacturer}.middev"

    # If middev already exists, check if this device is already in it
    if middev_file.exists():
        existing = middev_file.read_text()
        if f'Model="{model}"' not in existing:
            # Append device to existing middev (before closing tag)
            from lib.middev import parse_middev
            existing_devices = parse_middev(existing)
            existing_devices.append({"manufacturer": manufacturer, "model": model})
            middev_xml = generate_middev(existing_devices, author)
    middev_file.write_text(middev_xml)

    return jsonify({
        "message": "Installed successfully",
        "midnam_path": str(midnam_file),
        "middev_path": str(middev_file)
    })


# ── Import API ─────────────────────────────────────────────────────

@app.route("/api/import/midnam", methods=["POST"])
def import_midnam():
    """Import a midnam file and return project data."""
    if "file" in request.files:
        f = request.files["file"]
        xml_content = f.read().decode("utf-8")
    elif request.is_json:
        xml_content = request.get_json().get("xml", "")
    else:
        return jsonify({"error": "No file or XML provided"}), 400

    try:
        data = parse_midnam(xml_content)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed to parse midnam: {str(e)}"}), 400


@app.route("/api/import/text", methods=["POST"])
def import_text():
    """Import a text list of articulation names and generate banks.

    Expects JSON with:
        - text: newline-separated articulation names
        - start_cc32: starting CC32 value (default 1)
        - start_pc: starting program change value (default matches cc32)
    """
    data = request.get_json()
    text = data.get("text", "")
    start_cc32 = data.get("start_cc32", 1)
    start_pc = data.get("start_pc", None)

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    banks = []

    for i, name in enumerate(lines):
        cc32 = start_cc32 + i
        pc = (start_pc + i) if start_pc is not None else cc32
        banks.append({
            "name": name,
            "cc0": None,
            "cc32": cc32,
            "patches": [{
                "number": f"{i + 1:03d}",
                "name": name,
                "program_change": pc
            }]
        })

    return jsonify({"banks": banks})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", "5000"))
    print("\n  Articulation Mapper")
    print(f"  http://localhost:{port}\n")
    app.run(debug=debug, port=port)
