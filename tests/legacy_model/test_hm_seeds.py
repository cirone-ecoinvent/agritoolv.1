"""Heavy metals in seed from SALCAheavymetal 2023 Table 1 (decision L10, recommendation 8)."""
import pytest

from models.modelEnums import HeavyMetalType
from models.seedmodel import SeedModel


def test_sown_seed_in_kg_uses_the_crop_product():
    hm = SeedModel({"crop": "wheat", "seed_quantities": {"wheat": 180.0}}).computeHeavyMetal()
    assert hm[HeavyMetalType.zn] == pytest.approx(180 * 0.85 * 17.2)   # wheat grains, DM 0.85
    assert hm[HeavyMetalType.cd] == pytest.approx(180 * 0.85 * 0.048)


def test_crop_without_product_uses_the_main_product_mean():
    hm = SeedModel({"crop": "flax", "seed_quantities": {"flax": 50.0}}).computeHeavyMetal()
    assert hm[HeavyMetalType.cu] == pytest.approx(50 * 0.48 * 6.48)


def test_seedlings_and_trees_count_zero():
    for crop in ("apple", "tomato_fresh"):
        hm = SeedModel({"crop": crop, "seed_quantities": {crop: 1000.0}}).computeHeavyMetal()
        assert all(v == 0.0 for v in hm.values()), crop
