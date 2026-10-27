# Irrigation water consumption (ETirr, blue water consumption of irrigation) per crop and country, m3 per t of main
# product (decision L44): Pfister S., Bayer P. (2014) J Clean Prod 73:52-62, Appendix B, sheet 'Blue water
# consumption (m3_ton)', the expected value (geometric mean of deficit and full irrigation, paper Eq. 1),
# production-weighted per country, input data of the year 2000 (data/pfister2014_blue_water_country.csv, crops and
# countries of data/pfister2014_crop_mapping.csv and data/pfister2014_country_mapping.csv). GLO = world value of
# the sheet 'Global Averages WFP_mon and WSI'. A country without a value in Appendix B ('No production') has no
# entry and takes GLO. The crops marked mialyk in the crop mapping (hemp, mint; no Pfister value on the basis of the
# default yield) take the blue water from irrigation of Mialyk et al. (2024), 2010-2019
# (data/mialyk2024_national_blue_wf.csv, items of data/mialyk2024_crop_mapping.csv; decision L56). The crops marked
# legacy (flax, mulberry) take data/legacy_irrigation_water_consumption.csv (decisions L55, L56).
from collections import defaultdict

import dataloader


def _irrigation_water_consumption():
    expected = defaultdict(dict)
    for row in dataloader.rows("pfister2014_blue_water_country.csv"):
        if row["bw_expected_m3_t"] != "":
            expected[row["pfister_crop"]][row["country"]] = float(row["bw_expected_m3_t"])
    mialyk = defaultdict(dict)
    for row in dataloader.rows("mialyk2024_national_blue_wf.csv"):
        mialyk[row["mialyk_crop_code"]][row["country"]] = float(row["wfb_i_m3_t"])
    mialyk_items = {row["crop"]: row for row in dataloader.rows("mialyk2024_crop_mapping.csv")}
    legacy = dataloader.crop_country_table("legacy_irrigation_water_consumption.csv", "etirr_m3_per_t")
    table = {}
    for row in dataloader.rows("pfister2014_crop_mapping.csv"):
        if row["use"] == "legacy":
            table[row["crop"]] = legacy[row["crop"]]
        elif row["use"] == "mialyk":
            item = mialyk_items[row["crop"]]
            if "GLO" not in mialyk[item["mialyk_crop_code"]]:
                raise ValueError("mialyk2024_national_blue_wf.csv: no GLO value for %s" % item["mialyk_crop_code"])
            factor = float(item["kg_item_per_kg_product"] or 1.0)
            table[row["crop"]] = {country: value * factor for country, value in mialyk[item["mialyk_crop_code"]].items()}
        elif row["use"] in ("direct", "proxy"):
            if "GLO" not in expected[row["pfister_crop"]]:
                raise ValueError("pfister2014_blue_water_country.csv: no GLO value for %s" % row["pfister_crop"])
            table[row["crop"]] = dict(expected[row["pfister_crop"]])
        else:
            raise ValueError("pfister2014_crop_mapping.csv: unknown use %r for %s" % (row["use"], row["crop"]))
    return table


EVAPO_TRANSPI_PER_CROP_PER_COUNTRY = _irrigation_water_consumption()
