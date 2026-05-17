# Examples

Real `.midnam` and `.middev` files you can use as references or templates.

## Files

- **Roland FP-3.midnam**, full patch list for the Roland FP-3 stage piano. A typical hardware-synth patch map.
- **Roland FP-3 Perc.midnam**, percussion preset list for the Roland FP-3.
- **Roland.middev**, device registration for both Roland models above.

These show what a finished hardware patch list looks like. The same approach works for any device that responds to MIDI program changes: synths, sound modules, virtual instruments, or articulation banks.

## Use them as templates (in-app)

The Roland files are also available from the **Template** dropdown in the editor as `Roland FP-3` and `Roland FP-3 Perc`. Select one, click **Load**, then change the Manufacturer, Model, and patch entries to match your own device. Save under a new project name.

## Use them as raw imports

If you'd rather edit the XML directly:

1. Click **Import Midnam** in the toolbar.
2. Select one of the `.midnam` files in this folder.
3. Edit Manufacturer, Model, and articulation rows.
4. **Export** or **Install to PT** when done.

## Notes

Patch names are taken from the Roland FP-3 user manual. They are factual data, not creative work.

The `Roland.middev` registers two device types in one file. When you install your own midnam to Pro Tools, the editor merges new device entries into any existing `.middev` for that manufacturer rather than overwriting it.
