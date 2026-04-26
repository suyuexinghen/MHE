"""Tests for the FCIDUMP parser module."""

import pytest

from metaharness_ext.qcompute.contracts import FCIDumpData
from metaharness_ext.qcompute.fcidump import parse_fcidump, parse_fcidump_string

H2_FCIDUMP = """ &FCI NORB=2,NELEC=2,MS2=0,
   ORBSYM=1,1,
   ISYM=1,
 &END
  1.834752942932  1  1  0  0
  0.715403888080  2  1  0  0
  0.663476275792  2  2  0  0
  0.181293137885  1  1  1  1
  0.663476275792  2  2  2  2
  0.715403888080  1  2  0  0
  0.181293137885  2  2  1  1
  0.120365812741  2  1  2  1
  0.120365812741  1  2  1  2
  0.675710775216  2  2  2  1
  0.675710775216  2  1  2  2
  0.000000000000  0  0  0  0
"""


class TestParseMinimalH2FCIDUMP:
    def test_parse_minimal_h2_fcidump(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert data.norb == 2
        assert data.nelec == 2
        assert data.ms2 == 0
        assert data.orbsym == [1, 1]
        assert data.isym == 1


class TestFCIDUMPHeaderParsing:
    def test_header_with_extra_spaces(self) -> None:
        text = """ &FCI  NORB = 3 , NELEC = 4 , MS2 = 0 ,
   ORBSYM = 1 , 2 , 3 ,
   ISYM = 1 ,
 &END
  0.5  1  1  0  0
  0.000000000000  0  0  0  0
"""
        data = parse_fcidump_string(text)
        assert data.norb == 3
        assert data.nelec == 4
        assert data.orbsym == [1, 2, 3]

    def test_header_compact_format(self) -> None:
        text = """&FCI NORB=2,NELEC=2,MS2=0,ORBSYM=1,1,ISYM=1,&END
  1.0  1  1  0  0
  0.000000000000  0  0  0  0
"""
        data = parse_fcidump_string(text)
        assert data.norb == 2
        assert data.nelec == 2

    def test_header_trailing_commas(self) -> None:
        text = """ &FCI NORB=2,NELEC=2,MS2=0,
   ORBSYM=1,1,
   ISYM=1,
 &END
  1.0  1  1  0  0
  0.000000000000  0  0  0  0
"""
        data = parse_fcidump_string(text)
        assert data.norb == 2

    def test_header_missing_raises(self) -> None:
        with pytest.raises(ValueError, match="No &FCI"):
            parse_fcidump_string("no header here\n  1.0  1 1 0 0\n")

    def test_header_missing_norb_raises(self) -> None:
        with pytest.raises(ValueError, match="NORB"):
            parse_fcidump_string(" &FCI NELEC=2, &END\n  1.0  1 1 0 0\n")


class TestFCIDUMPOneElectronIntegrals:
    def test_one_electron_integrals_count(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        # H2 with 2 orbitals: h_11, h_21, h_22, h_12
        assert len(data.one_electron_integrals) == 4

    def test_one_electron_diagonal_values(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert abs(data.one_electron_integrals[(1, 1)] - 1.834752942932) < 1e-10
        assert abs(data.one_electron_integrals[(2, 2)] - 0.663476275792) < 1e-10

    def test_one_electron_offdiagonal_values(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert abs(data.one_electron_integrals[(2, 1)] - 0.715403888080) < 1e-10
        assert abs(data.one_electron_integrals[(1, 2)] - 0.715403888080) < 1e-10

    def test_one_electron_no_2e_entries(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        # Entries with r,s != 0 should not appear in 1e integrals
        for key in data.one_electron_integrals:
            assert len(key) == 2


class TestFCIDUMPTwoElectronIntegrals:
    def test_two_electron_integrals_count(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert len(data.two_electron_integrals) == 7

    def test_two_electron_diagonal_value(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert abs(data.two_electron_integrals[(1, 1, 1, 1)] - 0.181293137885) < 1e-10
        assert abs(data.two_electron_integrals[(2, 2, 2, 2)] - 0.663476275792) < 1e-10

    def test_two_electron_cross_terms(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        assert abs(data.two_electron_integrals[(2, 2, 1, 1)] - 0.181293137885) < 1e-10
        assert abs(data.two_electron_integrals[(2, 1, 2, 1)] - 0.120365812741) < 1e-10


class TestFCIDUMPRoundtrip:
    def test_roundtrip_serialization(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        serialized = data.model_dump()
        restored = FCIDumpData.model_validate(serialized)
        assert restored.norb == data.norb
        assert restored.nelec == data.nelec
        assert restored.ms2 == data.ms2
        assert restored.orbsym == data.orbsym
        assert restored.isym == data.isym
        assert restored.one_electron_integrals == data.one_electron_integrals
        assert restored.two_electron_integrals == data.two_electron_integrals

    def test_json_roundtrip(self) -> None:
        data = parse_fcidump_string(H2_FCIDUMP)
        json_str = data.model_dump_json()
        restored = FCIDumpData.model_validate_json(json_str)
        assert restored.norb == data.norb
        assert restored.one_electron_integrals[(1, 1)] == data.one_electron_integrals[(1, 1)]


class TestFCIDUMPMissingFile:
    def test_missing_file_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        missing = tmp_path / "nonexistent.fcidump"  # type: ignore[operator]
        with pytest.raises(FileNotFoundError, match="FCIDUMP file not found"):
            parse_fcidump(str(missing))

    def test_parse_from_file(self, tmp_path: pytest.TempPathFactory) -> None:
        fcidump_path = tmp_path / "h2.fcidump"  # type: ignore[operator]
        fcidump_path.write_text(H2_FCIDUMP)
        data = parse_fcidump(str(fcidump_path))
        assert data.norb == 2
        assert data.nelec == 2
