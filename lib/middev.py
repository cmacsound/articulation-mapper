"""
Middev XML generator for Pro Tools device registration.

Generates MIDIDeviceTypes XML files (.middev) that register a virtual
instrument as a recognized MIDI device in Pro Tools / Audio MIDI Setup.
"""

from xml.sax.saxutils import escape


def generate_middev(devices, author="Articulation Mapper"):
    """Generate a Pro Tools compatible .middev XML string.

    Args:
        devices: List of dicts, each with:
            - manufacturer: Manufacturer name
            - model: Model name
        author: Author tag

    Returns:
        XML string of the complete middev document.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE MIDIDeviceTypes PUBLIC '
                 '"-//MIDI Manufacturers Association//DTD MIDIDeviceTypes 03//EN" '
                 '"http://www.sonosphere.com/dtds/MIDIDeviceTypes.dtd">')
    lines.append('')
    lines.append('<MIDIDeviceTypes>')
    lines.append(f'\t<Author>{escape(author)}</Author>')

    for device in devices:
        mfg = escape(device["manufacturer"])
        mdl = escape(device["model"])
        lines.append('')
        lines.append(f'\t<MIDIDeviceType Manufacturer="{mfg}" '
                     f'Model="{mdl}" '
                     f'SupportsGeneralMIDI="false" '
                     f'SupportsMMC="false" '
                     f'CanRoute="false" '
                     f'IsSampler="false" '
                     f'IsDrumMachine="false" '
                     f'IsMixer="false" '
                     f'IsEffectUnit="false" >')
        lines.append('\t\t<Receives MaxChannels="16" MTC="false" Clock="false" '
                     'Notes="false" ProgramChanges="true" '
                     'BankSelectMSB="true" BankSelectLSB="true" '
                     'PanDisruptsStereo="false" />')
        lines.append('\t\t<Transmits MaxChannels="1" MTC="false" Clock="false" '
                     'Notes="false" ProgramChanges="true" '
                     'BankSelectMSB="true" BankSelectLSB="true" />')
        lines.append('\t</MIDIDeviceType>')

    lines.append('')
    lines.append('</MIDIDeviceTypes>')
    lines.append('')

    return '\n'.join(lines)


def parse_middev(xml_string):
    """Parse a middev XML string into a list of device entries.

    Args:
        xml_string: Raw XML content of a .middev file.

    Returns:
        List of dicts with manufacturer and model keys.
    """
    from lxml import etree

    root = etree.fromstring(xml_string.encode('utf-8'))
    devices = []
    for dt in root.findall('.//MIDIDeviceType'):
        devices.append({
            "manufacturer": dt.get('Manufacturer', ''),
            "model": dt.get('Model', '')
        })
    return devices
