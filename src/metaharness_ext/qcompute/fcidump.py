"""FCIDUMP ASCII format parser for molecular integrals.

Parses the standard FCIDUMP format used in quantum chemistry to extract
one-electron (h_ij) and two-electron (V_ijkl) integrals along with
metadata such as the number of orbitals, electrons, spin multiplicity,
and orbital symmetries.
"""

from __future__ import annotations

import re
from pathlib import Path

from metaharness_ext.qcompute.contracts import FCIDumpData


def parse_fcidump(path: str | Path) -> FCIDumpData:
    """Parse an FCIDUMP ASCII file and return structured integral data.

    Args:
        path: Filesystem path to the FCIDUMP file.

    Returns:
        FCIDumpData with parsed header fields and integral tensors.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as valid FCIDUMP format.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"FCIDUMP file not found: {file_path}")

    text = file_path.read_text()
    return parse_fcidump_string(text)


def parse_fcidump_string(text: str) -> FCIDumpData:
    """Parse an FCIDUMP format string and return structured integral data.

    Args:
        text: Raw FCIDUMP file contents.

    Returns:
        FCIDumpData with parsed header fields and integral tensors.

    Raises:
        ValueError: If the text cannot be parsed as valid FCIDUMP format.
    """
    header = _parse_header(text)
    one_electron: dict[tuple[int, int], float] = {}
    two_electron: dict[tuple[int, int, int, int], float] = {}

    for line in _data_lines(text):
        value, p, q, r, s = _parse_data_line(line)
        # The trailing line with value 0.0 and all indices 0 is the EOF marker.
        if p == 0 and q == 0 and r == 0 and s == 0:
            continue
        if r == 0 and s == 0:
            one_electron[(p, q)] = value
        else:
            two_electron[(p, q, r, s)] = value

    return FCIDumpData(
        norb=header["NORB"],
        nelec=header["NELEC"],
        ms2=header.get("MS2", 0),
        orbsym=header.get("ORBSYM", []),
        isym=header.get("ISYM", 1),
        one_electron_integrals=one_electron,
        two_electron_integrals=two_electron,
    )


def _parse_header(text: str) -> dict[str, object]:
    """Extract header key-value pairs from the &FCI ... &END block.

    Handles multi-line headers with various whitespace and comma styles.
    """
    match = re.search(r"&FCI\s*(.*?)\s*&END", text, re.DOTALL | re.IGNORECASE)
    if match is None:
        raise ValueError("No &FCI ... &END header block found in FCIDUMP text")

    header_body = match.group(1)
    # Normalize: collapse all whitespace to spaces, remove newlines.
    header_body = re.sub(r"\s+", " ", header_body).strip().rstrip(",")

    result: dict[str, object] = {}
    # Split by commas and look for key=value pairs.
    # For ORBSYM the value is a list of integers that may span commas.
    tokens = [t.strip() for t in header_body.split(",") if t.strip()]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        kv_match = re.match(r"(\w+)\s*=\s*(.*)", token)
        if kv_match:
            key = kv_match.group(1).upper()
            value_part = kv_match.group(2).strip()
            if key == "ORBSYM":
                # ORBSYM value is a list of integers that can span multiple
                # comma-separated tokens.
                orbsym_values: list[int] = []
                for part in value_part.split():
                    part = part.strip()
                    if part:
                        orbsym_values.append(int(part))
                # Continue consuming subsequent tokens that are bare integers.
                i += 1
                while i < len(tokens):
                    next_token = tokens[i].strip()
                    # Stop if the next token contains a new key=value assignment.
                    if re.match(r"\w+\s*=", next_token):
                        break
                    for part in next_token.split():
                        part = part.strip()
                        if part:
                            orbsym_values.append(int(part))
                    i += 1
                result[key] = orbsym_values
                continue
            elif value_part:
                try:
                    result[key] = int(value_part)
                except ValueError:
                    result[key] = value_part
        i += 1

    if "NORB" not in result or "NELEC" not in result:
        raise ValueError("FCIDUMP header must contain at least NORB and NELEC")

    return result


def _data_lines(text: str) -> list[str]:
    """Return all non-header, non-empty lines from the FCIDUMP text."""
    lines: list[str] = []
    in_header = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith("&FCI"):
            in_header = True
            continue
        if stripped.upper().startswith("&END"):
            in_header = False
            continue
        if in_header:
            continue
        lines.append(stripped)
    return lines


def _parse_data_line(line: str) -> tuple[float, int, int, int, int]:
    """Parse a single data line into (value, p, q, r, s).

    Each data line has the format: ``value  p  q  r  s``
    where value is a float and p,q,r,s are 1-based integer indices.
    """
    parts = line.split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5 fields in data line, got {len(parts)}: {line!r}")
    value = float(parts[0])
    p, q, r, s = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
    return value, p, q, r, s
