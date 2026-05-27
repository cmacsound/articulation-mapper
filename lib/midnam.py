"""
Midnam XML generator for Pro Tools articulation mapping.

Generates MIDINameDocument XML files (.midnam) that Pro Tools reads
to populate patch/program name lists for MIDI tracks.

Pro Tools' midnam parser only accepts ``<MIDICommands>`` on
``<PatchBank>``, never on a ``<Patch>``. So even when each row has a
unique CC32 (UACC, articulation maps), every CC32-differentiated
entry gets its own ``<PatchBank>`` containing a single patch.
"""

from xml.sax.saxutils import escape


def generate_midnam(manufacturer, model, banks, author="Articulation Mapper"):
    """Generate a Pro Tools compatible .midnam XML string.

    Args:
        manufacturer: Device manufacturer name (e.g., "UACC", "Spitfire")
        model: Device model name (e.g., "Articulations", "BBC Strings")
        banks: List of dicts, each with:
            - name: Bank/articulation name
            - cc0: Bank Select MSB value (int or None)
            - cc32: Bank Select LSB value (int or None)
            - patches: List of dicts with:
                - number: Display number string
                - name: Patch name
                - program_change: Program change number (int)
        author: Author tag for the midnam file

    Returns:
        XML string of the complete midnam document.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE MIDINameDocument PUBLIC '
                 '"-//MIDI Manufacturers Association//DTD MIDINameDocument 1.0//EN" "">')
    lines.append('')
    lines.append('<MIDINameDocument>')

    if author:
        lines.append(f'\t<Author>{escape(author)}</Author>')

    lines.append('\t<MasterDeviceNames>')
    lines.append(f'\t\t<Manufacturer>{escape(manufacturer)}</Manufacturer>')
    lines.append(f'\t\t<Model>{escape(model)}</Model>')

    channel_set_name = "Programs"
    lines.append('\t\t<CustomDeviceMode Name="" >')
    lines.append('\t\t\t<ChannelNameSetAssignments>')
    for ch in range(1, 17):
        lines.append(f'\t\t\t\t<ChannelNameSetAssign Channel="{ch}" '
                     f'NameSet="{escape(channel_set_name)}" />')
    lines.append('\t\t\t</ChannelNameSetAssignments>')
    lines.append('\t\t</CustomDeviceMode>')

    lines.append(f'\t\t<ChannelNameSet Name="{escape(channel_set_name)}" >')
    lines.append('\t\t\t<AvailableForChannels>')
    for ch in range(1, 17):
        lines.append(f'\t\t\t\t<AvailableChannel Channel="{ch}" Available="true" />')
    lines.append('\t\t\t</AvailableForChannels>')

    for bank in banks:
        bank_name = escape(bank["name"])
        lines.append(f'\t\t\t<PatchBank Name="{bank_name}" >')
        has_cc0 = bank.get("cc0") is not None
        has_cc32 = bank.get("cc32") is not None
        if has_cc0 or has_cc32:
            lines.append('\t\t\t\t<MIDICommands>')
            if has_cc0:
                lines.append(f'\t\t\t\t\t<ControlChange Control="0" '
                             f'Value="{bank["cc0"]}" />')
            if has_cc32:
                lines.append(f'\t\t\t\t\t<ControlChange Control="32" '
                             f'Value="{bank["cc32"]}" />')
            lines.append('\t\t\t\t</MIDICommands>')
        lines.append(f'\t\t\t\t<UsesPatchNameList Name="{bank_name}" />')
        lines.append('\t\t\t</PatchBank>')
    lines.append('\t\t</ChannelNameSet>')

    for bank in sorted(banks, key=lambda b: b["name"].lower()):
        bank_name = escape(bank["name"])
        lines.append(f'\t\t<PatchNameList Name="{bank_name}" >')
        for patch in bank.get("patches", []):
            patch_name = escape(patch["name"])
            lines.append(f'\t\t\t<Patch Number="{escape(str(patch["number"]))}" '
                         f'Name="{patch_name}" '
                         f'ProgramChange="{patch["program_change"]}" />')
        lines.append('\t\t</PatchNameList>')

    lines.append('\t</MasterDeviceNames>')
    lines.append('</MIDINameDocument>')
    lines.append('')

    return '\n'.join(lines)


def parse_midnam(xml_string):
    """Parse a midnam XML string into a project data structure.

    Args:
        xml_string: Raw XML content of a .midnam file.

    Returns:
        Dict with manufacturer, model, author, and banks list.
    """
    from lxml import etree

    root = etree.fromstring(xml_string.encode('utf-8'))

    author_el = root.find('.//Author')
    author = author_el.text if author_el is not None else ""

    master = root.find('.//MasterDeviceNames')
    manufacturer = master.findtext('Manufacturer', '')
    model = master.findtext('Model', '')

    patch_lists = {}
    for pnl in master.findall('.//PatchNameList'):
        pnl_name = pnl.get('Name', '')
        patches = []
        for patch in pnl.findall('Patch'):
            patches.append({
                "number": patch.get('Number', ''),
                "name": patch.get('Name', ''),
                "program_change": int(patch.get('ProgramChange', 0))
            })
        patch_lists[pnl_name] = patches

    banks = []
    for pb in master.findall('.//PatchBank'):
        bank_name = pb.get('Name', '')
        cc0 = None
        cc32 = None
        for cc in pb.findall('.//ControlChange'):
            ctrl = cc.get('Control', '')
            val = cc.get('Value', '')
            if ctrl == '0':
                cc0 = int(val)
            elif ctrl == '32':
                cc32 = int(val)

        uses_pnl = pb.find('UsesPatchNameList')
        pnl_name = uses_pnl.get('Name', '') if uses_pnl is not None else bank_name
        patches = patch_lists.get(pnl_name, [])

        banks.append({
            "name": bank_name,
            "cc0": cc0,
            "cc32": cc32,
            "patches": patches
        })

    return {
        "manufacturer": manufacturer,
        "model": model,
        "author": author,
        "banks": banks
    }
