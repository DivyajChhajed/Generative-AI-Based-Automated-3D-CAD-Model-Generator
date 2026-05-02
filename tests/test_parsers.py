"""
Unit tests for the parser functions in main.py.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _fraction_to_decimal, _parse_pressure, parse_part, normalize_to_sixteenth


class TestFractionToDecimal:

    def test_fraction_3_1_16(self):
        assert _fraction_to_decimal("3-1/16") == 3.0625

    def test_fraction_2_1_16(self):
        assert _fraction_to_decimal("2-1/16") == 2.0625

    def test_fraction_1_13_16(self):
        assert _fraction_to_decimal("1-13/16") == 1.8125

    def test_fraction_2_9_16(self):
        assert _fraction_to_decimal("2-9/16") == 2.5625

    def test_fraction_5_1_8(self):
        assert _fraction_to_decimal("5-1/8") == 5.125

    def test_fraction_7_1_16(self):
        assert _fraction_to_decimal("7-1/16") == 7.0625

    def test_fraction_space_separator(self):
        assert _fraction_to_decimal("3 1/16") == 3.0625

    def test_decimal_direct(self):
        assert _fraction_to_decimal("3.0625") == 3.0625

    def test_decimal_with_text(self):
        assert _fraction_to_decimal("size 2.0625 inch") == 2.0625

    def test_zero_denominator(self):
        assert _fraction_to_decimal("3-1/0") is None

    def test_no_match(self):
        assert _fraction_to_decimal("hello world") is None

    def test_with_quotes(self):
        result = _fraction_to_decimal('3-1/16"')
        assert result == 3.0625


class TestParsePressure:

    def test_10k(self):
        assert _parse_pressure("10k") == 10000

    def test_5k(self):
        assert _parse_pressure("5k") == 5000

    def test_15k(self):
        assert _parse_pressure("15k") == 15000

    def test_20k(self):
        assert _parse_pressure("20k") == 20000

    def test_2k(self):
        assert _parse_pressure("2k") == 2000

    def test_3k(self):
        assert _parse_pressure("3k") == 3000

    def test_number_10000(self):
        assert _parse_pressure("10000") == 10000

    def test_comma_separated(self):
        assert _parse_pressure("10,000") == 10000

    def test_with_psi(self):
        assert _parse_pressure("10k PSI") == 10000

    def test_no_match(self):
        assert _parse_pressure("hello world") is None


class TestParsePart:

    def test_bonnet(self):
        assert parse_part("Generate API 6A bonnet 3-1/16 10k") == "bonnet"

    def test_flange(self):
        assert parse_part("Generate API 6A flange 3-1/16 10k") == "flange"

    def test_spool(self):
        assert parse_part("Generate API 6A spool 3-1/16 10k") == "spool"

    def test_default_bonnet(self):
        assert parse_part("Generate 3-1/16 10k") == "bonnet"

    def test_case_insensitive(self):
        assert parse_part("BONNET 3-1/16 10k") == "bonnet"
        assert parse_part("FLANGE 3-1/16 10k") == "flange"
        assert parse_part("SPOOL 3-1/16 10k") == "spool"

    def test_blind_flange(self):
        assert parse_part("blind flange 3-1/16 10k") == "blind"

    def test_blind_keyword(self):
        assert parse_part("Generate API 6A blind 2-1/16 5k") == "blind"

    def test_tee(self):
        assert parse_part("tee 3-1/16 10k") == "tee"

    def test_tee_fitting(self):
        assert parse_part("Generate API 6A tee fitting 4-1/16 5k") == "tee"

    def test_gasket(self):
        assert parse_part("gasket 2-1/16 10k") == "gasket"

    def test_ring_gasket(self):
        assert parse_part("ring gasket 3-1/16 5k") == "gasket"

    def test_ring_joint(self):
        assert parse_part("ring joint 2-1/16 10k") == "gasket"


class TestNormalizeToSixteenth:

    def test_exact_sixteenth(self):
        assert normalize_to_sixteenth(3.0625) == 3.0625

    def test_snap_close(self):
        assert normalize_to_sixteenth(3.06) == 3.0625

    def test_whole_number(self):
        assert normalize_to_sixteenth(3.0) == 3.0

    def test_half_inch(self):
        assert normalize_to_sixteenth(2.5) == 2.5
