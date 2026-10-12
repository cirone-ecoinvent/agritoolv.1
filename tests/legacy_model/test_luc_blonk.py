"""Decision L16: land use change amounts from the WFLDB-adapted Blonk tool (2016-06-09a), in ha of
land use change per ha and crop cycle, and the Master Data land use change product."""
import pytest

from models.lucmodel import LUCModel


def _luc(crop, country, cycles=1.0):
    return LUCModel({"crop": crop, "country": country, "crop_cycle_per_year": cycles}).compute()


def test_apple_brazil_reproduces_the_blonk_tool():
    # sheet 'Country known; land use unknown', apples in Brazil: REC_CS and REC_SR (rows 104-105)
    luc = _luc("apple", "BR", cycles=2.0)
    assert luc["m_LUC_luc_crop_specific"] == pytest.approx(0.40163471153428115 / 2.0, rel=1e-15)
    assert luc["m_LUC_luc_formula"] == "%s * LUC_crop_specific + %s * (1-LUC_crop_specific)" % (
        0.40163471153428115 / 2.0, 0.19991651301809035 / 2.0)


def test_morocco_uses_the_workbook_value():
    # the legacy code had 0.032242306728212 (one digit lost)
    assert _luc("almond", "MA")["m_LUC_luc_formula"].endswith(
        "%s * (1-LUC_crop_specific)" % 0.03322423067282125)


def test_crop_without_value_for_the_country_falls_back_to_shared_responsibility():
    luc = _luc("almond", "BR")
    assert luc["m_LUC_luc_formula"] == luc["m_LUC_luc_crop_specific"] == 0.19991651301809035


def test_negative_country_expansion_is_zero():
    assert _luc("wheat", "IT")["m_LUC_luc_formula"].endswith("0.0 * (1-LUC_crop_specific)")


def test_unknown_country_names_the_table():
    with pytest.raises(KeyError, match="luc_blonk_country_expansion.csv"):
        _luc("wheat", "XX")


@pytest.mark.parametrize("crop, product", [
    ("rice", "land use change, paddy rice"),
    ("wheat", "land use change, annual crop"),
    ("apple", "land use change, perennial crop"),
])
def test_master_data_product(crop, product):
    assert _luc(crop, "IN")["m_LUC_luc_product"] == product
