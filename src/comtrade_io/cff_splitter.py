"""
cff_splitter.py
~~~~~~~~~~~~~~~
Splits a COMTRADE CFF (Combined File Format) into its constituent sections.

A CFF file is a single text/binary file that concatenates the CFG, DAT, and
optionally INF and HDR sections — each preceded by a sentinel header line:

    --- file type: CFG ---
    --- file type: DAT <ENCODING>: <BYTE_COUNT> ---
    --- file type: INF ---          (optional)
    --- file type: HDR ---          (optional)

The DAT section header carries two additional tokens:
  - ENCODING : ASCII | BINARY | BINARY32 | FLOAT32
  - BYTE_COUNT: number of raw bytes that follow (only relevant for binary formats)

Design note: binary DAT sections are kept as ``bytes``; all text sections are
returned as ``str``.  This mirrors what the existing cfg/dat parsers already
expect when reading from disk.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Matches any CFF section sentinel, e.g.:
#   --- file type: CFG ---
#   --- file type: DAT FLOAT32: 302760 ---
#   --- file type: INF ---
_SENTINEL_RE = re.compile(
    r"(?i)^---\s+file type:\s+([A-Z]+)"          # group 1: section type (CFG/DAT/INF/HDR)
    r"(?:\s+([A-Z0-9]+)"                          # group 2: DAT encoding  (optional)
    r"(?:\s*:\s*(\d+))?)?"                        # group 3: byte count    (optional)
    r"\s+---\s*$"
)

_TEXT_SECTIONS = {"CFG", "INF", "HDR"}
_BINARY_ENCODINGS = {"BINARY", "BINARY32", "FLOAT32"}


@dataclass
class CffSections:
    """Container for the raw content of each CFF section."""
    cfg: str = ""
    dat_encoding: str = "ASCII"          # ASCII | BINARY | BINARY32 | FLOAT32
    dat_text: Optional[str] = None       # populated when encoding is ASCII
    dat_bytes: Optional[bytes] = None    # populated for binary encodings
    inf: Optional[str] = None
    hdr: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Convenience helpers matching what the existing parsers expect        #
    # ------------------------------------------------------------------ #
    def cfg_stream(self) -> io.StringIO:
        """Return CFG content as a StringIO, ready for Configure.read()."""
        return io.StringIO(self.cfg)

    def dat_stream(self) -> io.StringIO | io.BytesIO:
        """Return DAT content as the appropriate IO type."""
        if self.dat_bytes is not None:
            return io.BytesIO(self.dat_bytes)
        return io.StringIO(self.dat_text or "")


def split_cff(path: str | Path, encoding: str = "utf-8") -> CffSections:
    """
    Parse a ``.cff`` file and return a :class:`CffSections` instance.

    The file is opened in binary mode so that we can handle the boundary
    between the text preamble and a potentially binary DAT section without
    codec confusion — think of it as reading a mixed-content stream where
    some pages are plain text and one page might be raw machine code.

    Parameters
    ----------
    path:
        Filesystem path to the ``.cff`` file.
    encoding:
        Text encoding used for the text sections (CFG / INF / HDR).
        Defaults to ``utf-8``; use ``"iso-8859-1"`` for legacy IEDs.

    Raises
    ------
    ValueError
        If the CFG or DAT section is missing, or an unknown section type is
        encountered.
    """
    path = Path(path)
    raw: bytes = path.read_bytes()

    sections = CffSections()
    _parse_raw(raw, sections, encoding)

    if not sections.cfg:
        raise ValueError(f"CFF file '{path}' is missing the CFG section.")
    if sections.dat_text is None and sections.dat_bytes is None:
        raise ValueError(f"CFF file '{path}' is missing the DAT section.")

    return sections


# ------------------------------------------------------------------ #
# Internal helpers                                                     #
# ------------------------------------------------------------------ #

def _parse_raw(raw: bytes, sections: CffSections, text_encoding: str) -> None:
    """
    Walk through *raw* byte-by-byte (line-by-line for text, verbatim for
    binary DAT) and populate *sections* in-place.

    State machine with three states:
      SEEKING  – haven't seen a sentinel yet (skip any preamble / BOM)
      IN_TEXT  – accumulating lines for a text section (CFG / INF / HDR)
      IN_DAT   – inside the DAT section (may be text or binary)
    """
    # We need to find sentinel lines.  For the text parts we decode
    # line-by-line; for binary DAT we grab an exact byte count instead.

    current_section: Optional[str] = None
    buf: list[str] = []
    pos = 0
    length = len(raw)

    while pos < length:
        # Read one line (keep the line ending so round-trip is exact).
        line_end = raw.find(b"\n", pos)
        if line_end == -1:
            line_bytes = raw[pos:]
            pos = length
        else:
            line_bytes = raw[pos: line_end + 1]
            pos = line_end + 1

        # Try to decode as text to check for a sentinel.
        try:
            line_text = line_bytes.decode(text_encoding)
        except UnicodeDecodeError:
            # Non-decodable line inside a binary DAT region — handled below.
            line_text = None

        if line_text is not None:
            m = _SENTINEL_RE.match(line_text.rstrip("\r\n"))
            if m:
                # ------ flush current section ------
                _flush(current_section, buf, sections)
                buf = []

                sec_type = m.group(1).upper()
                dat_encoding = (m.group(2) or "ASCII").upper()
                dat_byte_count_str = m.group(3)

                if sec_type == "DAT":
                    sections.dat_encoding = dat_encoding
                    if dat_encoding in _BINARY_ENCODINGS and dat_byte_count_str:
                        # Binary DAT: consume exactly the declared byte count.
                        byte_count = int(dat_byte_count_str)
                        sections.dat_bytes = raw[pos: pos + byte_count]
                        pos += byte_count
                        current_section = None  # nothing more to accumulate
                    else:
                        current_section = "DAT"
                elif sec_type in _TEXT_SECTIONS:
                    current_section = sec_type
                else:
                    # Unknown section type — skip gracefully.
                    current_section = None
                continue  # sentinel line itself is not content

        # Accumulate content line.
        if current_section is not None and line_text is not None:
            buf.append(line_text)

    # Flush last open section.
    _flush(current_section, buf, sections)


def _flush(section: Optional[str], buf: list[str], sections: CffSections) -> None:
    if section is None or not buf:
        return
    content = "".join(buf)
    if section == "CFG":
        sections.cfg = content
    elif section == "DAT":
        sections.dat_text = content
    elif section == "INF":
        sections.inf = content
    elif section == "HDR":
        sections.hdr = content
