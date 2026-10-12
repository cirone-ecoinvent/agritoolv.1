import dataloader

class LUCModel(object):
    """Inputs:
      crop: code
      country: text
      crop_cycle_per_year: ratio

    Outputs:
      m_LUC_luc_crop_type: crop type (annual / perennial)
      m_LUC_luc_formula: ha of land use change per ha and crop cycle, as the ecoSpold formula
        "<crop specific> * LUC_crop_specific + <shared> * (1-LUC_crop_specific)"; divided by the
        yield of the crop cycle it gives ha per kg of product
      m_LUC_luc_crop_specific: crop-specific ha of land use change per ha and crop cycle
      m_LUC_luc_product: Master Data name of the land use change product (unit ha)

    Decision L16: the amounts are the ratios expanded area / current area (REC) of the
    WFLDB-adapted Blonk direct land use change assessment tool (2016-06-09a), crop-specific
    (data/luc_blonk_crop_expansion.csv) and shared responsibility for all crops of the country
    (data/luc_blonk_country_expansion.csv), divided by the crop cycles per year. The ecoinvent
    land use change dataset describes 1 ha of land use change and already contains the
    amortisation over 20 years, so the ratio is not divided by 20.
    """
    _input_variables = ["crop",
                        "country",
                        "crop_cycle_per_year"
                       ]

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in LUCModel._input_variables:
            setattr(self, key, inputs[key])

    _CROP_TABLE = "luc_blonk_crop_expansion.csv"
    _COUNTRY_TABLE = "luc_blonk_country_expansion.csv"
    _PRODUCT_TABLE = "luc_product_mapping.csv"
    _CROP_TYPES_TABLE = "crop_types.csv"

    def compute(self):
        crop_type = self._compute_crop_type()
        formula, crop_specific = self._compute_formula()
        return {'m_LUC_luc_crop_type': crop_type, 'm_LUC_luc_formula': formula,
                'm_LUC_luc_crop_specific': crop_specific,
                'm_LUC_luc_product': self._compute_product()}

    def _compute_formula(self):
        """Formula with both approaches; a crop without a value for the country falls back to the
        shared-responsibility value only (legacy behaviour)."""
        sharedResponsability = self._compute_shared_responsability()
        try:
            crop_specific = self._compute_crop_specific()
            formula = str(crop_specific) + " * LUC_crop_specific + " + str(
                sharedResponsability) + " * (1-LUC_crop_specific)"
        except KeyError:
            formula = sharedResponsability
            crop_specific = formula
        return formula, crop_specific

    def _compute_crop_specific(self):
        """Crop-specific REC / crop cycles; KeyError if the crop has no value for the country."""
        rec = {(row["crop"], row["country"]): float(row["rec_crop_specific"])
               for row in dataloader.rows(self._CROP_TABLE)}
        return rec[(self.crop, self.country)] / self.crop_cycle_per_year

    def _compute_shared_responsability(self):
        """Shared-responsibility REC of the country (negative expansion -> 0) / crop cycles."""
        countries = dataloader.table(self._COUNTRY_TABLE)
        if self.country not in countries:
            raise KeyError("Country '%s' is not in %s" % (self.country, self._COUNTRY_TABLE))
        return max(0.0, countries[self.country]["rec_shared"]) / self.crop_cycle_per_year

    def _compute_crop_type(self):
        """annual / perennial from data/crop_types.csv (legacy table; rice = flooded annual, F7)."""
        return dataloader.table(self._CROP_TYPES_TABLE, numeric=False)[self.crop]["crop_type"]

    def _compute_product(self):
        """Master Data land use change product for the crop type and flooding (decision L16)."""
        crop = dataloader.table(self._CROP_TYPES_TABLE, numeric=False)[self.crop]
        for row in dataloader.rows(self._PRODUCT_TABLE):
            if row["crop_type"] == crop["crop_type"] and row["flooded"] == crop["flooded"]:
                return row["md312_name"]
        raise KeyError("No land use change product for %s / flooded %s in %s"
                       % (crop["crop_type"], crop["flooded"], self._PRODUCT_TABLE))
