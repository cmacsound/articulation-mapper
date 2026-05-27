# Examples

Reference files you can use as starting points or import directly. Organized by file type.

```
examples/
├── midnam/                  # MIDI patch-name documents
├── middev/                  # MIDI device registrations
└── midi-configurations/     # Audio MIDI Setup studio layouts (.mcfg)
```

## midnam/

- **Roland FP-3.midnam**, full patch list for the Roland FP-3 stage piano.
- **Roland FP-3 Perc.midnam**, percussion preset list for the Roland FP-3.
- **UACC Articulations.midnam**, the Spitfire UACC standard articulation set, flat program-change form.

The bundled in-app **UACC Standard Articulations** template (Template dropdown) uses the per-bank CC32 form, which is what UACC actually requires for articulation triggering in Pro Tools. The flat `.midnam` here is provided as a raw reference; for working sessions, prefer the in-app template.

## middev/

- **Roland.middev**, registers `Roland FP-3` and `Roland FP-3 Perc` as devices.
- **UACC.middev**, registers `UACC, Articulations` as a device.

## midi-configurations/

- **Articulation Mapper Example.mcfg**, an Audio MIDI Setup studio layout. Contains a Euphonix MIDI control surface plus three External Devices (`Articulations`, `FP-3`, `FP-3 Perc`) wired with the exact Manufacturer/Model strings the bundled `.middev` and `.midnam` files use.

Import via Audio MIDI Setup, **File, Import**, then pick the file. See [`docs/pro-tools-setup.md`](../docs/pro-tools-setup.md) for the full workflow.

## Use them as in-app templates

`Roland FP-3`, `Roland FP-3 Perc`, and `UACC Standard Articulations` are also available from the **Template** dropdown in the editor. Load one, change Manufacturer/Model/entries, save under a new project name.

## Use them as raw imports

If you'd rather edit the XML directly:

1. Click **Import Midnam** in the toolbar.
2. Select one of the `.midnam` files in `midnam/`.
3. Edit Manufacturer, Model, and articulation rows.
4. **Export** or **Install to PT** when done.

## Notes

Roland FP-3 patch names are taken from the FP-3 user manual. They are factual data, not creative work.

The `Roland.middev` registers two device types in one file. When you install your own midnam to Pro Tools, the editor merges new device entries into any existing `.middev` for that manufacturer rather than overwriting it.
