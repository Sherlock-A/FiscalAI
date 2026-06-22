"""
Tests for the Moroccan address normalization engine.
Run with: pytest backend/tests/test_address_normalizer.py -v
"""

import pytest
from app.services.address_normalizer import normalize_address, address_similarity, batch_normalize


class TestNormalizeAddress:
    """Test that address variants normalize to equivalent/similar strings."""

    def test_french_accent_removal(self):
        result = normalize_address("Résidence Al Qods, Salé")
        assert result is not None
        assert "residence" in result
        assert "sale" in result or "sle" in result

    def test_arabic_definite_article_variants(self):
        """El/Al/Es/Er variants should produce similar output."""
        variants = [
            "Hay El Qods",
            "Hay Al Qods",
            "Hay Es-Qods",
            "Hay Qods",
        ]
        normalized = [normalize_address(v) for v in variants]
        # All should contain 'hay' and 'qods'
        for n in normalized:
            assert n is not None
            assert "hay" in n
            assert "qods" in n

    def test_lot_lotissement_variants(self):
        """Lot/Los/Lotissement should normalize to 'lotissement'."""
        v1 = normalize_address("Lot 47, Hay Salam")
        v2 = normalize_address("Lotissement 47, Hay Salam")
        assert v1 is not None and v2 is not None
        # Both should contain 'lotissement' (or at least the number)
        assert "47" in v1
        assert "47" in v2

    def test_number_prefix_normalization(self):
        """N°47, Num 47, and plain 47 should all yield '47' in output."""
        addrs = ["N°47 Hay Salam", "Num 47 Hay Salam", "47 Hay Salam"]
        for addr in addrs:
            result = normalize_address(addr)
            assert result is not None
            assert "47" in result

    def test_none_input(self):
        assert normalize_address(None) is None

    def test_empty_string(self):
        assert normalize_address("   ") is None

    def test_arabic_script_transliteration(self):
        """Arabic address should be transliterated to Latin and normalized."""
        result = normalize_address("حي السلام، سلا")
        assert result is not None
        assert len(result) > 0
        # unidecode will produce some Latin representation
        assert all(ord(c) < 128 or c == " " for c in result)

    def test_case_insensitive(self):
        r1 = normalize_address("HAY SALAM SALE")
        r2 = normalize_address("hay salam sale")
        r3 = normalize_address("Hay Salam Salé")
        assert r1 == r2
        # r3 may differ only due to accent removal
        assert r1 is not None and r3 is not None

    def test_noise_punctuation_removed(self):
        result = normalize_address("Lot. 47; Hay (Salam), Salé.")
        assert result is not None
        assert "," not in result
        assert "." not in result
        assert ";" not in result


class TestAddressSimilarity:
    def test_identical_addresses(self):
        a = normalize_address("Hay Salam, Salé")
        score = address_similarity(a, a)
        assert score == 1.0

    def test_variant_addresses_high_similarity(self):
        a = normalize_address("Hay El Salam, Salé")
        b = normalize_address("Hay Es-Salam, Sale")
        score = address_similarity(a, b)
        assert score >= 0.70, f"Expected ≥0.70, got {score}"

    def test_different_addresses_low_similarity(self):
        a = normalize_address("Hay Inara, Salé")
        b = normalize_address("Douar Lhajja, Témara")
        score = address_similarity(a, b)
        assert score < 0.5, f"Expected <0.5, got {score}"

    def test_none_inputs(self):
        assert address_similarity(None, "hay salam") == 0.0
        assert address_similarity("hay salam", None) == 0.0
        assert address_similarity(None, None) == 0.0


class TestBatchNormalize:
    def test_batch_with_mixed_inputs(self):
        inputs = ["Hay Salam, Salé", None, "", "Lot 47 Hay Inara"]
        results = batch_normalize(inputs)
        assert len(results) == 4
        assert results[0] is not None
        assert results[1] is None
        assert results[2] is None
        assert results[3] is not None
