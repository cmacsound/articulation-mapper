# Articulation Mapper

A small, local web tool for naming MIDI patches in Pro Tools. Build `.midnam` files for hardware synths, sound modules, virtual instruments, and articulation banks, so program changes appear by name in the patch selector instead of as raw numbers. A modern alternative to CherryPicker.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Why this exists

Pro Tools reads patch and program names from `.midnam` (MIDI Name Document) files. With one in place, you stop typing cryptic program numbers and start picking patches by name from a drop-down on the MIDI track.

That works for any device that responds to MIDI program changes: a Roland stage piano, a Korg synth, a Kontakt instrument, a sample library articulation set. The same file format covers all of them.

Hand-writing midnam XML is tedious. Existing tools like CherryPicker are aging and macOS-only. This tool keeps the workflow simple: a clean editor in the browser, sane defaults, sensible templates, and one-click install to the right system folder.

## Who this is for

- Composers and sound designers who want articulation banks named instead of numbered.
- Anyone routing MIDI to a hardware synth, sound module, or stage instrument and tired of guessing which program is which.
- Engineers who need to share a patch list with a session collaborator without exporting a screenshot of the manual.

## Quick start

Requires Python 3.9 or newer.

```bash
git clone https://github.com/cmacsound/articulation-mapper.git
cd articulation-mapper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser.

## Pro Tools setup (required, do this first)

Pro Tools won't show patch names by name unless three pieces line up: a macOS MIDI Studio device, an installed `.middev`/`.midnam` pair, and a Pro Tools track routed to the named device alongside its instrument. The Manufacturer and Model strings must match exactly across all three.

The full walkthrough, with the Audio MIDI Setup steps, the install paths, and the Ctrl-click second-output trick, is in [docs/pro-tools-setup.md](docs/pro-tools-setup.md). A reference MIDI Studio configuration ships in [examples/midi-configurations/](examples/midi-configurations/) that you can import to skip the manual device creation.

## What it does

- Generates `.midnam` files that Pro Tools reads as patch and program name lists
- Generates companion `.middev` files that register your device (hardware or virtual) as a MIDI device
- Maps patch and articulation names to CC0/CC32 (bank select MSB/LSB) and program change values
- One-click install to the Pro Tools system folders for Pro Tools (macOS only)

## Features

**Device setup.** Set Manufacturer, Model, and Author. These become the identity of your midnam file.

**Patch table.** Inline editing of name, CC0 (MSB), CC32 (LSB), and program change. Add single rows or bulk-add from a text list. Delete, duplicate, drag-to-reorder. Filter and search across all entries. Works equally well for hardware patch lists and sample-library articulation banks.

**Templates.** Built-in templates ship with the tool: Roland FP-3, Roland FP-3 Perc, and UACC Standard Articulations (105 articulations). Select from the Template dropdown and click Load, then edit the manufacturer, model, and entries to match your device. See [examples/](examples/) for the raw `.midnam`, `.middev`, and `.mcfg` versions.

**Import.** Open any existing `.midnam` file and edit it. Or paste a list of patch names, one per line, and the tool auto-numbers them.

**Export and install.** Download `.midnam` and `.middev` files, preview the XML before exporting, or write directly to the Pro Tools system folder.

**Project files.** Save and load projects as JSON. Stored locally in `data/projects/`.

## File structure

```
articulation-mapper/
├── app.py                          # Flask server
├── requirements.txt                # Python dependencies
├── lib/
│   ├── midnam.py                   # Midnam XML generation and parsing
│   └── middev.py                   # Middev XML generation and parsing
├── templates/
│   └── index.html                  # Web UI
├── static/
│   ├── css/style.css               # Styling
│   └── js/app.js                   # Client-side logic
├── data/
│   ├── templates/                  # Built-in templates
│   │   ├── uacc-standard.json
│   │   ├── roland-fp-3.json
│   │   └── roland-fp-3-perc.json
│   └── projects/                   # Saved user projects (gitignored)
├── docs/
│   └── pro-tools-setup.md          # Audio MIDI Setup + Pro Tools wiring guide
└── examples/
    ├── midnam/                     # Reference .midnam files (Roland FP-3, UACC)
    ├── middev/                     # Reference .middev files
    └── midi-configurations/        # Audio MIDI Setup .mcfg you can import
```

## Pro Tools integration

After exporting or installing, quit and reopen Pro Tools. Your patch names will appear in the MIDI track's program/patch selector under the manufacturer and model you specified, **provided** you've also completed the Audio MIDI Setup and track-routing steps in [docs/pro-tools-setup.md](docs/pro-tools-setup.md).

The install paths on macOS are:

```
/Library/Audio/MIDI Patch Names/Avid/[Manufacturer]/[Manufacturer] [Model].midnam
/Library/Audio/MIDI Devices/[Manufacturer].middev
```

Both targets are root-owned. The Install button writes the generated files to a temp location, then runs a single privileged copy via `osascript`. macOS shows its native authentication dialog. The server itself never runs as root.

If a `[Manufacturer].middev` already exists with a different manufacturer attribute, the installer aborts and surfaces the conflict instead of silently overwriting. Matching manufacturer with a new model is merged in.

### Bank structure

Pro Tools' midnam parser only honours bank-select MIDI commands on `<PatchBank>` elements, never on individual `<Patch>` elements. CC0/CC32 differentiation therefore lives at the bank level. For articulation maps such as UACC, where each row is selected by a unique CC32, that means one `<PatchBank>` per row, each containing a single patch. The bundled UACC template follows this pattern.

## Keyboard shortcuts

- `Cmd+S` (or `Ctrl+S`), save project
- `Esc`, close modal

## Platform notes

The editor runs on any platform with Python 3.9+. The Install to PT button writes to a macOS system path and only works on macOS. On Windows or Linux, use Export and place the files in your Pro Tools install location manually.

## Credits and acknowledgments

The UACC (Unified Articulation Controller Code) standard was designed by Spitfire Audio. The bundled UACC template implements that standard.

`.midnam` and `.middev` are MIDI Manufacturers Association formats, used by Pro Tools and other DAWs. This project is not affiliated with or endorsed by Avid Technology, Inc. Pro Tools is a trademark of Avid.

## License

MIT. See [LICENSE](LICENSE).

## Author

Curtis R. Macdonald, [curtismacdonald.com](https://curtismacdonald.com)
