import dataloader
from models.modelEnums import HeavyMetalType


class SeedModel(object):
    """Heavy metals brought to the field with the seed (SALCAheavymetal 2023, Nemecek et al.,
    Appendix 7, Eq. 2, term M_seed x c_seed; decision L10).

    Inputs:
      crop: crop code
      seed_quantities: map crop -> amount per ha from the template: kg of seed for sown crops
                       (template field "seeds"), number of seedlings or trees otherwise

    Outputs:
      computeHeavyMetal: map HeavyMetalType -> mg/ha

    Seed in kg: kg x DM x concentration [mg/kg DM] of the Table 1 plant row mapped to the crop in
    data/hm_crop_product_mapping_salca2023.csv (same product as the harvest). Seedlings and trees
    count 0, because their mass per unit is not known (recommendation 8; the legacy code multiplied
    the number of plants by a concentration per kg).
    """

    _input_variables = ["crop", "seed_quantities"]
    _MAPPING = "hm_crop_product_mapping_salca2023.csv"

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in SeedModel._input_variables:
            setattr(self, key, inputs[key])

    def computeHeavyMetal(self):
        total_hm_values = dict.fromkeys(HeavyMetalType, 0.0)
        if not self._seed_amount_is_mass():
            return total_hm_values
        product = dataloader.table(self._MAPPING, numeric=False)[self.crop]["salca2023_main_product"]
        content = dataloader.hm_entry(product)
        kg_seed = sum(self.seed_quantities.values())
        for element in HeavyMetalType:
            total_hm_values[element] += kg_seed * content["dm"] * content[element.name.capitalize()]
        return total_hm_values

    def _seed_amount_is_mass(self):
        from defaultGeneration import SEEDLINGS_BASED_CROPS, TREE_BASED_CROPS
        return self.crop not in TREE_BASED_CROPS and self.crop not in SEEDLINGS_BASED_CROPS
