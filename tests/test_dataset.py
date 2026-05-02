"""
Unit tests for the dataset loading and validation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

from main import list_supported, load_dimensions, DATA_PATH


class TestDatasetIntegrity:

    def test_csv_exists(self):
        assert DATA_PATH.exists(), f"Dataset not found at {DATA_PATH}"

    def test_csv_loads(self):
        df = pd.read_csv(DATA_PATH)
        assert len(df) > 0, "Dataset is empty"

    def test_required_columns_exist(self):
        df = pd.read_csv(DATA_PATH)
        required = ["part", "size", "pressure", "bore", "flange_od", "flange_thk",
                     "bolt_circle_dia", "bolt_hole_dia", "bolt_count",
                     "branch_length", "gasket_od", "gasket_id", "gasket_height"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_nan_in_critical_columns(self):
        df = pd.read_csv(DATA_PATH)
        critical = ["part", "size", "pressure", "bore", "flange_od", "flange_thk",
                     "bolt_circle_dia", "bolt_hole_dia", "bolt_count"]
        for col in critical:
            nan_count = df[col].isna().sum()
            assert nan_count == 0, f"Column {col} has {nan_count} NaN values"

    def test_all_six_part_types(self):
        df = pd.read_csv(DATA_PATH)
        parts = set(df["part"].unique())
        assert "bonnet" in parts, "Missing bonnet rows"
        assert "flange" in parts, "Missing flange rows"
        assert "spool" in parts, "Missing spool rows"
        assert "blind" in parts, "Missing blind flange rows"
        assert "tee" in parts, "Missing tee rows"
        assert "gasket" in parts, "Missing gasket rows"

    def test_dataset_has_minimum_rows(self):
        df = pd.read_csv(DATA_PATH)
        assert len(df) >= 100, f"Expected 100+ rows, got {len(df)}"

    def test_pressures_are_valid(self):
        df = pd.read_csv(DATA_PATH)
        valid_pressures = {2000, 3000, 5000, 10000, 15000, 20000}
        for p in df["pressure"].unique():
            assert int(p) in valid_pressures, f"Unexpected pressure: {p}"

    def test_list_supported_returns_dataframe(self):
        df = list_supported()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_load_dimensions_bonnet(self):
        dims = load_dimensions("bonnet", 2.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["bore"] > 0
        assert dims["flange_od"] > 0
        assert dims["bolt_count"] > 0

    def test_load_dimensions_flange(self):
        dims = load_dimensions("flange", 2.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["bore"] > 0
        assert dims["flange_od"] > 0

    def test_load_dimensions_spool(self):
        dims = load_dimensions("spool", 2.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["bore"] > 0
        assert dims["spool_length"] > 0

    def test_load_dimensions_blind(self):
        dims = load_dimensions("blind", 3.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["flange_od"] > 0
        assert dims["bolt_count"] > 0

    def test_load_dimensions_tee(self):
        dims = load_dimensions("tee", 3.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["bore"] > 0
        assert dims["spool_length"] > 0
        assert dims["branch_length"] > 0

    def test_load_dimensions_gasket(self):
        dims = load_dimensions("gasket", 2.0625, 10000)
        assert isinstance(dims, dict)
        assert dims["gasket_od"] > 0
        assert dims["gasket_id"] > 0
        assert dims["gasket_height"] > 0

    def test_load_dimensions_not_found(self):
        """Should raise ValueError for non-existent combo."""
        try:
            load_dimensions("bonnet", 99.0, 999999)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Closest available" in str(e)
