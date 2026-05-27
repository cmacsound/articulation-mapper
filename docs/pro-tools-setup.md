# Pro Tools setup

This is the one-time setup that makes Articulation Mapper actually do anything in Pro Tools. Skip it and the patch names you so carefully built will not appear in the program selector.

There are three stages, in order:

1. **Audio MIDI Setup** (macOS), register the device so Pro Tools can see it
2. **Install** the `.midnam` and `.middev`, so Pro Tools knows the patch names
3. **Pro Tools wiring**, route a track to both your instrument and the named MIDI device

The whole chain depends on one rule:

> The **Manufacturer** and **Model** strings must match exactly across all three stages: the `.middev` file, the `.midnam` file, and the External Device created in Audio MIDI Setup.

If they don't match, Pro Tools won't link the patch names to the device, and the program selector will keep showing raw numbers.

---

## Stage 1, Audio MIDI Setup

Pro Tools doesn't invent MIDI devices. It reads them from macOS's MIDI Studio, which lives in **Audio MIDI Setup**.

1. Open `/Applications/Utilities/Audio MIDI Setup.app`.
2. Menu, **Window, Show MIDI Studio** (or `Cmd+2`).
3. Click the **Add** button (the `+` icon) and choose **External Device**.
4. Double-click the new device to open its inspector.
5. Set the fields:
   - **Name**, what you want to see in Pro Tools (e.g., `Articulations`, `FP-3`)
   - **Manufacturer**, must match the `Manufacturer` in your `.midnam` and `.middev` (e.g., `UACC`, `Roland`)
   - **Model**, must match the `Model` in your `.midnam` and `.middev` (e.g., `Articulations`, `FP-3`)
6. Connect the External Device's MIDI input arrow to the output of your interface or virtual MIDI port.

> Screenshot placeholder, MIDI Studio window with an External Device named "Articulations", Manufacturer "UACC", Model "Articulations"

### Shortcut, import an example configuration

`examples/midi-configurations/Articulation Mapper Example.mcfg` is a ready-made MIDI Studio layout containing a Euphonix control surface plus three External Devices (`Articulations`, `FP-3`, `FP-3 Perc`) wired with the correct Manufacturer/Model strings.

To use it:

1. Audio MIDI Setup, **File, Import**, then choose the `.mcfg` file.
2. Confirm the new devices appear in MIDI Studio.

Treat it as a reference. Rename or delete devices you don't need, and edit the Manufacturer/Model fields if you're targeting a different instrument.

---

## Stage 2, install the midnam and middev

Use the **Install to PT** button in Articulation Mapper, or copy the files manually:

```
/Library/Audio/MIDI Patch Names/Avid/[Manufacturer]/[Manufacturer] [Model].midnam
/Library/Audio/MIDI Devices/[Manufacturer].middev
```

Both targets are root-owned; the in-app installer handles the privileged copy.

If you're installing from the bundled examples manually:

| Source                                                | Destination                                                                         |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `examples/midnam/UACC Articulations.midnam`           | `/Library/Audio/MIDI Patch Names/Avid/UACC/UACC Articulations.midnam`               |
| `examples/middev/UACC.middev`                         | `/Library/Audio/MIDI Devices/UACC.middev`                                           |
| `examples/midnam/Roland FP-3.midnam`                  | `/Library/Audio/MIDI Patch Names/Avid/Roland/Roland FP-3.midnam`                    |
| `examples/midnam/Roland FP-3 Perc.midnam`             | `/Library/Audio/MIDI Patch Names/Avid/Roland/Roland FP-3 Perc.midnam`               |
| `examples/middev/Roland.middev`                       | `/Library/Audio/MIDI Devices/Roland.middev`                                         |

After installing, **quit and reopen Pro Tools** so it re-scans the patch-name folder.

---

## Stage 3, Pro Tools wiring

### Confirm Pro Tools sees the device

1. Pro Tools menu, **Setup, MIDI, Input Devices**.
2. The list should include the External Device names you created in Stage 1 (e.g., `FP-3`, `Articulations`).
3. Tick the box next to each device you want to use. If a device is missing, the Manufacturer/Model strings don't match, or Pro Tools wasn't restarted after Stage 2.

> Screenshot placeholder, MIDI Input Devices dialog with `Articulations` and `FP-3` checked

### Route a track to the named device (the key step)

For patch names to appear in the program selector, the track that triggers the instrument must also send its MIDI to the named device you registered. This is what publishes program changes through the named-device path so Pro Tools can label them.

On an Instrument or MIDI track:

1. Click the track's **MIDI Output** selector.
2. Choose the primary destination as usual, the virtual instrument plug-in or the external synth.
3. **Hold `Ctrl` and click the Output selector again**, then choose the named MIDI device (e.g., `Articulations` or `FP-3`).

The track now sends MIDI to **both** outputs. The instrument plays as before, and the named device receives the program changes so Pro Tools can show patch names in the program selector.

> Screenshot placeholder, track Output selector showing two assignments, the instrument and the named MIDI device

### Pick patches by name

On the same track, the **Program** / **Patch Select** control now shows your named patches grouped by Manufacturer and Model. Picking a patch sends the underlying CC0/CC32/Program Change values defined in the `.midnam`.

---

## Troubleshooting

**Patch names don't appear in the program selector.**
- Check the Manufacturer and Model strings match exactly across `.middev`, `.midnam`, and the Audio MIDI Setup External Device. Pay attention to case and spaces.
- Confirm Pro Tools was restarted after Stage 2.
- Confirm the device is ticked in **Setup, MIDI, Input Devices**.

**Patch names appear, but program changes don't reach the instrument.**
- The track is only routed to the named MIDI device, not to the instrument. Add the second output (Stage 3) so MIDI hits both.

**Articulation maps (UACC) trigger the wrong articulation.**
- UACC selects via CC32 (bank-select LSB) at the `<PatchBank>` level. Confirm your `.midnam` has one bank per articulation, each containing a single patch. The bundled UACC template follows this pattern; see the bank-structure note in the README.
