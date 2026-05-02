"""
Unit tests for the fuzzy matching / closest-match logic.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import find_closest_match


class TestFuzzyMatch:

    def test_exact_match_returns_zero_distance(self):
        results = find_closest_match("bonnet", 2.0625, 10000)
        assert len(results) > 0
        best = results[0]
        assert best["size"] == 2.0625
        assert best["pressure"] == 10000
        assert best["distance"] == 0.0

    def test_close_size_returns_suggestions(self):
        # 2.5 is not in the dataset but 2.5625 is
        results = find_closest_match("bonnet", 2.5, 5000)
        assert len(results) > 0
        # Should suggest 2.5625 as closest
        sizes = [r["size"] for r in results]
        assert 2.5625 in sizes

    def test_returns_max_top_n(self):
        results = find_closest_match("bonnet", 3.0, 10000, top_n=5)
        assert len(results) <= 5

    def test_wrong_part_type(self):
        # "valve" is not in dataset, should fall back to all parts
        results = find_closest_match("valve", 2.0625, 10000)
        assert len(results) > 0

    def test_extreme_values_still_return(self):
        results = find_closest_match("bonnet", 99.0, 999999)
        assert len(results) > 0

    def test_results_sorted_by_distance(self):
        results = find_closest_match("bonnet", 3.0, 8000, top_n=5)
        distances = [r["distance"] for r in results]
        assert distances == sorted(distances)

    def test_same_part_type_preferred(self):
        results = find_closest_match("flange", 2.0625, 10000)
        assert len(results) > 0
        # All results should be flanges (since flanges exist for 2.0625 @ 10k)
        for r in results:
            assert r["part"] == "flange"
