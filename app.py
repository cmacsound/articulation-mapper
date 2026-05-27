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
import shlex
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify, send_file

from lib.midnam import generate_midnam, parse_midnam
from lib.middev import generate_middev, parse_middev

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
PROJECTS_DIR = DATA_DIR / "projects"

# Pro Tools install paths on macOS.
# .middev is registered in /Library/Audio/MIDI Devices, alongside
# Apple's "Digidesign Device List.middev". .midnam files live under
# /Library/Audio/MIDI Patch Names/Avid/<Manufacturer>/, the location
# Pro Tools scans for patch names.
PROTOOLS_MIDDEV_DIR = Path("/Library/Audio/MIDI Devices")
PROTOOLS_MIDNAM_DIR = Path("/Library/Audio/MIDI Patch Names/Avid")

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


def _admin_shell(script: str) -> subprocess.CompletedProcess:
    """Run a shell script as administrator via osascript.

    macOS shows its native Authorization dialog. Returns the completed
    process so the caller can branch on returncode.
    """
    quoted = script.replace('\\', '\\\\').replace('"', '\\"')
    applescript = (
        f'do shell script "{quoted}" '
        f'with administrator privileges'
    )
    return subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True, text=True
    )


@app.route("/api/install/preflight", methods=["POST"])
def install_preflight():
    """Check the on-disk middev for a manufacturer/model conflict.

    Returns ``{"ok": True}`` if installing would not collide with a
    different manufacturer or model already registered at the target
    middev path. Returns ``{"ok": False, "conflict": {...}}`` with the
    existing manufacturer/model otherwise, so the UI can surface the
    diff before authentication is requested.
    """
    data = request.get_json() or {}
    manufacturer = (data.get("manufacturer") or "").strip()
    model = (data.get("model") or "").strip()

    if not manufacturer or not model:
        return jsonify({"ok": False, "error":
                        "Manufacturer and Model are both required."}), 400

    middev_path = PROTOOLS_MIDDEV_DIR / f"{manufacturer}.middev"
    if not middev_path.exists():
        return jsonify({"ok": True, "existing": None})

    try:
        existing_devices = parse_middev(middev_path.read_text())
    except Exception as e:
        return jsonify({"ok": False, "error":
                        f"Could not parse existing middev: {e}"}), 400

    mismatched = [
        d for d in existing_devices
        if d.get("manufacturer", "") != manufacturer
    ]
    if mismatched:
        return jsonify({
            "ok": False,
            "conflict": {
                "path": str(middev_path),
                "existing": existing_devices,
                "incoming": {"manufacturer": manufacturer, "model": model},
                "reason": "manufacturer-mismatch",
            }
        })

    return jsonify({"ok": True, "existing": existing_devices})


@app.route("/api/install", methods=["POST"])
def install_to_protools():
    """Install midnam to /Library/Audio/MIDI Patch Names/Avid/<Manufacturer>/
    and middev to /Library/Audio/MIDI Devices/.

    Both targets are root-owned. Files are generated into a temp dir
    first, then a single osascript call moves them into place with
    administrator privileges. The user sees one native macOS auth prompt.
    """
    data = request.get_json() or {}
    manufacturer = (data.get("manufacturer") or "").strip()
    model = (data.get("model") or "").strip()
    author = data.get("author", "Articulation Mapper")
    banks = data.get("banks", [])
    force = bool(data.get("force", False))

    if not manufacturer or not model:
        return jsonify({
            "error": "Manufacturer and Model are both required."
        }), 400
    if not banks:
        return jsonify({"error": "Add at least one articulation."}), 400

    midnam_target_dir = PROTOOLS_MIDNAM_DIR / manufacturer
    midnam_target = midnam_target_dir / f"{manufacturer} {model}.midnam"
    middev_target = PROTOOLS_MIDDEV_DIR / f"{manufacturer}.middev"

    midnam_xml = generate_midnam(manufacturer, model, banks, author)

    incoming_device = {"manufacturer": manufacturer, "model": model}
    if middev_target.exists():
        try:
            existing_devices = parse_middev(middev_target.read_text())
        except Exception as e:
            return jsonify({
                "error": f"Could not parse existing middev: {e}"
            }), 400

        mismatched = [
            d for d in existing_devices
            if d.get("manufacturer", "") != manufacturer
        ]
        if mismatched and not force:
            return jsonify({
                "error": "manufacturer-mismatch",
                "conflict": {
                    "path": str(middev_target),
                    "existing": existing_devices,
                    "incoming": incoming_device,
                }
            }), 409

        # Force mode replaces the file outright with just the incoming
        # device. Merge mode (matching manufacturer) keeps siblings
        # under the same manufacturer.
        if force:
            merged = [incoming_device]
        else:
            kept = [
                d for d in existing_devices
                if d.get("manufacturer", "") == manufacturer
            ]
            models = {d.get("model", "") for d in kept}
            merged = kept if model in models else kept + [incoming_device]
        middev_xml = generate_middev(merged, author)
    else:
        middev_xml = generate_middev([incoming_device], author)

    with tempfile.TemporaryDirectory(prefix="artmapper_install_") as td:
        td_path = Path(td)
        midnam_tmp = td_path / midnam_target.name
        middev_tmp = td_path / middev_target.name
        midnam_tmp.write_text(midnam_xml)
        middev_tmp.write_text(middev_xml)

        cmd = (
            f"/bin/mkdir -p {shlex.quote(str(midnam_target_dir))} && "
            f"/bin/cp {shlex.quote(str(midnam_tmp))} "
            f"{shlex.quote(str(midnam_target))} && "
            f"/bin/cp {shlex.quote(str(middev_tmp))} "
            f"{shlex.quote(str(middev_target))}"
        )
        result = _admin_shell(cmd)

    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "Install failed"
        if "User canceled" in msg or "(-128)" in msg:
            return jsonify({"error": "Authentication cancelled."}), 403
        return jsonify({"error": msg}), 500

    return jsonify({
        "message": "Installed successfully",
        "midnam_path": str(midnam_target),
        "middev_path": str(middev_target)
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
