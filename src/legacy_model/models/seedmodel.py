from models.modelEnums import HeavyMetalType

class SeedModel(object):
    """Inputs:
      seed_quantities: map Crop -> quantity (kg or unit) / ha

    Outputs:
      computeHeavyMetal:
        hm_total_seed : map HeavyMetalType -> mg i/ha (i: hm type)
    """

    _input_variables = ["seed_quantities"
                       ]

    _SEED_DM = {
                "almond": 0.73, #tree_seedlings
                "apple": 0.73, #tree_seedlings
                "apricot": 0.73, #tree_seedlings
        "asparagus_green": 0.73,  # vegetable
        "asparagus_white": 0.73,  # vegetable
                "banana": 0.73, #tree_seedlings
        "bellpepper": 0.9,
        "blueberry": 0.73,  # tree_seedlings
        "cabbage_red": 0.73,
        "cabbage_white": 0.73,
                "carrot": 0.73, #vegetable
        "cashew": 0.9,
        "cassava": 0.9,
        "castor_beans": 0.9,  # cashew
        "chick_pea": 0.73,  # other
        "chilli": 0.9,
                "cocoa": 0.73, #other
                "coconut": 0.73, #tree_seedlings
        "coffee_arabica": 0.73,  # other
        "coffee_robusta": 0.73,  # other
        "coriander": 0.73,  # other
        "cotton": 0.9,
        "cranberry": 0.73,  # tree_seedlings
        "eggplant": 0.955,
        "flax": 0.9,
        "ginger": 0.73,  # other
        "grape": 0.9,
        "guar": 0.9,
        "hemp": 0.9504,
        "lemon": 0.73,  # tree_seedlings
        "citruslime": 0.73,  # tree_seedlings
        "lentil": 0.92,
                "linseed": 0.85, #pea
                "maizegrain": 0.85,
                "mandarin": 0.73, #tree_seedlings
        "mango": 0.55,
                "mint": 0.73, #vegetable
        "mulberry": 0.9,
                "oat": 0.73, #other
                "olive": 0.73, #tree_seedlings
                "onion": 0.73, #vegetable
        "orange_fresh": 0.73,  # tree_seedlings
        "orange_processing": 0.73,  # tree_seedlings
                "palmtree": 0.73, #tree_seedlings
                "peach": 0.73, #tree_seedlings
                "peanut": 0.73, #other
                "pear": 0.73, #tree_seedlings
        "pearl_millet": 0.73,  # other
                "pineapple": 0.73, #tree_seedlings
        "pomegranate": 0.73,  # tree_seedlings
                "potato": 0.18,
                "rapeseed": 0.90,
        "raspberry": 0.73,  # other
                "rice":0.85, #wheat
        "sesame_seed": 0.9,  # cashew
                "soybean": 0.85,
        "strawberry_fresh": 0.73,  # other
        "strawberry_processing": 0.73,  # other
                "sugarbeet": 0.22,
                "sugarcane": 0.73, #other
                "sunflower": 0.85,
                "sweetcorn": 0.85, #maize
                "tea": 0.73, #other
        "tomato_fresh": 0.73,  # other
        "tomato_processing": 0.73,  # other
        "turmeric": 0.73,  # other
                "wheat": 0.85
                    }

    #src: Table 7 Freiermuth 2006
    # mg/kg TS
    _HM_SEED_VALUES = {
                "almond": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
                "apple": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
                "apricot": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "asparagus_green": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # vegetable
        "asparagus_white": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # vegetable
                "banana": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "bellpepper": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "blueberry": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
        "cabbage_red": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "cabbage_white": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "carrot": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #vegetable
        "cashew": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "cassava": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "castor_beans": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "chick_pea": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "chilli": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "cocoa": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #Other
                "coconut": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "coffee_arabica": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "coffee_robusta": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "coriander": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # vegetable
        "cotton": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "cranberry": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
        "eggplant": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "flax": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "ginger": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "grape": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "guar": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "hemp": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
        "lemon": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
        "citruslime": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
        "lentil": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "linseed": [0.09, 10.0, 73.0, 0.16, 0.83, 0.32, 0.01], #pea
                "maizegrain": [0.03, 2.5, 21.5, 0.3, 1.16, 0.32, 0],
                "mandarin": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "mango": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "mint": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #vegetable
        "mulberry": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "oat": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #Other
                "olive": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
                "onion": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #vegetable
        "orange_fresh": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
        "orange_processing": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
                "palmtree": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
                "peach": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
                "peanut": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #Other
                "pear": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "pearl_millet": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
                "pineapple": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #tree_seedlings
        "pomegranate": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # tree_seedlings
                "potato": [0.04, 6.45, 15.0, 0.55, 0.33, 0.57, 0.09],
                "rapeseed": [1.6, 3.3, 48.0, 5.25, 2.6, 0.5, 0.1],
        "raspberry": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
                "rice": [0.15, 5.0, 45.0, 0.16, 0.3, 0.3, 0.01], #wheat
        "sesame_seed": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
                "soybean": [0.06, 15.1, 47.7, 0.08, 5.32, 0.52, 0],
        "strawberry_fresh": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "strawberry_processing": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
                "sugarbeet": [0.5, 10.3, 41.4, 1.8, 1.5, 1.9, 0.0],
                "sugarcane": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #Other
                "sunflower": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],
                "sweetcorn": [0.03, 2.5, 21.5, 0.3, 1.16, 0.32, 0], #maize
                "tea": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04], #Other
        "tomato_fresh": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "tomato_processing": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
        "turmeric": [0.1, 6.6, 32.0, 0.54, 1.04, 0.55, 0.04],  # Other
                "wheat": [0.15, 5.0, 45.0, 0.16, 0.3, 0.3, 0.01]
        }

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in SeedModel._input_variables:
            setattr(self, key, inputs[key])

    def computeHeavyMetal(self):
        total_hm_values = dict.fromkeys(HeavyMetalType,0.0)
        self._add_hm_values_for_seed_type(total_hm_values, self.seed_quantities, self._HM_SEED_VALUES);
        return total_hm_values

    def _add_hm_values_for_seed_type(self,total_hm_values, seed_quantities,seed_hm_map):
        for seedKey,seedQuantity in seed_quantities.items():
            for hm_element_index,hm_element_value in enumerate(seed_hm_map[seedKey]):
                total_hm_values[HeavyMetalType(hm_element_index)] += hm_element_value * self._SEED_DM[seedKey] * seedQuantity

