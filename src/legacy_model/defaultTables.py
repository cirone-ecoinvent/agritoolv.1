from models.fertilisermodel import NFertiliserType, KFertiliserType, \
    PFertiliserType
from models.irrigationmodel import IrrigationType, WaterUseType
from models.manuremodel import LiquidManureType, SolidManureType
from models.modelEnums import SoilTexture
from models.pmodel import LandUseCategory

#Generated from GD_crop GrossEnergy_C_L1 column D, kgC/kgDM
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean: http://www.modernscientificpress.com/Journals/ViewArticle.aspx?gkN1Z6Pb60HNQPymfPQlZIiDnrBBtQSfoCsKufNADqZ4TrWuS7h5KvbfIK0SLlFq
# Chickpea:Calculated from Energy Gross Calorific data
# Coriander:https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Ginger: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Pearl Millet:https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Sesame seed: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Turmenic: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
# Pomegranate: https://www.biogeosciences-discuss.net/bg-2017-322/bg-2017-322.pdf
CARBON_CONTENT_PER_CROP = {
                "almond":0.62655914,
                "apple":0.431788079,
                "apricot":0.475,
    "asparagus_green": 0.475,
    "asparagus_white": 0.475,
                "banana":0.429522,
    "bellpepper": 0.73,
    "blueberry": 0.4494,
    "cabbage_red": 0.64,
    "cabbage_white": 0.64,
                "carrot":0.475,
    "cashew": 0.9,
    "cassava": 0.875,
    "castor_beans": 0.52,
    "chick_pea": 0.399,
    "chilli": 0.73,
                "cocoa":0.535987,
                "coconut":0.645262412752311,
    "coffee_arabica": 0.475,
    "coffee_robusta": 0.475,
    "coriander": 0.43,
    "cotton": 0.45,
    "cranberry": 0.4451,
    "eggplant": 0.54,
    "flax": 0.46,
    "ginger": 0.43,
    "grape": 0.8,
    "guar": 0.45,
    "hemp": 0.44,
    "lemon": 0.3841230769,
    "citruslime": 0.3841230769,
    "lentil": 0.6,
                "linseed":0.590234292,
                "maizegrain":0.43501682,
                "mandarin":0.3841230769,
    "mango": 0.75,
                "mint":0.445395683453237,
    "mulberry": 0.7,
                "oat":0.475,
                "olive":0.599451774112943,
                "onion":0.424377803,
    "orange_fresh": 0.3841230769,
    "orange_processing": 0.3841230769,
                "palmtree":0.599451774112943,
                "peach":0.412732283,
                "peanut":0.58063,
                "pear":0.475,
    "pearl_millet": 0.413,
                "pineapple":0.5, #no src
    "pomegranate": 0.471,
                "potato":0.423959628,
                "rapeseed":0.47088,
    "raspberry": 0.4553,
                "rice":0.475,
    "sesame_seed": 0.43,
                "soybean":0.681929577464789,
    "strawberry_fresh": 0.475,
    "strawberry_processing": 0.475,
                "sugarbeet":0.38146638,
                "sugarcane":0.475,
                "sunflower":0.842802816901409,
                "sweetcorn":0.43501682,
                "tea":0.475,
    "tomato_fresh": 0.383275862,
    "tomato_processing": 0.383275862,
    "turmeric": 0.43,
                "wheat":0.42410592
    }

#Generated from GD_crop precipitation_L1 line 16
# mm/year
ANNUAL_PRECIPITATION_PER_COUNTRY = {
   "AR":559.045870807,
   "AU":473.091499829,
   "BE":874.297532025,
   "BR":1762.97099306,
   "CA":457.469053257,
   "CL":631.170165709,
   "CN":574.773938266,
   "CO":2618.58518334,
   "CR":3268.2661656,
   "CI":1356.08177591,
   "EC":1945.27384594,
   "FI":524.701103909,
   "FR":838.929003034,
   "DE":713.499730401,
   "GH":1184.94458325,
   "HU":571.754958413,
   "IN":1072.21725144,
   "ID":2801.53519982,
   "IL":248.689445496,
   "IT":930.193617321,
   "KE":678.112942292,
   "MX":738.139128273,
    "MA": 311.100000000,
   "NL":766.068878174,
   "NZ":1790.94567393,
   "PE":1513.24211891,
   "PH":2317.59269526,
   "PL":600.659095624,
   "RU":434.795213565,
    "CS": 784.400000000,
   "ZA":474.776152751,
   "ES":622.987063842,
   "LK":1699.40728205,
   "CH":1646.41245524,
   "TH":1532.47654527,
   "TR":573.283130847,
   "UA":561.788800317,
   "US":654.536672556,
   "VN":1835.16079337
}

#from GD_crop SoilTypes_L1 line 15
CLAY_CONTENT_PER_COUNTRY = {
                            "AR":0.292466663312031,
                            "AU":0.254921189470263,
                            "BE":0.308178506375228,
                            "BR":0.437376412776413,
                            "CA":0.31123525871545,
                            "CL":0.306546165119687,
                            "CN":0.294914334944001,
                            "CO":0.366829819277108,
                            "CR":0.365213675213675,
                            "CI":0.474068430900829,
                            "EC":0.331469798657718,
                            "FI":0.345413595413595,
                            "FR":0.304420218037661,
                            "DE":0.307058249267816,
                            "GH":0.467859531772575,
                            "HU":0.279274035317201,
                            "IN":0.346841483315514,
                            "ID":0.393157729037674,
                            "IL":0.3,
                            "IT":0.301079680414597,
                            "KE":0.343026018950218,
                            "MX":0.305421469017309,
    "MA": 0.3947,
                            "NL":0.327041742286751,
                            "NZ":0.328650578675203,
                            "PE":0.338214661753093,
                            "PH":0.456787439613527,
                            "PL":0.300541961210803,
                            "RU":0.323891074146178,
    "CS": 0.458,
                            "ZA":0.291097108969607,
                            "ES":0.300886342684051,
                            "LK":0.357411764705882,
                            "CH":0.313327370304114,
                            "TH":0.470251694094869,
                            "TR":0.307997221981075,
                            "UA":0.307020760574311,
                            "US":0.332748853695815,
                            "VN":0.44672620566471
                            }


#from GD_crop Cfactor_L1
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean: (oil seeds) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Chickpea: (dried pulses) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Coriander:(other fodder crops) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Ginger:(potatoes) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Pearl millet:(MIllet and other cereals) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Sesame seed: (oil seeds) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Turmenic:(potatoes) https://www.sciencedirect.com/science/article/pii/S0264837715001611
# Pomegranate: (grove) https://www.researchgate.net/figure/235986141_TABLE-2--CORINE-land-use-code-and-corresponding-C-factor
CROP_FACTOR_PER_CROP = {
        "almond":0.1,
        "apple":0.1,
        "apricot":0.1,
    "asparagus_green": 0.5,
    "asparagus_white": 0.5,
        "banana":0.33,
    "bellpepper": 0.3,
    "blueberry": 0.3,
    "cabbage_red": 0.3,
    "cabbage_white": 0.3,
    "carrot": 0.5,
    "cashew": 0.25,
    "cassava": 0.5,
    "castor_beans": 0.23,
    "chick_pea": 0.32,
    "chilli": 0.3,
        "cocoa":0.21,
        "coconut":0.3,
    "coffee_arabica": 0.26,
    "coffee_robusta": 0.26,
    "coriander": 0.18,
    "cotton": 0.6,
    "cranberry": 0.3,
    "eggplant": 0.48,
    "flax": 0.18,
    "ginger": 0.34,
    "grape": 0.15,
    "guar": 0.3,
    "hemp": 0.45,
    "lemon": 0.1,
    "citruslime": 0.1,
    "lentil": 0.3,
        "linseed":0.18,
        "maizegrain":0.35,
        "mandarin":0.1,
    "mango": 0.25,
        "mint":0.47,
    "mulberry": 0.5,
        "oat":0.26,
        "olive":0.1,
        "onion":0.45,
    "orange_fresh": 0.1,
    "orange_processing": 0.1,
        "palmtree":0.21,
        "peach":0.1,
        "peanut":0.51,
        "pear":0.1,
    "pearl_millet": 0.18,
    "pineapple": 0.48,
    "pomegranate": 0.1,
        "potato":0.44,
        "rapeseed":0.33,
    "raspberry": 0.3,
        "rice":0.17,
    "sesame_seed": 0.28,
        "soybean":0.28,
    "strawberry_fresh": 0.47,
    "strawberry_processing": 0.47,
        "sugarbeet":0.35,
        "sugarcane":0.4,
        "sunflower":0.32,
        "sweetcorn":0.37,
        "tea":0.3,
    "tomato_fresh": 0.47,
    "tomato_processing": 0.47,
    "turmeric": 0.34,
    "wheat": 0.22
        }

#src: ecoinvent report no. 15a
# Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor beans: Calculated from Crop Carbon Content value
# Chickpea (only seed):  Calculated from Crop Carbon Content value https://books.google.ch/books?id=zf3VpYKr9aUC&pg=PA103&lpg=PA103&dq=energy+gross+calorific+value+chickpea&source=bl&ots=erh2xBkc-8&sig=G4DzPDl7hxErg1n1yBS3dy3235Q&hl=en&sa=X&ved=0ahUKEwi2goCvrpjYAhVRoqQKHbhzD_IQ6AEILTAB#v=onepage&q=energy%20gross%20calorific%20value%20chickpea&f=false
# Coriander: Calculated from Crop Carbon Content value
# Ginger: Calculated from Crop Carbon Content value
# Millet: Calculated from Crop Carbon Content value
# Sesame seed: Calculated from Crop Carbon Content value
# Turmenic: Calculated from Crop Carbon Content value
# Pomegranate: Calculated from Crop Carbon Content value
#MJ/kgDM
ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL = {
    "bellpepper": 30.92,
    "blueberry": 13.28,
    "cabbage_red": 27.17,
    "cabbage_white": 27.17,
    "cashew": 37.95,
    "cassava": 36.9,
    "castor_beans": 21.87,
    "chick_pea": 16.81,
    "chilli": 30.92,
    "coriander": 18.15,
    "cotton": 19.06,
    "cranberry": 11.91,
    "eggplant": 22.79,
    "flax": 19.19,
    "ginger": 18.15,
    "grape": 33.91,
    "guar": 18.98,
    "hemp": 18.75,
    "lentil": 25.3,
            "maizegrain": 18.52,
    "mango": 31.75,
    "mulberry": 18.98,
    "pearl_millet": 17.41,
    "pomegranate": 19.85,
            "potato": 17.59,
            "rapeseed": 26.48,
    "raspberry": 10.72,
            "rice": 18.11,#Wheat grains
    "sesame_seed": 18.15,
    "strawberry_fresh": 12.57,
    "strawberry_processing": 12.57,
            "soybean": 22.98,
            "sugarbeet": 16.43,
            "sunflower": 30.25,#sunflower grains
            "sweetcorn": 18.52,#grain maize
    "turmeric": 18.15,
            "wheat": 18.11#Wheat grains
            }

#Generated in GD_crop using "AR":{KFertiliserType.potassium_salt:0.451949860724234,    KFertiliserType.potassium_sulphate:0.139275766016713,    KFertiliserType.potassium_nitrate:0.302924791086351,    KFertiliserType.patent_potassium:0.105849582172702},
FERT_K_RATIO_PER_COUNTRY={
   "AR":{
      KFertiliserType.potassium_salt:0.451949860724234,
      KFertiliserType.potassium_sulphate:0.139275766016713,
      KFertiliserType.potassium_nitrate:0.302924791086351,
      KFertiliserType.patent_potassium:0.105849582172702
   },
   "AU":{
      KFertiliserType.potassium_salt:0.296028880866426,
      KFertiliserType.potassium_sulphate:0.108580949736184,
      KFertiliserType.potassium_nitrate:0.590391557900583,
      KFertiliserType.patent_potassium:0.00499861149680644
   },
   "BE":{
      KFertiliserType.potassium_salt:0.3710407239819,
      KFertiliserType.potassium_sulphate:0.0180995475113122,
      KFertiliserType.potassium_nitrate:0.592760180995475,
      KFertiliserType.patent_potassium:0.0180995475113122
   },
   "BR":{
      KFertiliserType.potassium_salt:0.973469946185887,
      KFertiliserType.potassium_sulphate:0.00246267976042078,
      KFertiliserType.potassium_nitrate:0.0223343771852482,
      KFertiliserType.patent_potassium:0.00173299686844426
   },
   "CA":{
      KFertiliserType.potassium_salt:0.917746113989637,
      KFertiliserType.potassium_sulphate:0.0145725388601036,
      KFertiliserType.potassium_nitrate:0.0158678756476684,
      KFertiliserType.patent_potassium:0.0518134715025907
   },
   "CL":{
      KFertiliserType.potassium_salt:0.648272167157782,
      KFertiliserType.potassium_sulphate:0.0720600053576212,
      KFertiliserType.potassium_nitrate:0.279667827484597,
      KFertiliserType.patent_potassium:0
   },
   "CN":{
      KFertiliserType.potassium_salt:0.722896546735081,
      KFertiliserType.potassium_sulphate:0.0339435840993763,
      KFertiliserType.potassium_nitrate:0.218961695267327,
      KFertiliserType.patent_potassium:0.0241981738982158
   },
   "CO":{
      KFertiliserType.potassium_salt:0.527710843373494,
      KFertiliserType.potassium_sulphate:0.0301204819277108,
      KFertiliserType.potassium_nitrate:0.403614457831325,
      KFertiliserType.patent_potassium:0.0385542168674699
   },
   "CR":{
      KFertiliserType.potassium_salt:0.861878453038674,
      KFertiliserType.potassium_sulphate:0.0386740331491713,
      KFertiliserType.potassium_nitrate:0.0552486187845304,
      KFertiliserType.patent_potassium:0.0441988950276243
   },
   "CI":{
      KFertiliserType.potassium_salt:0.233830845771144,
      KFertiliserType.potassium_sulphate:0.233830845771144,
      KFertiliserType.potassium_nitrate:0.298507462686567,
      KFertiliserType.patent_potassium:0.233830845771144
   },
   "EC":{
      KFertiliserType.potassium_salt:0.881638846737481,
      KFertiliserType.potassium_sulphate:0.0121396054628225,
      KFertiliserType.potassium_nitrate:0.106221547799697,
      KFertiliserType.patent_potassium:0
   },
   "FI":{
      KFertiliserType.potassium_salt:0,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:1,
      KFertiliserType.patent_potassium:0
   },
   "FR":{
      KFertiliserType.potassium_salt:0.417530913442362,
      KFertiliserType.potassium_sulphate:0.01770043877144,
      KFertiliserType.potassium_nitrate:0.505434782608696,
      KFertiliserType.patent_potassium:0.059333865177503
   },
   "DE":{
      KFertiliserType.potassium_salt:0.634493078937523,
      KFertiliserType.potassium_sulphate:0.0548696844993141,
      KFertiliserType.potassium_nitrate:0.287941139792992,
      KFertiliserType.patent_potassium:0.0226960967701708
   },
   "GH":{#Using GLO
      KFertiliserType.potassium_salt:0.96,
      KFertiliserType.potassium_sulphate:0.04,
      KFertiliserType.potassium_nitrate:0,
      KFertiliserType.patent_potassium:0
   },
   "HU":{
      KFertiliserType.potassium_salt:0.881720430107527,
      KFertiliserType.potassium_sulphate:0.021505376344086,
      KFertiliserType.potassium_nitrate:0.0967741935483871,
      KFertiliserType.patent_potassium:0
   },
   "IN":{
      KFertiliserType.potassium_salt:0.702927698574338,
      KFertiliserType.potassium_sulphate:0.00486252545824847,
      KFertiliserType.potassium_nitrate:0.292209775967413,
      KFertiliserType.patent_potassium:0
   },
   "ID":{
      KFertiliserType.potassium_salt:0.748280048563335,
      KFertiliserType.potassium_sulphate:0.00202347227842979,
      KFertiliserType.potassium_nitrate:0.249696479158236,
      KFertiliserType.patent_potassium:0
   },
   "IL":{
      KFertiliserType.potassium_salt:0.166666666666667,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:0.833333333333333,
      KFertiliserType.patent_potassium:0
   },
   "IT":{
      KFertiliserType.potassium_salt:0.333333333333333,
      KFertiliserType.potassium_sulphate:0.174329501915709,
      KFertiliserType.potassium_nitrate:0.440613026819923,
      KFertiliserType.patent_potassium:0.0517241379310345
   },
   "KE":{
      KFertiliserType.potassium_salt:0,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:1,
      KFertiliserType.patent_potassium:0
   },
   "MX":{
      KFertiliserType.potassium_salt:0.555328089645512,
      KFertiliserType.potassium_sulphate:0.13252882232518,
      KFertiliserType.potassium_nitrate:0.276909815752613,
      KFertiliserType.patent_potassium:0.0352332722766943
   },
    "MA": {
        KFertiliserType.potassium_salt: 0.0,
        KFertiliserType.potassium_sulphate: 0.357143,
        KFertiliserType.potassium_nitrate: 0.642857,
        KFertiliserType.patent_potassium: 0.0
    },
   "NL":{
      KFertiliserType.potassium_salt:0.492537313432836,
      KFertiliserType.potassium_sulphate:0.119402985074627,
      KFertiliserType.potassium_nitrate:0.388059701492537,
      KFertiliserType.patent_potassium:0
   },
   "NZ":{
      KFertiliserType.potassium_salt:0.869218126320733,
      KFertiliserType.potassium_sulphate:0.065977929091336,
      KFertiliserType.potassium_nitrate:0.0648039445879314,
      KFertiliserType.patent_potassium:0
   },
   "PE":{
      KFertiliserType.potassium_salt:0.790960451977401,
      KFertiliserType.potassium_sulphate:0.135593220338983,
      KFertiliserType.potassium_nitrate:0,
      KFertiliserType.patent_potassium:0.0734463276836158
   },
   "PH":{
      KFertiliserType.potassium_salt:0.169270833333333,
      KFertiliserType.potassium_sulphate:0.078125,
      KFertiliserType.potassium_nitrate:0.752604166666667,
      KFertiliserType.patent_potassium:0
   },
   "PL":{
      KFertiliserType.potassium_salt:0.293371757925072,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:0.706628242074928,
      KFertiliserType.patent_potassium:0
   },
   "RU":{
      KFertiliserType.potassium_salt:0.345803049736355,
      KFertiliserType.potassium_sulphate:0.0391905372666382,
      KFertiliserType.potassium_nitrate:0.590779535413995,
      KFertiliserType.patent_potassium:0.0242268775830127
   },
    "CS": {
        KFertiliserType.potassium_salt: 0.0,
        KFertiliserType.potassium_sulphate: 0.0,
        KFertiliserType.potassium_nitrate: 1.0,
        KFertiliserType.patent_potassium: 0.0
    },
   "ZA":{
      KFertiliserType.potassium_salt:0.149092480553155,
      KFertiliserType.potassium_sulphate:0.0280898876404494,
      KFertiliserType.potassium_nitrate:0.822817631806396,
      KFertiliserType.patent_potassium:0
   },
   "ES":{
      KFertiliserType.potassium_salt:0.290322580645161,
      KFertiliserType.potassium_sulphate:0.0552884615384615,
      KFertiliserType.potassium_nitrate:0.654388957816377,
      KFertiliserType.patent_potassium:0
   },
   "LK":{
      KFertiliserType.potassium_salt:0.948529411764706,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:0.0514705882352941,
      KFertiliserType.patent_potassium:0
   },
   "CH":{
      KFertiliserType.potassium_salt:0,
      KFertiliserType.potassium_sulphate:0.0444444444444444,
      KFertiliserType.potassium_nitrate:0.955555555555556,
      KFertiliserType.patent_potassium:0
   },
   "TH":{
      KFertiliserType.potassium_salt:0,
      KFertiliserType.potassium_sulphate:0,
      KFertiliserType.potassium_nitrate:1,
      KFertiliserType.patent_potassium:0
   },
   "TR":{
      KFertiliserType.potassium_salt:0,
      KFertiliserType.potassium_sulphate:0.0944972630365889,
      KFertiliserType.potassium_nitrate:0.905502736963411,
      KFertiliserType.patent_potassium:0
   },
   "UA":{
      KFertiliserType.potassium_salt:0.0695825049701789,
      KFertiliserType.potassium_sulphate:0.073558648111332,
      KFertiliserType.potassium_nitrate:0.78727634194831,
      KFertiliserType.patent_potassium:0.0695825049701789
   },
   "US":{
      KFertiliserType.potassium_salt:0.712309762296307,
      KFertiliserType.potassium_sulphate:0.0336612348632083,
      KFertiliserType.potassium_nitrate:0.236011361937509,
      KFertiliserType.patent_potassium:0.018017640902975
   },
   "VN":{#Using GLO
      KFertiliserType.potassium_salt:0.96,
      KFertiliserType.potassium_sulphate:0.04,
      KFertiliserType.potassium_nitrate:0,
      KFertiliserType.patent_potassium:0
   }
}

#Generated in GD_crop MineralFertiliser_L1 using =""""&C3&""":{NFertiliserType.ammonium_nitrate:"&C5&", NFertiliserType.urea:"&C6&", NFertiliserType.ureaAN:"&C7&", NFertiliserType.mono_ammonium_phosphate:"&C8&", NFertiliserType.di_ammonium_phosphate:"&C9&", NFertiliserType.an_phosphate:"&C10&", NFertiliserType.lime_ammonium_nitrate:"&C11&", NFertiliserType.ammonium_sulphate:"&C12&", NFertiliserType.potassium_nitrate:"&C13&", NFertiliserType.ammonia_liquid:"&C14&"},"
FERT_N_RATIO_PER_COUNTRY = {
    "AR":{
      NFertiliserType.ammonium_nitrate:0.0395983072479344,
      NFertiliserType.urea:0.27525693558138,
      NFertiliserType.ureaAN:0.27525693558138,
      NFertiliserType.mono_ammonium_phosphate:0.0736716598374421,
      NFertiliserType.di_ammonium_phosphate:0.0736716598374421,
      NFertiliserType.an_phosphate:0.00849734667830994,
      NFertiliserType.lime_ammonium_nitrate:0.0232081682004433,
      NFertiliserType.ammonium_sulphate:0.01309867669779,
      NFertiliserType.potassium_nitrate:0.00886679653388863,
      NFertiliserType.ammonia_liquid:0.20887351380399
    },
    "AU":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.278332092330603,
      NFertiliserType.ureaAN:0.278332092330603,
      NFertiliserType.mono_ammonium_phosphate:0.0838876478861587,
      NFertiliserType.di_ammonium_phosphate:0.0838876478861587,
      NFertiliserType.an_phosphate:0.00894349300901795,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.0821047406304294,
      NFertiliserType.potassium_nitrate:0.0278232812112187,
      NFertiliserType.ammonia_liquid:0.15668900471581
    },
    "BE":{
      NFertiliserType.ammonium_nitrate:0.00402414486921529,
      NFertiliserType.urea:0.0248155600268276,
      NFertiliserType.ureaAN:0.0248155600268276,
      NFertiliserType.mono_ammonium_phosphate:0.0140845070422535,
      NFertiliserType.di_ammonium_phosphate:0.0140845070422535,
      NFertiliserType.an_phosphate:0.0147551978537894,
      NFertiliserType.lime_ammonium_nitrate:0.622401073105299,
      NFertiliserType.ammonium_sulphate:0.028169014084507,
      NFertiliserType.potassium_nitrate:0.0321931589537223,
      NFertiliserType.ammonia_liquid:0.220657276995305
    },
    "BR":{
      NFertiliserType.ammonium_nitrate:0.152585312497487,
      NFertiliserType.urea:0.258873062724692,
      NFertiliserType.ureaAN:0.258873062724692,
      NFertiliserType.mono_ammonium_phosphate:0.0647353563299742,
      NFertiliserType.di_ammonium_phosphate:0.0647353563299742,
      NFertiliserType.an_phosphate:0.0171067341177606,
      NFertiliserType.lime_ammonium_nitrate:0.0156670982893266,
      NFertiliserType.ammonium_sulphate:0.129728077724249,
      NFertiliserType.potassium_nitrate:0.0376959392618448,
      NFertiliserType.ammonia_liquid:0
    },
    "CA":{
      NFertiliserType.ammonium_nitrate:0.0139419029717356,
      NFertiliserType.urea:0.243170312626129,
      NFertiliserType.ureaAN:0.243170312626129,
      NFertiliserType.mono_ammonium_phosphate:0.0347317519440633,
      NFertiliserType.di_ammonium_phosphate:0.0347317519440633,
      NFertiliserType.an_phosphate:0.0014972073910921,
      NFertiliserType.lime_ammonium_nitrate:0.00889099023259568,
      NFertiliserType.ammonium_sulphate:0.0653159126814811,
      NFertiliserType.potassium_nitrate:0.00449162217327629,
      NFertiliserType.ammonia_liquid:0.350058235409435
    },
    "CL":{
      NFertiliserType.ammonium_nitrate:0.00675167027383081,
      NFertiliserType.urea:0.404606191775666,
      NFertiliserType.ureaAN:0.404606191775666,
      NFertiliserType.mono_ammonium_phosphate:0.0399297387158496,
      NFertiliserType.di_ammonium_phosphate:0.0399297387158496,
      NFertiliserType.an_phosphate:0.00572441265957781,
      NFertiliserType.lime_ammonium_nitrate:0.0411216712148302,
      NFertiliserType.ammonium_sulphate:0.00564599604780277,
      NFertiliserType.potassium_nitrate:0.0501082149242496,
      NFertiliserType.ammonia_liquid:0.00157617389667827
    },
    "CN":{
      NFertiliserType.ammonium_nitrate:0.0460331280354,
      NFertiliserType.urea:0.378479415636297,
      NFertiliserType.ureaAN:0.378479415636297,
      NFertiliserType.mono_ammonium_phosphate:0.0492320852115766,
      NFertiliserType.di_ammonium_phosphate:0.0492320852115766,
      NFertiliserType.an_phosphate:0.0137500095467358,
      NFertiliserType.lime_ammonium_nitrate:0.00250407799596894,
      NFertiliserType.ammonium_sulphate:0.0101996093106173,
      NFertiliserType.potassium_nitrate:0.0260570453801313,
      NFertiliserType.ammonia_liquid:0.0460331280354
    },
    "CO":{
      NFertiliserType.ammonium_nitrate:0.0200975676789886,
      NFertiliserType.urea:0.294489487426137,
      NFertiliserType.ureaAN:0.294489487426137,
      NFertiliserType.mono_ammonium_phosphate:0.0816041409005543,
      NFertiliserType.di_ammonium_phosphate:0.0816041409005543,
      NFertiliserType.an_phosphate:0.0348128807658834,
      NFertiliserType.lime_ammonium_nitrate:0.0099628967981311,
      NFertiliserType.ammonium_sulphate:0.0584031881269754,
      NFertiliserType.potassium_nitrate:0.10443864229765,
      NFertiliserType.ammonia_liquid:0.0200975676789886
    },
    "CR":{
      NFertiliserType.ammonium_nitrate:0.2632639355272,
      NFertiliserType.urea:0.270987239758227,
      NFertiliserType.ureaAN:0.270987239758227,
      NFertiliserType.mono_ammonium_phosphate:0.0475710767853145,
      NFertiliserType.di_ammonium_phosphate:0.0475710767853145,
      NFertiliserType.an_phosphate:0.0109693306469666,
      NFertiliserType.lime_ammonium_nitrate:0.0349227669576897,
      NFertiliserType.ammonium_sulphate:0.0208193418401612,
      NFertiliserType.potassium_nitrate:0.0329079919408999,
      NFertiliserType.ammonia_liquid:0
    },
    "CI":{
      NFertiliserType.ammonium_nitrate:0.139004581424406,
      NFertiliserType.urea:0.0834027488546439,
      NFertiliserType.ureaAN:0.0834027488546439,
      NFertiliserType.mono_ammonium_phosphate:0.0369290573372206,
      NFertiliserType.di_ammonium_phosphate:0.0369290573372206,
      NFertiliserType.an_phosphate:0.0646258503401361,
      NFertiliserType.lime_ammonium_nitrate:0.111203665139525,
      NFertiliserType.ammonium_sulphate:0.111203665139525,
      NFertiliserType.potassium_nitrate:0.0830903790087464,
      NFertiliserType.ammonia_liquid:0.250208246563932
    },
    "EC":{
      NFertiliserType.ammonium_nitrate:0.0607207207207207,
      NFertiliserType.urea:0.368378378378378,
      NFertiliserType.ureaAN:0.368378378378378,
      NFertiliserType.mono_ammonium_phosphate:0.0462162162162162,
      NFertiliserType.di_ammonium_phosphate:0.0462162162162162,
      NFertiliserType.an_phosphate:0.0171171171171171,
      NFertiliserType.lime_ammonium_nitrate:0.0158558558558559,
      NFertiliserType.ammonium_sulphate:0.0257657657657658,
      NFertiliserType.potassium_nitrate:0.0513513513513514,
      NFertiliserType.ammonia_liquid:0
    },
    "FI":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.00256849315068493,
      NFertiliserType.ureaAN:0.00256849315068493,
      NFertiliserType.mono_ammonium_phosphate:0.113299086757991,
      NFertiliserType.di_ammonium_phosphate:0.113299086757991,
      NFertiliserType.an_phosphate:0.113299086757991,
      NFertiliserType.lime_ammonium_nitrate:0.315068493150685,
      NFertiliserType.ammonium_sulphate:0,
      NFertiliserType.potassium_nitrate:0.339897260273973,
      NFertiliserType.ammonia_liquid:0
    },
    "FR":{
      NFertiliserType.ammonium_nitrate:0.296814621105105,
      NFertiliserType.urea:0.079897147927198,
      NFertiliserType.ureaAN:0.079897147927198,
      NFertiliserType.mono_ammonium_phosphate:0.0210393390693892,
      NFertiliserType.di_ammonium_phosphate:0.0210393390693892,
      NFertiliserType.an_phosphate:0.0293340493674383,
      NFertiliserType.lime_ammonium_nitrate:0.140794097388421,
      NFertiliserType.ammonium_sulphate:0.00805538368142709,
      NFertiliserType.potassium_nitrate:0.0304236664837667,
      NFertiliserType.ammonia_liquid:0.292705207980667
    },
    "DE":{
      NFertiliserType.ammonium_nitrate:0.0366604449528856,
      NFertiliserType.urea:0.136398530872746,
      NFertiliserType.ureaAN:0.136398530872746,
      NFertiliserType.mono_ammonium_phosphate:0.0143124504520778,
      NFertiliserType.di_ammonium_phosphate:0.0143124504520778,
      NFertiliserType.an_phosphate:0.0345581077962088,
      NFertiliserType.lime_ammonium_nitrate:0.414546768221092,
      NFertiliserType.ammonium_sulphate:0.0443297106903092,
      NFertiliserType.potassium_nitrate:0.0217885420116206,
      NFertiliserType.ammonia_liquid:0.146694463678237
    },
    "GH":{ #Using GLO
      NFertiliserType.ammonium_nitrate:0.08,
      NFertiliserType.urea:0.66,
      NFertiliserType.ureaAN:0.05,
      NFertiliserType.mono_ammonium_phosphate:0.03,
      NFertiliserType.di_ammonium_phosphate:0.05,
      NFertiliserType.an_phosphate:0.0,
      NFertiliserType.lime_ammonium_nitrate:0.04,
      NFertiliserType.ammonium_sulphate:0.04,
      NFertiliserType.potassium_nitrate:0.0,
      NFertiliserType.ammonia_liquid:0.05
    },
    "HU":{
      NFertiliserType.ammonium_nitrate:0.351025117600071,
      NFertiliserType.urea:0.0523653146356617,
      NFertiliserType.ureaAN:0.0523653146356617,
      NFertiliserType.mono_ammonium_phosphate:0.0181947279666282,
      NFertiliserType.di_ammonium_phosphate:0.0181947279666282,
      NFertiliserType.an_phosphate:0.0217449187893849,
      NFertiliserType.lime_ammonium_nitrate:0.371882488683767,
      NFertiliserType.ammonium_sulphate:0.0103843081565634,
      NFertiliserType.potassium_nitrate:0.0386083251974794,
      NFertiliserType.ammonia_liquid:0.0652347563681548
    },
    "IN":{
      NFertiliserType.ammonium_nitrate:0.0000705535777077859,
      NFertiliserType.urea:0.397001208843117,
      NFertiliserType.ureaAN:0.397001208843117,
      NFertiliserType.mono_ammonium_phosphate:0.0607236156029803,
      NFertiliserType.di_ammonium_phosphate:0.0607236156029803,
      NFertiliserType.an_phosphate:0.0615762952052241,
      NFertiliserType.lime_ammonium_nitrate:0.00157406163741649,
      NFertiliserType.ammonium_sulphate:0.00660562587437388,
      NFertiliserType.potassium_nitrate:0.0146532612353743,
      NFertiliserType.ammonia_liquid:0.0000705535777077859
    },
    "ID":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.404818047013637,
      NFertiliserType.ureaAN:0.404818047013637,
      NFertiliserType.mono_ammonium_phosphate:0.0211474936053782,
      NFertiliserType.di_ammonium_phosphate:0.0211474936053782,
      NFertiliserType.an_phosphate:0.018258772178601,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.0750338300475646,
      NFertiliserType.potassium_nitrate:0.0547763165358031,
      NFertiliserType.ammonia_liquid:0
    },
    "IL":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.226345609065156,
      NFertiliserType.ureaAN:0.226345609065156,
      NFertiliserType.mono_ammonium_phosphate:0.0250236071765817,
      NFertiliserType.di_ammonium_phosphate:0.0250236071765817,
      NFertiliserType.an_phosphate:0.0547686496694995,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.0288951841359773,
      NFertiliserType.potassium_nitrate:0.0623229461756374,
      NFertiliserType.ammonia_liquid:0.351274787535411
    },
    "IT":{
      NFertiliserType.ammonium_nitrate:0.0436934997847611,
      NFertiliserType.urea:0.295953508394318,
      NFertiliserType.ureaAN:0.295953508394318,
      NFertiliserType.mono_ammonium_phosphate:0.0434065145644999,
      NFertiliserType.di_ammonium_phosphate:0.0434065145644999,
      NFertiliserType.an_phosphate:0.0315683742287272,
      NFertiliserType.lime_ammonium_nitrate:0.138613861386139,
      NFertiliserType.ammonium_sulphate:0.0563925957813173,
      NFertiliserType.potassium_nitrate:0.0434782608695652,
      NFertiliserType.ammonia_liquid:0.00753336203185536
    },
    "KE":{
      NFertiliserType.ammonium_nitrate:0.0301219815782923,
      NFertiliserType.urea:0.085511575802838,
      NFertiliserType.ureaAN:0.085511575802838,
      NFertiliserType.mono_ammonium_phosphate:0.170732719276409,
      NFertiliserType.di_ammonium_phosphate:0.170732719276409,
      NFertiliserType.an_phosphate:0.0506182059580118,
      NFertiliserType.lime_ammonium_nitrate:0.24520786656709,
      NFertiliserType.ammonium_sulphate:0.00970873786407767,
      NFertiliserType.potassium_nitrate:0.151854617874035,
      NFertiliserType.ammonia_liquid:0
    },
    "MA": {
        NFertiliserType.ammonium_nitrate: 0.350671,
        NFertiliserType.urea: 0.139681,
        NFertiliserType.ureaAN: 0.0,
        NFertiliserType.mono_ammonium_phosphate: 0.079069,
        NFertiliserType.di_ammonium_phosphate: 0.079069,
        NFertiliserType.an_phosphate: 0.150168,
        NFertiliserType.lime_ammonium_nitrate: 0.0,
        NFertiliserType.ammonium_sulphate: 0.051174,
        NFertiliserType.potassium_nitrate: 0.150168,
        NFertiliserType.ammonia_liquid: 0.0
    },
    "MX":{
      NFertiliserType.ammonium_nitrate:0.00473321858864028,
      NFertiliserType.urea:0.283993115318417,
      NFertiliserType.ureaAN:0.283993115318417,
      NFertiliserType.mono_ammonium_phosphate:0.035732214572576,
      NFertiliserType.di_ammonium_phosphate:0.035732214572576,
      NFertiliserType.an_phosphate:0.00932300631095812,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.236833046471601,
      NFertiliserType.potassium_nitrate:0.0451807228915663,
      NFertiliserType.ammonia_liquid:0.0644793459552496
    },
    "NL":{
      NFertiliserType.ammonium_nitrate:0.0137614678899083,
      NFertiliserType.urea:0.025802752293578,
      NFertiliserType.ureaAN:0.025802752293578,
      NFertiliserType.mono_ammonium_phosphate:0.0160550458715596,
      NFertiliserType.di_ammonium_phosphate:0.0160550458715596,
      NFertiliserType.an_phosphate:0.0986238532110092,
      NFertiliserType.lime_ammonium_nitrate:0.708715596330275,
      NFertiliserType.ammonium_sulphate:0.0160550458715596,
      NFertiliserType.potassium_nitrate:0.0424311926605505,
      NFertiliserType.ammonia_liquid:0.036697247706422
    },
    "NZ":{
      NFertiliserType.ammonium_nitrate:0.0136652025378233,
      NFertiliserType.urea:0.425852332148086,
      NFertiliserType.ureaAN:0.425852332148086,
      NFertiliserType.mono_ammonium_phosphate:0.0394152780682795,
      NFertiliserType.di_ammonium_phosphate:0.0394152780682795,
      NFertiliserType.an_phosphate:0.00145250877315299,
      NFertiliserType.lime_ammonium_nitrate:0.0032071393711218,
      NFertiliserType.ammonium_sulphate:0.0467824025657115,
      NFertiliserType.potassium_nitrate:0.00435752631945897,
      NFertiliserType.ammonia_liquid:0
    },
    "PE":{
      NFertiliserType.ammonium_nitrate:0.171799027552674,
      NFertiliserType.urea:0.303619665045921,
      NFertiliserType.ureaAN:0.303619665045921,
      NFertiliserType.mono_ammonium_phosphate:0.0560237709346299,
      NFertiliserType.di_ammonium_phosphate:0.0560237709346299,
      NFertiliserType.an_phosphate:0,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.108914100486224,
      NFertiliserType.potassium_nitrate:0,
      NFertiliserType.ammonia_liquid:0
    },
    "PH":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.319812362030905,
      NFertiliserType.ureaAN:0.319812362030905,
      NFertiliserType.mono_ammonium_phosphate:0.02906548933039,
      NFertiliserType.di_ammonium_phosphate:0.02906548933039,
      NFertiliserType.an_phosphate:0.0872884473877851,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.176600441501104,
      NFertiliserType.potassium_nitrate:0.038355408388521,
      NFertiliserType.ammonia_liquid:0
    },
    "PL":{
      NFertiliserType.ammonium_nitrate:0.330466274332277,
      NFertiliserType.urea:0.145427795382526,
      NFertiliserType.ureaAN:0.145427795382526,
      NFertiliserType.mono_ammonium_phosphate:0.0270861626678739,
      NFertiliserType.di_ammonium_phosphate:0.0270861626678739,
      NFertiliserType.an_phosphate:0.0173532518484986,
      NFertiliserType.lime_ammonium_nitrate:0.175622453598914,
      NFertiliserType.ammonium_sulphate:0.032390221819828,
      NFertiliserType.potassium_nitrate:0.0520597555454957,
      NFertiliserType.ammonia_liquid:0.0470801267541874
    },
    "RU":{
      NFertiliserType.ammonium_nitrate:0.66670472152002,
      NFertiliserType.urea:0.0251162032129169,
      NFertiliserType.ureaAN:0.0251162032129169,
      NFertiliserType.mono_ammonium_phosphate:0.053594824539944,
      NFertiliserType.di_ammonium_phosphate:0.053594824539944,
      NFertiliserType.an_phosphate:0.0284704667155943,
      NFertiliserType.lime_ammonium_nitrate:0.00587132023159097,
      NFertiliserType.ammonium_sulphate:0.0436924080567561,
      NFertiliserType.potassium_nitrate:0.085411400146783,
      NFertiliserType.ammonia_liquid:0.0124276278235342
    },
    "CS": {
        NFertiliserType.ammonium_nitrate: 0.263744773,
        NFertiliserType.urea: 0.424345671,
        NFertiliserType.ureaAN: 0.0,
        NFertiliserType.mono_ammonium_phosphate: 0.013422126,
        NFertiliserType.di_ammonium_phosphate: 0.013422126,
        NFertiliserType.an_phosphate: 0.051365443,
        NFertiliserType.lime_ammonium_nitrate: 0.182334417,
        NFertiliserType.ammonium_sulphate: 0.0,
        NFertiliserType.potassium_nitrate: 0.051365443,
        NFertiliserType.ammonia_liquid: 0.0
    },
    "ZA":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.205686630369026,
      NFertiliserType.ureaAN:0.205686630369026,
      NFertiliserType.mono_ammonium_phosphate:0.0827283726557774,
      NFertiliserType.di_ammonium_phosphate:0.0827283726557774,
      NFertiliserType.an_phosphate:0.0474894131881428,
      NFertiliserType.lime_ammonium_nitrate:0.188445251058681,
      NFertiliserType.ammonium_sulphate:0.044767090139141,
      NFertiliserType.potassium_nitrate:0.142468239564428,
      NFertiliserType.ammonia_liquid:0
    },
    "ES":{
      NFertiliserType.ammonium_nitrate:0.0587409445723592,
      NFertiliserType.urea:0.171224799236255,
      NFertiliserType.ureaAN:0.171224799236255,
      NFertiliserType.mono_ammonium_phosphate:0.0528490668463713,
      NFertiliserType.di_ammonium_phosphate:0.0528490668463713,
      NFertiliserType.an_phosphate:0.0314670260758878,
      NFertiliserType.lime_ammonium_nitrate:0.196804627393722,
      NFertiliserType.ammonium_sulphate:0.0617453810299321,
      NFertiliserType.potassium_nitrate:0.102880889537822,
      NFertiliserType.ammonia_liquid:0.100213399225024
    },
    "LK":{
      NFertiliserType.ammonium_nitrate:0.00735188121666426,
      NFertiliserType.urea:0.463889289318149,
      NFertiliserType.ureaAN:0.463889289318149,
      NFertiliserType.mono_ammonium_phosphate:0.000768824179520446,
      NFertiliserType.di_ammonium_phosphate:0.000768824179520446,
      NFertiliserType.an_phosphate:0.000480515112200279,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.0614098313391956,
      NFertiliserType.potassium_nitrate:0.00144154533660084,
      NFertiliserType.ammonia_liquid:0
    },
    "CH":{
      NFertiliserType.ammonium_nitrate:0.235496840896037,
      NFertiliserType.urea:0.0660539919586445,
      NFertiliserType.ureaAN:0.0660539919586445,
      NFertiliserType.mono_ammonium_phosphate:0.0411640819452422,
      NFertiliserType.di_ammonium_phosphate:0.0411640819452422,
      NFertiliserType.an_phosphate:0.0268045184759717,
      NFertiliserType.lime_ammonium_nitrate:0.371625502584721,
      NFertiliserType.ammonium_sulphate:0.0367604824813326,
      NFertiliserType.potassium_nitrate:0.0919012062033314,
      NFertiliserType.ammonia_liquid:0.0229753015508328
    },
    "TH":{
      NFertiliserType.ammonium_nitrate:0,
      NFertiliserType.urea:0.357545267838637,
      NFertiliserType.ureaAN:0.357545267838637,
      NFertiliserType.mono_ammonium_phosphate:0.0377718739597661,
      NFertiliserType.di_ammonium_phosphate:0.0377718739597661,
      NFertiliserType.an_phosphate:0.0517337754916185,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.1092645978181,
      NFertiliserType.potassium_nitrate:0.048367343093475,
      NFertiliserType.ammonia_liquid:0
    },
    "TR":{
      NFertiliserType.ammonium_nitrate:0.225840798942576,
      NFertiliserType.urea:0.140384050521369,
      NFertiliserType.ureaAN:0.140384050521369,
      NFertiliserType.mono_ammonium_phosphate:0.0413545797229157,
      NFertiliserType.di_ammonium_phosphate:0.0413545797229157,
      NFertiliserType.an_phosphate:0.156395334606158,
      NFertiliserType.lime_ammonium_nitrate:0.157805845204876,
      NFertiliserType.ammonium_sulphate:0.069338375679248,
      NFertiliserType.potassium_nitrate:0.0269588045234249,
      NFertiliserType.ammonia_liquid:0.000183580555147599
    },
    "UA":{
      NFertiliserType.ammonium_nitrate:0.358220392408824,
      NFertiliserType.urea:0.0858916636675225,
      NFertiliserType.ureaAN:0.0858916636675225,
      NFertiliserType.mono_ammonium_phosphate:0.0359534983708005,
      NFertiliserType.di_ammonium_phosphate:0.0359534983708005,
      NFertiliserType.an_phosphate:0.0460137147439536,
      NFertiliserType.lime_ammonium_nitrate:0.0543686459407691,
      NFertiliserType.ammonium_sulphate:0.0360621921851563,
      NFertiliserType.potassium_nitrate:0.0728248556183833,
      NFertiliserType.ammonia_liquid:0.188819875026268
    },
    "US":{
      NFertiliserType.ammonium_nitrate:0.0296294084780968,
      NFertiliserType.urea:0.115445720646755,
      NFertiliserType.ureaAN:0.115445720646755,
      NFertiliserType.mono_ammonium_phosphate:0.0407772228453957,
      NFertiliserType.di_ammonium_phosphate:0.0407772228453957,
      NFertiliserType.an_phosphate:0.0321020800723355,
      NFertiliserType.lime_ammonium_nitrate:0,
      NFertiliserType.ammonium_sulphate:0.0228948704059916,
      NFertiliserType.potassium_nitrate:0.0409990062397905,
      NFertiliserType.ammonia_liquid:0.561928747819485
    },
    "VN":{ #Using GLO
      NFertiliserType.ammonium_nitrate:0.08,
      NFertiliserType.urea:0.66,
      NFertiliserType.ureaAN:0.05,
      NFertiliserType.mono_ammonium_phosphate:0.03,
      NFertiliserType.di_ammonium_phosphate:0.05,
      NFertiliserType.an_phosphate:0.0,
      NFertiliserType.lime_ammonium_nitrate:0.04,
      NFertiliserType.ammonium_sulphate:0.04,
      NFertiliserType.potassium_nitrate:0.0,
      NFertiliserType.ammonia_liquid:0.05
      }
}

# Generated in GD_crop using "AR":{PFertiliserType.triple_superphosphate:0.0790316503391107,   PFertiliserType.superphosphate:0.14764925060705,   PFertiliserType.mono_ammonium_phosphate:0.376231544279773,   PFertiliserType.di_ammonium_phosphate:0.376231544279773,  PFertiliserType.an_phosphate:0.0144296519579112,   PFertiliserType.hypophosphate_raw_phosphate:0.00321317926819057,  PFertiliserType.ground_basic_slag:0.00321317926819057},
FERT_P_RATIO_PER_COUNTRY = {
   "AR":{
      PFertiliserType.triple_superphosphate:0.0790316503391107,
      PFertiliserType.superphosphate:0.14764925060705,
      PFertiliserType.mono_ammonium_phosphate:0.376231544279773,
      PFertiliserType.di_ammonium_phosphate:0.376231544279773,
      PFertiliserType.an_phosphate:0.0144296519579112,
      PFertiliserType.hypophosphate_raw_phosphate:0.00321317926819057,
      PFertiliserType.ground_basic_slag:0.00321317926819057
   },
   "AU":{
      PFertiliserType.triple_superphosphate:0.0126986152766256,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.444557888243677,
      PFertiliserType.di_ammonium_phosphate:0.444557888243677,
      PFertiliserType.an_phosphate:0.0981856082360198,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "BE":{
      PFertiliserType.triple_superphosphate:0.139784946236559,
      PFertiliserType.superphosphate:0.0860215053763441,
      PFertiliserType.mono_ammonium_phosphate:0.245519713261649,
      PFertiliserType.di_ammonium_phosphate:0.245519713261649,
      PFertiliserType.an_phosphate:0.175627240143369,
      PFertiliserType.hypophosphate_raw_phosphate:0.0537634408602151,
      PFertiliserType.ground_basic_slag:0.0537634408602151
   },
   "BR":{
      PFertiliserType.triple_superphosphate:0.226250372380921,
      PFertiliserType.superphosphate:0.27231306477773,
      PFertiliserType.mono_ammonium_phosphate:0.227412752529432,
      PFertiliserType.di_ammonium_phosphate:0.227412752529432,
      PFertiliserType.an_phosphate:0.0239736078470314,
      PFertiliserType.hypophosphate_raw_phosphate:0.0219936446989507,
      PFertiliserType.ground_basic_slag:0.00064380523650326
   },
   "CA":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.479439043468544,
      PFertiliserType.di_ammonium_phosphate:0.479439043468544,
      PFertiliserType.an_phosphate:0.0411219130629121,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "CL":{
      PFertiliserType.triple_superphosphate:0.455731780766914,
      PFertiliserType.superphosphate:0.00301144348524393,
      PFertiliserType.mono_ammonium_phosphate:0.269959178210533,
      PFertiliserType.di_ammonium_phosphate:0.269959178210533,
      PFertiliserType.an_phosphate:0.00133841932677508,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "CN":{
      PFertiliserType.triple_superphosphate:0.0182834418893969,
      PFertiliserType.superphosphate:0.192939750935296,
      PFertiliserType.mono_ammonium_phosphate:0.361376933139892,
      PFertiliserType.di_ammonium_phosphate:0.361376933139892,
      PFertiliserType.an_phosphate:0.0453484490835208,
      PFertiliserType.hypophosphate_raw_phosphate:0.0140226987942277,
      PFertiliserType.ground_basic_slag:0.00665179301777467
   },
   "CO":{
      PFertiliserType.triple_superphosphate:0.00736485491235823,
      PFertiliserType.superphosphate:0.00736485491235823,
      PFertiliserType.mono_ammonium_phosphate:0.425492217803309,
      PFertiliserType.di_ammonium_phosphate:0.425492217803309,
      PFertiliserType.an_phosphate:0.0900967250945156,
      PFertiliserType.hypophosphate_raw_phosphate:0.0368242745617911,
      PFertiliserType.ground_basic_slag:0.00736485491235823
   },
   "CR":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.333333333333333,
      PFertiliserType.di_ammonium_phosphate:0.333333333333333,
      PFertiliserType.an_phosphate:0.333333333333333,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "CI":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.291666666666667,
      PFertiliserType.di_ammonium_phosphate:0.291666666666667,
      PFertiliserType.an_phosphate:0.416666666666667,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "EC":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.442105263157895,
      PFertiliserType.di_ammonium_phosphate:0.442105263157895,
      PFertiliserType.an_phosphate:0.115789473684211,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "FI":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.333333333333333,
      PFertiliserType.di_ammonium_phosphate:0.333333333333333,
      PFertiliserType.an_phosphate:0.333333333333333,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "FR":{
      PFertiliserType.triple_superphosphate:0.165198297965196,
      PFertiliserType.superphosphate:0.0500927390758824,
      PFertiliserType.mono_ammonium_phosphate:0.269325186841962,
      PFertiliserType.di_ammonium_phosphate:0.269325186841962,
      PFertiliserType.an_phosphate:0.231193060935028,
      PFertiliserType.hypophosphate_raw_phosphate:0.0127788991326169,
      PFertiliserType.ground_basic_slag:0.00208662920735366
   },
   "DE":{
      PFertiliserType.triple_superphosphate:0.0722977469341192,
      PFertiliserType.superphosphate:0.006416959787052,
      PFertiliserType.mono_ammonium_phosphate:0.236492695756884,
      PFertiliserType.di_ammonium_phosphate:0.236492695756884,
      PFertiliserType.an_phosphate:0.435465982190956,
      PFertiliserType.hypophosphate_raw_phosphate:0.006416959787052,
      PFertiliserType.ground_basic_slag:0.006416959787052
   },
   "GH":{#Using GLO
      PFertiliserType.triple_superphosphate:0.09,
      PFertiliserType.superphosphate:0.24,
      PFertiliserType.mono_ammonium_phosphate:0.24,
      PFertiliserType.di_ammonium_phosphate:0.42,
      PFertiliserType.an_phosphate:0,
      PFertiliserType.hypophosphate_raw_phosphate:0.01,
      PFertiliserType.ground_basic_slag:0
   },
   "HU":{
      PFertiliserType.triple_superphosphate:0.0075223319228961,
      PFertiliserType.superphosphate:0.0493653032440056,
      PFertiliserType.mono_ammonium_phosphate:0.352452593637361,
      PFertiliserType.di_ammonium_phosphate:0.352452593637361,
      PFertiliserType.an_phosphate:0.233505720106566,
      PFertiliserType.hypophosphate_raw_phosphate:0.00235072872590503,
      PFertiliserType.ground_basic_slag:0.00235072872590503
   },
   "IN":{
      PFertiliserType.triple_superphosphate:0.00444211040383734,
      PFertiliserType.superphosphate:0.0816371585211251,
      PFertiliserType.mono_ammonium_phosphate:0.366667558656708,
      PFertiliserType.di_ammonium_phosphate:0.366667558656708,
      PFertiliserType.an_phosphate:0.179679128882526,
      PFertiliserType.hypophosphate_raw_phosphate:0.000906484879096325,
      PFertiliserType.ground_basic_slag:0
   },
   "ID":{
      PFertiliserType.triple_superphosphate:0.252142206016408,
      PFertiliserType.superphosphate:0.0752051048313583,
      PFertiliserType.mono_ammonium_phosphate:0.195016712245518,
      PFertiliserType.di_ammonium_phosphate:0.195016712245518,
      PFertiliserType.an_phosphate:0.158189000303859,
      PFertiliserType.hypophosphate_raw_phosphate:0.124430264357338,
      PFertiliserType.ground_basic_slag:0
   },
   "IL":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.177777777777778,
      PFertiliserType.di_ammonium_phosphate:0.177777777777778,
      PFertiliserType.an_phosphate:0.644444444444444,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "IT":{
      PFertiliserType.triple_superphosphate:0.0873425692695214,
      PFertiliserType.superphosphate:0.0670654911838791,
      PFertiliserType.mono_ammonium_phosphate:0.340428211586902,
      PFertiliserType.di_ammonium_phosphate:0.340428211586902,
      PFertiliserType.an_phosphate:0.154030226700252,
      PFertiliserType.hypophosphate_raw_phosphate:0.00535264483627204,
      PFertiliserType.ground_basic_slag:0.00535264483627204
   },
   "KE":{
      PFertiliserType.triple_superphosphate:0.00366422385076616,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.469298245614035,
      PFertiliserType.di_ammonium_phosphate:0.469298245614035,
      PFertiliserType.an_phosphate:0.0577392849211637,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "MX":{
      PFertiliserType.triple_superphosphate:0.0199776112976836,
      PFertiliserType.superphosphate:0.0309997416688194,
      PFertiliserType.mono_ammonium_phosphate:0.441215304687276,
      PFertiliserType.di_ammonium_phosphate:0.441215304687276,
      PFertiliserType.an_phosphate:0.0665920376589454,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
    "MA": {
        PFertiliserType.triple_superphosphate: 0.029907,
        PFertiliserType.superphosphate: 0.0,
        PFertiliserType.mono_ammonium_phosphate: 0.291033,
        PFertiliserType.di_ammonium_phosphate: 0.291033,
        PFertiliserType.an_phosphate: 0.388027,
        PFertiliserType.hypophosphate_raw_phosphate: 0,
        PFertiliserType.ground_basic_slag: 0
    },
   "NL":{
      PFertiliserType.triple_superphosphate:0.0253164556962025,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.310126582278481,
      PFertiliserType.di_ammonium_phosphate:0.310126582278481,
      PFertiliserType.an_phosphate:0.354430379746835,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "NZ":{
      PFertiliserType.triple_superphosphate:0.00657643190334174,
      PFertiliserType.superphosphate:0.377074252504397,
      PFertiliserType.mono_ammonium_phosphate:0.23736330962759,
      PFertiliserType.di_ammonium_phosphate:0.23736330962759,
      PFertiliserType.an_phosphate:0.134663913741684,
      PFertiliserType.hypophosphate_raw_phosphate:0.0069587825953965,
      PFertiliserType.ground_basic_slag:0
   },
   "PE":{
      PFertiliserType.triple_superphosphate:0.00749063670411985,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.49625468164794,
      PFertiliserType.di_ammonium_phosphate:0.49625468164794,
      PFertiliserType.an_phosphate:0,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "PH":{
      PFertiliserType.triple_superphosphate:0.0622093023255814,
      PFertiliserType.superphosphate:0.00174418604651163,
      PFertiliserType.mono_ammonium_phosphate:0.261627906976744,
      PFertiliserType.di_ammonium_phosphate:0.261627906976744,
      PFertiliserType.an_phosphate:0.412790697674419,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "PL":{
      PFertiliserType.triple_superphosphate:0.126016260162602,
      PFertiliserType.superphosphate:0.0623306233062331,
      PFertiliserType.mono_ammonium_phosphate:0.290311653116531,
      PFertiliserType.di_ammonium_phosphate:0.290311653116531,
      PFertiliserType.an_phosphate:0.209349593495935,
      PFertiliserType.hypophosphate_raw_phosphate:0.010840108401084,
      PFertiliserType.ground_basic_slag:0.010840108401084
   },
   "RU":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0.00284769428623921,
      PFertiliserType.mono_ammonium_phosphate:0.434732684181518,
      PFertiliserType.di_ammonium_phosphate:0.434732684181518,
      PFertiliserType.an_phosphate:0.120889215506155,
      PFertiliserType.hypophosphate_raw_phosphate:0.00679772184457101,
      PFertiliserType.ground_basic_slag:0
   },
    "CS": {
        PFertiliserType.triple_superphosphate: 0.0,
        PFertiliserType.superphosphate: 0.0,
        PFertiliserType.mono_ammonium_phosphate: 0.331671,
        PFertiliserType.di_ammonium_phosphate: 0.331671,
        PFertiliserType.an_phosphate: 0.336658,
        PFertiliserType.hypophosphate_raw_phosphate: 0,
        PFertiliserType.ground_basic_slag: 0
    },
   "ZA":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.360310928212163,
      PFertiliserType.di_ammonium_phosphate:0.360310928212163,
      PFertiliserType.an_phosphate:0.279378143575674,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "ES":{
      PFertiliserType.triple_superphosphate:0.027861710350643,
      PFertiliserType.superphosphate:0.054985594828192,
      PFertiliserType.mono_ammonium_phosphate:0.347012390790059,
      PFertiliserType.di_ammonium_phosphate:0.347012390790059,
      PFertiliserType.an_phosphate:0.178225938678472,
      PFertiliserType.hypophosphate_raw_phosphate:0.0224509872812873,
      PFertiliserType.ground_basic_slag:0.0224509872812873
   },
   "LK":{
      PFertiliserType.triple_superphosphate:0.675675675675676,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.042042042042042,
      PFertiliserType.di_ammonium_phosphate:0.042042042042042,
      PFertiliserType.an_phosphate:0.042042042042042,
      PFertiliserType.hypophosphate_raw_phosphate:0.198198198198198,
      PFertiliserType.ground_basic_slag:0
   },
   "CH":{
      PFertiliserType.triple_superphosphate:0.136363636363636,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.303030303030303,
      PFertiliserType.di_ammonium_phosphate:0.303030303030303,
      PFertiliserType.an_phosphate:0.257575757575758,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "TH":{
      PFertiliserType.triple_superphosphate:0,
      PFertiliserType.superphosphate:0,
      PFertiliserType.mono_ammonium_phosphate:0.415413533834587,
      PFertiliserType.di_ammonium_phosphate:0.415413533834587,
      PFertiliserType.an_phosphate:0.169172932330827,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "TR":{
      PFertiliserType.triple_superphosphate:0.0201021663040393,
      PFertiliserType.superphosphate:0.00132437801532495,
      PFertiliserType.mono_ammonium_phosphate:0.271844354050389,
      PFertiliserType.di_ammonium_phosphate:0.271844354050389,
      PFertiliserType.an_phosphate:0.434884747579857,
      PFertiliserType.hypophosphate_raw_phosphate:0,
      PFertiliserType.ground_basic_slag:0
   },
   "UA":{
      PFertiliserType.triple_superphosphate:0.0580786146613172,
      PFertiliserType.superphosphate:0.0630420096234713,
      PFertiliserType.mono_ammonium_phosphate:0.288871884665407,
      PFertiliserType.di_ammonium_phosphate:0.288871884665407,
      PFertiliserType.an_phosphate:0.184978377061762,
      PFertiliserType.hypophosphate_raw_phosphate:0.0580786146613172,
      PFertiliserType.ground_basic_slag:0.0580786146613172
   },
   "US":{
      PFertiliserType.triple_superphosphate:0.0138193133212593,
      PFertiliserType.superphosphate:0.00444266759148652,
      PFertiliserType.mono_ammonium_phosphate:0.362503692857051,
      PFertiliserType.di_ammonium_phosphate:0.362503692857051,
      PFertiliserType.an_phosphate:0.247845298190179,
      PFertiliserType.hypophosphate_raw_phosphate:0.00444266759148652,
      PFertiliserType.ground_basic_slag:0.00444266759148652
   },
   "VN":{#Using GLO
      PFertiliserType.triple_superphosphate:0.09,
      PFertiliserType.superphosphate:0.24,
      PFertiliserType.mono_ammonium_phosphate:0.24,
      PFertiliserType.di_ammonium_phosphate:0.42,
      PFertiliserType.an_phosphate:0,
      PFertiliserType.hypophosphate_raw_phosphate:0.01,
      PFertiliserType.ground_basic_slag:0
   }
}

# Generated in GD_crop (combinaison of IrrTechn_L0 and IrrTechn_L1)
# using =""""&B$3&""":{IrrigationType.surface_irrigation_no_energy:0.0"&",  IrrigationType.surface_irrigation_electricity:"&B5&",  IrrigationType.surface_irrigation_diesel:"&B6&",  IrrigationType.sprinkler_irrigation_electricity:"&B7&",  IrrigationType.sprinkler_irrigation_diesel:"&B8&",  IrrigationType.drip_irrigation_electricity:"&B9&", IrrigationType.drip_irrigation_diesel:"&B10&"},"
IRR_TECH_RATIO_PER_COUNTRY = {
   "AR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "AU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.718978388998035,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.206082514734774,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0749390962671906,
      IrrigationType.drip_irrigation_diesel:0
   },
   "BE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "BR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.192036629213483,
      IrrigationType.surface_irrigation_diesel:0.192036629213483,
      IrrigationType.sprinkler_irrigation_electricity:0.271124494382022,
      IrrigationType.sprinkler_irrigation_diesel:0.271124494382022,
      IrrigationType.drip_irrigation_electricity:0.0368388764044944,
      IrrigationType.drip_irrigation_diesel:0.0368388764044944
   },
   "CA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.207973563218391,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.785090804597701,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00693563218390805,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CI":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "CL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.964220183486238,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0146788990825688,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0211009174311927,
      IrrigationType.drip_irrigation_diesel:0
   },
   "CN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.461248060708263,
      IrrigationType.surface_irrigation_diesel:0.461248060708263,
      IrrigationType.sprinkler_irrigation_electricity:0.024677150084317,
      IrrigationType.sprinkler_irrigation_diesel:0.024677150084317,
      IrrigationType.drip_irrigation_electricity:0.0140747892074199,
      IrrigationType.drip_irrigation_diesel:0.0140747892074199
   },
   "CO":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "CR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.225806451612903,
      IrrigationType.surface_irrigation_diesel:0.67741935483871,
      IrrigationType.sprinkler_irrigation_electricity:0.0161290322580645,
      IrrigationType.sprinkler_irrigation_diesel:0.0483870967741936,
      IrrigationType.drip_irrigation_electricity:0.00806451612903226,
      IrrigationType.drip_irrigation_diesel:0.0241935483870968
   },
   "DE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "EC":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "ES":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.296592219020173,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.225506628242075,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.477901152737752,
      IrrigationType.drip_irrigation_diesel:0
   },
   "FI":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.857142857142857,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.142857142857143,
      IrrigationType.drip_irrigation_diesel:0
   },
   "FR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.488586206896552,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.475793103448276,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0356206896551724,
      IrrigationType.drip_irrigation_diesel:0
   },
   "GH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "HU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.127272727272727,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.840909090909091,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0318181818181818,
      IrrigationType.drip_irrigation_diesel:0
   },
   "ID":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "IL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0043290043290044,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.25974025974026,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.735930735930736,
      IrrigationType.drip_irrigation_diesel:0
   },
   "IN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.459423481116585,
      IrrigationType.surface_irrigation_diesel:0.459423481116585,
      IrrigationType.sprinkler_irrigation_electricity:0.0249995073891626,
      IrrigationType.sprinkler_irrigation_diesel:0.0249995073891626,
      IrrigationType.drip_irrigation_electricity:0.0155770114942529,
      IrrigationType.drip_irrigation_diesel:0.0155770114942529
   },
   "IT":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.41882734082397,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.367476779026217,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.213695880149813,
      IrrigationType.drip_irrigation_diesel:0
   },
   "KE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.22,
      IrrigationType.surface_irrigation_diesel:0.66,
      IrrigationType.sprinkler_irrigation_electricity:0.02875,
      IrrigationType.sprinkler_irrigation_diesel:0.08625,
      IrrigationType.drip_irrigation_electricity:0.00125,
      IrrigationType.drip_irrigation_diesel:0.00375
   },
   "LK":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "MX":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.903225806451613,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0645161290322581,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.032258064516129,
      IrrigationType.drip_irrigation_diesel:0
   },
    "MA": {
        IrrigationType.surface_irrigation_no_energy: 0.0,
        IrrigationType.surface_irrigation_electricity: 0.0715,
        IrrigationType.surface_irrigation_diesel: 0.6435,
        IrrigationType.sprinkler_irrigation_electricity: 0.0085,
        IrrigationType.sprinkler_irrigation_diesel: 0.0765,
        IrrigationType.drip_irrigation_electricity: 0.02,
        IrrigationType.drip_irrigation_diesel: 0.18
    },
   "NL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "NZ":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.0185185185185185,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.972222222222222,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.00925925925925926,
      IrrigationType.drip_irrigation_diesel:0
   },
   "PE":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.24105504587156,
      IrrigationType.surface_irrigation_diesel:0.723165137614679,
      IrrigationType.sprinkler_irrigation_electricity:0.0036697247706422,
      IrrigationType.sprinkler_irrigation_diesel:0.0110091743119266,
      IrrigationType.drip_irrigation_electricity:0.00527522935779817,
      IrrigationType.drip_irrigation_diesel:0.0158256880733945
   },
   "PH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.247728618421053,
      IrrigationType.surface_irrigation_diesel:0.743185855263158,
      IrrigationType.sprinkler_irrigation_electricity:0.00118009868421053,
      IrrigationType.sprinkler_irrigation_diesel:0.00354029605263158,
      IrrigationType.drip_irrigation_electricity:0.00109128289473684,
      IrrigationType.drip_irrigation_diesel:0.00327384868421053
   },
   "PL":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.87,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.05,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.08,
      IrrigationType.drip_irrigation_diesel:0
   },
   "RU":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.229022988505747,
      IrrigationType.surface_irrigation_diesel:0.687068965517241,
      IrrigationType.sprinkler_irrigation_electricity:0.0132183908045977,
      IrrigationType.sprinkler_irrigation_diesel:0.0396551724137931,
      IrrigationType.drip_irrigation_electricity:0.00775862068965517,
      IrrigationType.drip_irrigation_diesel:0.0232758620689655
   },
    "CS": {
        IrrigationType.surface_irrigation_no_energy: 0.0,
        IrrigationType.surface_irrigation_electricity: 0.0251,
        IrrigationType.surface_irrigation_diesel: 0.0251,
        IrrigationType.sprinkler_irrigation_electricity: 0.44655,
        IrrigationType.sprinkler_irrigation_diesel: 0.44655,
        IrrigationType.drip_irrigation_electricity: 0.02835,
        IrrigationType.drip_irrigation_diesel: 0.02835
    },
   "TH":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "TR":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.878277153558053,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.0936329588014981,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0280898876404494,
      IrrigationType.drip_irrigation_diesel:0
   },
   "UA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.25,
      IrrigationType.sprinkler_irrigation_diesel:0.75,
      IrrigationType.drip_irrigation_electricity:0,
      IrrigationType.drip_irrigation_diesel:0
   },
   "US":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.433690111336032,
      IrrigationType.surface_irrigation_diesel:0,
      IrrigationType.sprinkler_irrigation_electricity:0.49992624048583,
      IrrigationType.sprinkler_irrigation_diesel:0,
      IrrigationType.drip_irrigation_electricity:0.0663836481781377,
      IrrigationType.drip_irrigation_diesel:0
   },
   "VN":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.245394736842105,
      IrrigationType.surface_irrigation_diesel:0.736184210526316,
      IrrigationType.sprinkler_irrigation_electricity:0.00131578947368421,
      IrrigationType.sprinkler_irrigation_diesel:0.00394736842105263,
      IrrigationType.drip_irrigation_electricity:0.00328947368421053,
      IrrigationType.drip_irrigation_diesel:0.00986842105263158
   },
   "ZA":{
      IrrigationType.surface_irrigation_no_energy:0.0,
      IrrigationType.surface_irrigation_electricity:0.115149401197605,
      IrrigationType.surface_irrigation_diesel:0.115149401197605,
      IrrigationType.sprinkler_irrigation_electricity:0.275466766467066,
      IrrigationType.sprinkler_irrigation_diesel:0.275466766467066,
      IrrigationType.drip_irrigation_electricity:0.109383832335329,
      IrrigationType.drip_irrigation_diesel:0.109383832335329
   }
}

#Generated in GD_crop (IrrWaterSource_L1)
# using =""""&C$3&""":{WaterUseType.groundwater:"&C4 &",  WaterUseType.surfacewater:"&C5 &", WaterUseType.nonconventional:"&C6&"},"
IRR_WATERUSE_RATIO_PER_COUNTRY = {
   "AR":{
      WaterUseType.groundwater:0.23914616909283,
      WaterUseType.surfacewater:0.76085383090717,
      WaterUseType.nonconventional:0.0
   },
   "AU":{
      WaterUseType.groundwater:0.211339450682171,
      WaterUseType.surfacewater:0.769530030353248,
      WaterUseType.nonconventional:0.0191305189645816
   },
   "BE":{
      WaterUseType.groundwater:0.580962162162162,
      WaterUseType.surfacewater:0.419037837837838,
      WaterUseType.nonconventional:0.0
   },
   "BR":{
      WaterUseType.groundwater:0.187805022645312,
      WaterUseType.surfacewater:0.812194977354688,
      WaterUseType.nonconventional:0.0
   },
   "CA":{
      WaterUseType.groundwater:0.08577824612747,
      WaterUseType.surfacewater:0.91422175387253,
      WaterUseType.nonconventional:0.0
   },
   "CL":{
      WaterUseType.groundwater:0.0543166377237681,
      WaterUseType.surfacewater:0.945683362276232,
      WaterUseType.nonconventional:0.0
   },
   "CN":{
      WaterUseType.groundwater:0.297593503621964,
      WaterUseType.surfacewater:0.702406496378036,
      WaterUseType.nonconventional:0.0
   },
   "CO":{
      WaterUseType.groundwater:0.05,
      WaterUseType.surfacewater:0.95,
      WaterUseType.nonconventional:0.0
   },
   "CR":{
      WaterUseType.groundwater:0.17,
      WaterUseType.surfacewater:0.83,
      WaterUseType.nonconventional:0.0
   },
   "CI":{
      WaterUseType.groundwater:0.0,
      WaterUseType.surfacewater:1.0,
      WaterUseType.nonconventional:0.0
   },
   "EC":{
      WaterUseType.groundwater:0.118820056727693,
      WaterUseType.surfacewater:0.881179943272307,
      WaterUseType.nonconventional:0.0
   },
   "FI":{
      WaterUseType.groundwater:0.15,
      WaterUseType.surfacewater:0.85,
      WaterUseType.nonconventional:0.0
   },
   "FR":{
      WaterUseType.groundwater:0.446022143207711,
      WaterUseType.surfacewater:0.553977856792289,
      WaterUseType.nonconventional:0.0
   },
   "DE":{
      WaterUseType.groundwater:0.787726881335413,
      WaterUseType.surfacewater:0.212273118664586,
      WaterUseType.nonconventional:0.0
   },
   "GH":{
      WaterUseType.groundwater:0.214630656412091,
      WaterUseType.surfacewater:0.7639062779467,
      WaterUseType.nonconventional:0.0214630656412091
   },
   "HU":{
      WaterUseType.groundwater:0.220485875706215,
      WaterUseType.surfacewater:0.779514124293785,
      WaterUseType.nonconventional:0.0
   },
   "IN":{
      WaterUseType.groundwater:0.633925342549058,
      WaterUseType.surfacewater:0.366074657450942,
      WaterUseType.nonconventional:0.0
   },
   "ID":{
      WaterUseType.groundwater:0.00998417468157694,
      WaterUseType.surfacewater:0.990015825318423,
      WaterUseType.nonconventional:0.0
   },
   "IL":{
      WaterUseType.groundwater:0.49,
      WaterUseType.surfacewater:0.33,
      WaterUseType.nonconventional:0.18
   },
   "IT":{
      WaterUseType.groundwater:0.32698606155749,
      WaterUseType.surfacewater:0.67301393844251,
      WaterUseType.nonconventional:0.0
   },
   "KE":{
      WaterUseType.groundwater:0.0099998969189061,
      WaterUseType.surfacewater:0.990000103081094,
      WaterUseType.nonconventional:0.0
   },
   "MX":{
      WaterUseType.groundwater:0.387889248911863,
      WaterUseType.surfacewater:0.612110751088137,
      WaterUseType.nonconventional:0.0
   },
    "MA": {
        WaterUseType.groundwater: 0.5419,
        WaterUseType.surfacewater: 0.4563,
        WaterUseType.nonconventional: 0.0018
    },
   "NL":{
      WaterUseType.groundwater:0.58029522431259,
      WaterUseType.surfacewater:0.41970477568741,
      WaterUseType.nonconventional:0.0
   },
   "NZ":{
      WaterUseType.groundwater:0.306927386271384,
      WaterUseType.surfacewater:0.693072613728616,
      WaterUseType.nonconventional:0.0
   },
   "PE":{
      WaterUseType.groundwater:0.283358103917645,
      WaterUseType.surfacewater:0.716641896082355,
      WaterUseType.nonconventional:0.0
   },
   "PH":{
      WaterUseType.groundwater:0.135192998290657,
      WaterUseType.surfacewater:0.864807001709343,
      WaterUseType.nonconventional:0.0
   },
   "PL":{
      WaterUseType.groundwater:0.1,
      WaterUseType.surfacewater:0.9,
      WaterUseType.nonconventional:0.0
   },
   "RU":{
      WaterUseType.groundwater:0.36,
      WaterUseType.surfacewater:0.64,
      WaterUseType.nonconventional:0.0
   },
    "CS": {
        WaterUseType.groundwater: 0.9466,
        WaterUseType.surfacewater: 0.0534,
        WaterUseType.nonconventional: 0.0
    },
   "ZA":{
      WaterUseType.groundwater:0.085,
      WaterUseType.surfacewater:0.915,
      WaterUseType.nonconventional:0.0
   },
   "ES":{
      WaterUseType.groundwater:0.371089129707478,
      WaterUseType.surfacewater:0.628910870292522,
      WaterUseType.nonconventional:0.0
   },
   "LK":{
      WaterUseType.groundwater:0.0119794385964912,
      WaterUseType.surfacewater:0.988020561403509,
      WaterUseType.nonconventional:0.0
   },
   "CH":{
      WaterUseType.groundwater:0.22,
      WaterUseType.surfacewater:0.78,
      WaterUseType.nonconventional:0.0
   },
   "TH":{
      WaterUseType.groundwater:0.0911128154913198,
      WaterUseType.surfacewater:0.90888718450868,
      WaterUseType.nonconventional:0.0
   },
   "TR":{
      WaterUseType.groundwater:0.493354749015524,
      WaterUseType.surfacewater:0.506645250984476,
      WaterUseType.nonconventional:0.0
   },
   "UA":{
      WaterUseType.groundwater:0.0,
      WaterUseType.surfacewater:1.0,
      WaterUseType.nonconventional:0.0
   },
   "US":{
      WaterUseType.groundwater:0.602191204788111,
      WaterUseType.surfacewater:0.397808795211889,
      WaterUseType.nonconventional:0.0
   },
   "VN":{
      WaterUseType.groundwater:0.01,
      WaterUseType.surfacewater:0.99,
      WaterUseType.nonconventional:0.0
   }
}

EI_IRR_RATIO_TO_AIR = {
    "BR": 0.62,
    "CA": 0.75,
    "CN": 0.51,
    "CO": 0.52,
    "FR": 0.75,
    "DE": 0.78,
    "IN": 0.51,
    "MA": 0.56,
    "PE": 0.52,
    "PH": 0.50,
    "CS": 0.74,
    "ZA": 0.71,
    "ES": 0.70,
    "US": 0.66,
    "GLO": 0.55
}

EI_IRR_RATIO_TO_RIVER = {
    "BR": 0.08,
    "CA": 0.05,
    "CN": 0.10,
    "CO": 0.10,
    "FR": 0.05,
    "DE": 0.04,
    "IN": 0.10,
    "MA": 0.09,
    "PE": 0.10,
    "PH": 0.10,
    "CS": 0.05,
    "ZA": 0.06,
    "ES": 0.06,
    "US": 0.07,
    "GLO": 0.09
}

EI_IRR_RATIO_TO_GROUNDWATER = {
    "BR": 0.30,
    "CA": 0.20,
    "CN": 0.39,
    "CO": 0.38,
    "FR": 0.20,
    "DE": 0.18,
    "IN": 0.39,
    "MA": 0.35,
    "PE": 0.38,
    "PH": 0.40,
    "CS": 0.21,
    "ZA": 0.23,
    "ES": 0.24,
    "US": 0.27,
    "GLO": 0.36
}

LAND_USE_CATEGORY_PER_CROP = {
        "almond":LandUseCategory.fruit_trees,
        "apple":LandUseCategory.fruit_trees,
        "apricot":LandUseCategory.fruit_trees,
    "asparagus_green": LandUseCategory.vegetables,
    "asparagus_white": LandUseCategory.vegetables,
        "banana":LandUseCategory.fruit_trees,
    "bellpepper": LandUseCategory.vegetables,
    "blueberry": LandUseCategory.fruit_trees,
    "cabbage_red": LandUseCategory.vegetables,
    "cabbage_white": LandUseCategory.vegetables,
        "carrot":LandUseCategory.vegetables,
    "cashew": LandUseCategory.fruit_trees,
    "cassava": LandUseCategory.arable_land,
    "castor_beans": LandUseCategory.fruit_trees,
    "chick_pea": LandUseCategory.arable_land,
    "chilli": LandUseCategory.vegetables,
        "cocoa":LandUseCategory.fruit_trees,
        "coconut":LandUseCategory.fruit_trees,
    "coffee_arabica": LandUseCategory.fruit_trees,
    "coffee_robusta": LandUseCategory.fruit_trees,
    "coriander": LandUseCategory.vegetables,
    "cotton": LandUseCategory.arable_land,
    "cranberry": LandUseCategory.fruit_trees,
    "eggplant": LandUseCategory.vegetables,
    "flax": LandUseCategory.arable_land,
    "ginger": LandUseCategory.vegetables,
    "grape": LandUseCategory.fruit_trees,
    "guar": LandUseCategory.arable_land,
    "hemp": LandUseCategory.arable_land,
    "lemon": LandUseCategory.fruit_trees,
    "citruslime": LandUseCategory.fruit_trees,
    "lentil": LandUseCategory.arable_land,
        "linseed":LandUseCategory.arable_land,
        "maizegrain":LandUseCategory.arable_land,
        "mandarin":LandUseCategory.fruit_trees,
    "mango": LandUseCategory.fruit_trees,
        "mint":LandUseCategory.vegetables,
    "mulberry": LandUseCategory.fruit_trees,
        "oat":LandUseCategory.arable_land,
        "olive":LandUseCategory.fruit_trees,
        "onion":LandUseCategory.vegetables,
    "orange_fresh": LandUseCategory.fruit_trees,
    "orange_processing": LandUseCategory.fruit_trees,
        "palmtree":LandUseCategory.fruit_trees,
        "peach":LandUseCategory.fruit_trees,
        "peanut":LandUseCategory.arable_land,
        "pear":LandUseCategory.fruit_trees,
    "pearl_millet": LandUseCategory.arable_land,
        "pineapple":LandUseCategory.arable_land,
    "pomegranate": LandUseCategory.fruit_trees,
        "potato":LandUseCategory.arable_land,
        "rapeseed":LandUseCategory.arable_land,
    "raspberry": LandUseCategory.fruit_trees,
        "rice":LandUseCategory.arable_land,
    "sesame_seed": LandUseCategory.arable_land,
        "soybean":LandUseCategory.arable_land,
    "strawberry_fresh": LandUseCategory.vegetables,
    "strawberry_processing": LandUseCategory.vegetables,
        "sugarbeet":LandUseCategory.arable_land,
        "sugarcane":LandUseCategory.arable_land,
        "sunflower":LandUseCategory.arable_land,
        "sweetcorn":LandUseCategory.arable_land,
        "tea":LandUseCategory.vegetables,
    "tomato_fresh": LandUseCategory.vegetables,
    "tomato_processing": LandUseCategory.vegetables,
    "turmeric": LandUseCategory.vegetables,
        "wheat":LandUseCategory.arable_land
        }

#Generated in GD_crop OrgFertiliser_L1 using =""""&C$3&""":{LiquidManureType.cattle:"&C5&",  LiquidManureType.pig:"&C6+C7&",  LiquidManureType.laying_hens:"&C8&",  LiquidManureType.other:"&C9&"},"
MANURE_LIQUID_RATIO_PER_COUNTRY={
   "AR":{
      LiquidManureType.cattle:0.966236579156714,
      LiquidManureType.pig:0.00694397589098068,
      LiquidManureType.laying_hens:0.0268194449523053,
      LiquidManureType.other:0
   },
   "AU":{
      LiquidManureType.cattle:0.932419087357062,
      LiquidManureType.pig:0.0539051038187365,
      LiquidManureType.laying_hens:0.013675808824202,
      LiquidManureType.other:0
   },
   "BE":{
      LiquidManureType.cattle:0.651980577390597,
      LiquidManureType.pig:0.33755453080352,
      LiquidManureType.laying_hens:0.0104648918058829,
      LiquidManureType.other:0
   },
   "BR":{
      LiquidManureType.cattle:0.773192504917913,
      LiquidManureType.pig:0.209272715844499,
      LiquidManureType.laying_hens:0.0175347792375884,
      LiquidManureType.other:0
   },
   "CA":{
      LiquidManureType.cattle:0.692978661588794,
      LiquidManureType.pig:0.287387571957475,
      LiquidManureType.laying_hens:0.0196337664537316,
      LiquidManureType.other:0
   },
   "CL":{
      LiquidManureType.cattle:0.671554978323718,
      LiquidManureType.pig:0.313956216577732,
      LiquidManureType.laying_hens:0.0144888050985496,
      LiquidManureType.other:0
   },
   "CN":{
      LiquidManureType.cattle:0.537242763171236,
      LiquidManureType.pig:0.407708581139235,
      LiquidManureType.laying_hens:0.0550486556895287,
      LiquidManureType.other:0
   },
   "CO":{
      LiquidManureType.cattle:0.851488143861912,
      LiquidManureType.pig:0.135951615481044,
      LiquidManureType.laying_hens:0.0125602406570442,
      LiquidManureType.other:0
   },
   "CR":{
      LiquidManureType.cattle:0.895766461352508,
      LiquidManureType.pig:0.0967795210030105,
      LiquidManureType.laying_hens:0.00745401764448142,
      LiquidManureType.other:0
   },
   "CI":{
      LiquidManureType.cattle:0.334403636655568,
      LiquidManureType.pig:0.634734666175069,
      LiquidManureType.laying_hens:0.0308616971693619,
      LiquidManureType.other:0
   },
   "EC":{
      LiquidManureType.cattle:0.827252441996018,
      LiquidManureType.pig:0.164514870836777,
      LiquidManureType.laying_hens:0.0082326871672052,
      LiquidManureType.other:0
   },
   "FI":{
      LiquidManureType.cattle:0.778299855183584,
      LiquidManureType.pig:0.21066782505035,
      LiquidManureType.laying_hens:0.0110323197660669,
      LiquidManureType.other:0
   },
   "FR":{
      LiquidManureType.cattle:0.859989060959847,
      LiquidManureType.pig:0.129061822523649,
      LiquidManureType.laying_hens:0.0109491165165037,
      LiquidManureType.other:0
   },
   "DE":{
      LiquidManureType.cattle:0.713839694570081,
      LiquidManureType.pig:0.2776675583672,
      LiquidManureType.laying_hens:0.0084927470627198,
      LiquidManureType.other:0
   },
   "GH":{
      LiquidManureType.cattle:0.263744005199079,
      LiquidManureType.pig:0.699031130863308,
      LiquidManureType.laying_hens:0.0372248639376124,
      LiquidManureType.other:0
   },
   "HU":{
      LiquidManureType.cattle:0.524511327653383,
      LiquidManureType.pig:0.44007859925733,
      LiquidManureType.laying_hens:0.0354100730892873,
      LiquidManureType.other:0
   },
   "IN":{
      LiquidManureType.cattle:0.956101289109399,
      LiquidManureType.pig:0.0233188441830511,
      LiquidManureType.laying_hens:0.0205798667075499,
      LiquidManureType.other:0
   },
   "ID":{
      LiquidManureType.cattle:0.841953137050475,
      LiquidManureType.pig:0.0935464385871454,
      LiquidManureType.laying_hens:0.0645004243623796,
      LiquidManureType.other:0
   },
   "IL":{
      LiquidManureType.cattle:0.27213220939371,
      LiquidManureType.pig:0.641543269196396,
      LiquidManureType.laying_hens:0.0863245214098939,
      LiquidManureType.other:0
   },
   "IT":{
      LiquidManureType.cattle:0.750511965391496,
      LiquidManureType.pig:0.214944527652967,
      LiquidManureType.laying_hens:0.0345435069555363,
      LiquidManureType.other:0
   },
   "KE":{
      LiquidManureType.cattle:0.897991182476556,
      LiquidManureType.pig:0.0923011873958199,
      LiquidManureType.laying_hens:0.00970763012762398,
      LiquidManureType.other:0
   },
   "MX":{
      LiquidManureType.cattle:0.469470222458186,
      LiquidManureType.pig:0.467383795135426,
      LiquidManureType.laying_hens:0.0631459824063886,
      LiquidManureType.other:0
   },
    "MA": {
        LiquidManureType.cattle: 0.6615,
        LiquidManureType.pig: 0.0079,
        LiquidManureType.laying_hens: 0.3306,
        LiquidManureType.other: 0
    },
   "NL":{
      LiquidManureType.cattle:0.63220650185421,
      LiquidManureType.pig:0.342018951568641,
      LiquidManureType.laying_hens:0.0257745465771489,
      LiquidManureType.other:0
   },
   "NZ":{
      LiquidManureType.cattle:0.979450321664584,
      LiquidManureType.pig:0.0140995427909364,
      LiquidManureType.laying_hens:0.00645013554447995,
      LiquidManureType.other:0
   },
   "PE":{
      LiquidManureType.cattle:0.594188650414037,
      LiquidManureType.pig:0.38368236901601,
      LiquidManureType.laying_hens:0.0221289805699533,
      LiquidManureType.other:0
   },
   "PH":{
      LiquidManureType.cattle:0.436931601829857,
      LiquidManureType.pig:0.489759584546912,
      LiquidManureType.laying_hens:0.0733088136232304,
      LiquidManureType.other:0
   },
   "PL":{
      LiquidManureType.cattle:0.683498764026531,
      LiquidManureType.pig:0.294497161576218,
      LiquidManureType.laying_hens:0.0220040743972504,
      LiquidManureType.other:0
   },
   "RU":{
      LiquidManureType.cattle:0.846999341113014,
      LiquidManureType.pig:0.129000077712947,
      LiquidManureType.laying_hens:0.0240005811740389,
      LiquidManureType.other:0
   },
    "CS": {
        LiquidManureType.cattle: 0.5391,
        LiquidManureType.pig: 0.3769,
        LiquidManureType.laying_hens: 0.0840,
        LiquidManureType.other: 0
    },
   "ZA":{
      LiquidManureType.cattle:0.41919169262082,
      LiquidManureType.pig:0.549851812411446,
      LiquidManureType.laying_hens:0.0309564949677344,
      LiquidManureType.other:0
   },
   "ES":{
      LiquidManureType.cattle:0.507915454115911,
      LiquidManureType.pig:0.471746060350606,
      LiquidManureType.laying_hens:0.0203384855334841,
      LiquidManureType.other:0
   },
   "LK":{
      LiquidManureType.cattle:0.882715893891701,
      LiquidManureType.pig:0.033172429408555,
      LiquidManureType.laying_hens:0.0841116766997438,
      LiquidManureType.other:0
   },
   "CH":{
      LiquidManureType.cattle:0.847633294065572,
      LiquidManureType.pig:0.147390713511541,
      LiquidManureType.laying_hens:0.00497599242288751,
      LiquidManureType.other:0
   },
   "TH":{
      LiquidManureType.cattle:0.755351921445373,
      LiquidManureType.pig:0.196190337682957,
      LiquidManureType.laying_hens:0.0484577408716699,
      LiquidManureType.other:0
   },
   "TR":{
      LiquidManureType.cattle:0.97789519996087,
      LiquidManureType.pig:0.0000210712338866819,
      LiquidManureType.laying_hens:0.0220837288052437,
      LiquidManureType.other:0
   },
   "UA":{
      LiquidManureType.cattle:0.741443874469408,
      LiquidManureType.pig:0.206193115577965,
      LiquidManureType.laying_hens:0.0523630099526263,
      LiquidManureType.other:0
   },
   "US":{
      LiquidManureType.cattle:0.766419201590052,
      LiquidManureType.pig:0.200025658106077,
      LiquidManureType.laying_hens:0.0335551403038707,
      LiquidManureType.other:0
   },
   "VN":{
      LiquidManureType.cattle:0.474349921379399,
      LiquidManureType.pig:0.495364975254196,
      LiquidManureType.laying_hens:0.0302851033664051,
      LiquidManureType.other:0
   }
}

#Generated in GD_crop OrgFertiliser_L1 using =""""&C$3&""":{SolidManureType.cattle:"&C12&",  SolidManureType.pigs:"&C13&",  SolidManureType.sheep_goats:"&C14&",  SolidManureType.laying_hen_litter:"&C15&",  SolidManureType.broiler_litter:"&C16&",  SolidManureType.horses:0"&",  SolidManureType.other:"&C17+C18&"},"
MANURE_SOLID_RATIO_PER_COUNTRY = {
   "AR":{
      SolidManureType.cattle:0.891984968037592,
      SolidManureType.pigs:0.00428250486383302,
      SolidManureType.sheep_goats:0.00785192210275657,
      SolidManureType.laying_hen_litter:0.0587269859794054,
      SolidManureType.horses:0,
      SolidManureType.other:0.0154080727192603
   },
   "AU":{
      SolidManureType.cattle:0.866230714363227,
      SolidManureType.pigs:0.0396558670056438,
      SolidManureType.sheep_goats:0,
      SolidManureType.laying_hen_litter:0.0842828110565378,
      SolidManureType.horses:0,
      SolidManureType.other:0.00983060757459108
   },
   "BE":{
      SolidManureType.cattle:0.680918401872099,
      SolidManureType.pigs:0.280055070828466,
      SolidManureType.sheep_goats:0.00287090731445683,
      SolidManureType.laying_hen_litter:0.0336298155034748,
      SolidManureType.horses:0,
      SolidManureType.other:0.00182107880156133
   },
   "BR":{
      SolidManureType.cattle:0.747215795807973,
      SolidManureType.pigs:0.170711134549261,
      SolidManureType.sheep_goats:0.00150204832846079,
      SolidManureType.laying_hen_litter:0.066481712553207,
      SolidManureType.horses:0,
      SolidManureType.other:0.0106371188335423
   },
   "CA":{
      SolidManureType.cattle:0.642672694527304,
      SolidManureType.pigs:0.21456568114916,
      SolidManureType.sheep_goats:0.00589291129178607,
      SolidManureType.laying_hen_litter:0.101590444813062,
      SolidManureType.horses:0,
      SolidManureType.other:0.0233093573163688
   },
   "CL":{
      SolidManureType.cattle:0.552250451631966,
      SolidManureType.pigs:0.217928697517175,
      SolidManureType.sheep_goats:0.00217715952451313,
      SolidManureType.laying_hen_litter:0.0438606686453432,
      SolidManureType.horses:0,
      SolidManureType.other:0.180852077242765
   },
   "CN":{
      SolidManureType.cattle:0.362384649367369,
      SolidManureType.pigs:0.230730522410369,
      SolidManureType.sheep_goats:0.14772992931581,
      SolidManureType.laying_hen_litter:0.0676886805955466,
      SolidManureType.horses:0,
      SolidManureType.other:0.183306047927011
   },
   "CO":{
      SolidManureType.cattle:0.838197032202166,
      SolidManureType.pigs:0.112964690235755,
      SolidManureType.sheep_goats:0.00133593378235541,
      SolidManureType.laying_hen_litter:0.0427314752873547,
      SolidManureType.horses:0,
      SolidManureType.other:0
   },
   "CR":{
      SolidManureType.cattle:0.86703206910812,
      SolidManureType.pigs:0.0790705320551174,
      SolidManureType.sheep_goats:0.0000342803689755446,
      SolidManureType.laying_hen_litter:0.0510683786509679,
      SolidManureType.horses:0,
      SolidManureType.other:0
   },
   "CI":{
      SolidManureType.cattle:0.30319915656893,
      SolidManureType.pigs:0.485781032504727,
      SolidManureType.sheep_goats:0.0773942195973608,
      SolidManureType.laying_hen_litter:0.133625591328983,
      SolidManureType.horses:0,
      SolidManureType.other:0
   },
   "EC":{
      SolidManureType.cattle:0.732791342645394,
      SolidManureType.pigs:0.123009389316786,
      SolidManureType.sheep_goats:0.000401295431772118,
      SolidManureType.laying_hen_litter:0.136401211063513,
      SolidManureType.horses:0,
      SolidManureType.other:0.00260223066010027
   },
   "FI":{
      SolidManureType.cattle:0.796050906155418,
      SolidManureType.pigs:0.171171394598401,
      SolidManureType.sheep_goats:0.00813728584106536,
      SolidManureType.laying_hen_litter:0.0154009489950553,
      SolidManureType.horses:0,
      SolidManureType.other:0.0050773244121249
   },
   "FR":{
      SolidManureType.cattle:0.817006208590229,
      SolidManureType.pigs:0.0974023218136786,
      SolidManureType.sheep_goats:0.028576974423064,
      SolidManureType.laying_hen_litter:0.0228714023639015,
      SolidManureType.horses:0,
      SolidManureType.other:0.0328108856640718
   },
   "DE":{
      SolidManureType.cattle:0.727786900832796,
      SolidManureType.pigs:0.224888769346684,
      SolidManureType.sheep_goats:0.00877737537493331,
      SolidManureType.laying_hen_litter:0.0217845836784869,
      SolidManureType.horses:0,
      SolidManureType.other:0.0149340704445282
   },
   "GH":{
      SolidManureType.cattle:0.229471343581357,
      SolidManureType.pigs:0.513373819312835,
      SolidManureType.sheep_goats:0.154434937260582,
      SolidManureType.laying_hen_litter:0.102091955498911,
      SolidManureType.horses:0,
      SolidManureType.other:0
   },
   "HU":{
      SolidManureType.cattle:0.43790738862665,
      SolidManureType.pigs:0.293028837016495,
      SolidManureType.sheep_goats:0.130362255346065,
      SolidManureType.laying_hen_litter:0.0661592669305374,
      SolidManureType.horses:0,
      SolidManureType.other:0.0661343707038014
   },
   "IN":{
      SolidManureType.cattle:0.25834922642825,
      SolidManureType.pigs:0.0052864383650807,
      SolidManureType.sheep_goats:0.0981507817052525,
      SolidManureType.laying_hen_litter:0.0144465747636179,
      SolidManureType.horses:0,
      SolidManureType.other:0.623106249383288
   },
   "ID":{
      SolidManureType.cattle:0.467197539586431,
      SolidManureType.pigs:0.0435507726372292,
      SolidManureType.sheep_goats:0.119821943999018,
      SolidManureType.laying_hen_litter:0.220295369162569,
      SolidManureType.horses:0,
      SolidManureType.other:0.145861038464536
   },
   "IL":{
      SolidManureType.cattle:0.199236580122689,
      SolidManureType.pigs:0.39646666414798,
      SolidManureType.sheep_goats:0,
      SolidManureType.laying_hen_litter:0.259146837443465,
      SolidManureType.horses:0,
      SolidManureType.other:0.145149918285867
   },
   "IT":{
      SolidManureType.cattle:0.623557125987676,
      SolidManureType.pigs:0.141867888486309,
      SolidManureType.sheep_goats:0.0623664331281349,
      SolidManureType.laying_hen_litter:0.0461048852989332,
      SolidManureType.horses:0,
      SolidManureType.other:0.123983045058037
   },
   "KE":{
      SolidManureType.cattle:0.716502772802802,
      SolidManureType.pigs:0.0621647840759193,
      SolidManureType.sheep_goats:0.159458408168703,
      SolidManureType.laying_hen_litter:0.0124634802549919,
      SolidManureType.horses:0,
      SolidManureType.other:0.0493881369381422
   },
   "MX":{
      SolidManureType.cattle:0.437879115151199,
      SolidManureType.pigs:0.367968515803388,
      SolidManureType.sheep_goats:0.00791315611290666,
      SolidManureType.laying_hen_litter:0.144748167445137,
      SolidManureType.horses:0,
      SolidManureType.other:0.0139241223195238
   },
    "MA": {
        SolidManureType.cattle: 0.1740,
        SolidManureType.pigs: 0.0021,
        SolidManureType.sheep_goats: 0.7369,
        SolidManureType.laying_hen_litter: 0.087,
        SolidManureType.horses: 0.0,
        SolidManureType.other: 0.0
    },
   "NL":{
      SolidManureType.cattle:0.650340967131297,
      SolidManureType.pigs:0.279493306740428,
      SolidManureType.sheep_goats:0.0140888719565466,
      SolidManureType.laying_hen_litter:0.0503111762710478,
      SolidManureType.horses:0,
      SolidManureType.other:0.00440480042111328
   },
   "NZ":{
      SolidManureType.cattle:0.963421730440515,
      SolidManureType.pigs:0.0109823225235529,
      SolidManureType.sheep_goats:0,
      SolidManureType.laying_hen_litter:0.0238938933876232,
      SolidManureType.horses:0,
      SolidManureType.other:0.00170205364830849
   },
   "PE":{
      SolidManureType.cattle:0.496720484396516,
      SolidManureType.pigs:0.270738732154887,
      SolidManureType.sheep_goats:0.00617767908700828,
      SolidManureType.laying_hen_litter:0.138445339042684,
      SolidManureType.horses:0,
      SolidManureType.other:0.0754721922606031
   },
   "PH":{
      SolidManureType.cattle:0.181039090379967,
      SolidManureType.pigs:0.170254196102749,
      SolidManureType.sheep_goats:0.0236394474661915,
      SolidManureType.laying_hen_litter:0.0556849945310376,
      SolidManureType.horses:0,
      SolidManureType.other:0.565015879482784
   },
   "PL":{
      SolidManureType.cattle:0.682243198492267,
      SolidManureType.pigs:0.234441939364468,
      SolidManureType.sheep_goats:0.0062009560207519,
      SolidManureType.laying_hen_litter:0.0471719484860473,
      SolidManureType.horses:0,
      SolidManureType.other:0.0250107466216499
   },
   "RU":{
      SolidManureType.cattle:0.713799208422998,
      SolidManureType.pigs:0.086703308957753,
      SolidManureType.sheep_goats:0.125362195508399,
      SolidManureType.laying_hen_litter:0.0459795592019804,
      SolidManureType.horses:0,
      SolidManureType.other:0.0206964990993778
   },
    "CS": {
        SolidManureType.cattle: 0.4517,
        SolidManureType.pigs: 0.3157,
        SolidManureType.sheep_goats: 0.1623,
        SolidManureType.laying_hen_litter: 0.0703,
        SolidManureType.horses: 0.0,
        SolidManureType.other: 0.0
    },
   "ZA":{
      SolidManureType.cattle:0.356625251567831,
      SolidManureType.pigs:0.394853891860788,
      SolidManureType.sheep_goats:0.132864576090439,
      SolidManureType.laying_hen_litter:0.106933665101149,
      SolidManureType.horses:0,
      SolidManureType.other:0.00236287438764808
   },
   "ES":{
      SolidManureType.cattle:0.474296687896011,
      SolidManureType.pigs:0.349950028157995,
      SolidManureType.sheep_goats:0.12997128300961,
      SolidManureType.laying_hen_litter:0.0422583249187088,
      SolidManureType.horses:0,
      SolidManureType.other:0.00150157348727131
   },
   "LK":{
      SolidManureType.cattle:0.358031210049245,
      SolidManureType.pigs:0.0112883407239895,
      SolidManureType.sheep_goats:0.0270469208521131,
      SolidManureType.laying_hen_litter:0.0561358733095111,
      SolidManureType.horses:0,
      SolidManureType.other:0.547187751890528
   },
   "CH":{
      SolidManureType.cattle:0.847661071767102,
      SolidManureType.pigs:0.117090979573841,
      SolidManureType.sheep_goats:0.0171437568569013,
      SolidManureType.laying_hen_litter:0.0153716911193726,
      SolidManureType.horses:0,
      SolidManureType.other:0.000565871544344061
   },
   "TH":{
      SolidManureType.cattle:0.483365490034822,
      SolidManureType.pigs:0.105331894540662,
      SolidManureType.sheep_goats:0.00325053153676041,
      SolidManureType.laying_hen_litter:0.086165099964401,
      SolidManureType.horses:0,
      SolidManureType.other:0.321772314596681
   },
   "TR":{
      SolidManureType.cattle:0.715196837161228,
      SolidManureType.pigs:0.0000129294244842317,
      SolidManureType.sheep_goats:0.223468643242192,
      SolidManureType.laying_hen_litter:0.0457627044658414,
      SolidManureType.horses:0,
      SolidManureType.other:0.0123703169532276
   },
   "UA":{
      SolidManureType.cattle:0.698618141080016,
      SolidManureType.pigs:0.154948882686506,
      SolidManureType.sheep_goats:0.0332941900836932,
      SolidManureType.laying_hen_litter:0.0839576794763046,
      SolidManureType.horses:0,
      SolidManureType.other:0.0194023377379171
   },
   "US":{
      SolidManureType.cattle:0.582965251842265,
      SolidManureType.pigs:0.122485390244081,
      SolidManureType.sheep_goats:0.00534999988371993,
      SolidManureType.laying_hen_litter:0.150308182514656,
      SolidManureType.horses:0,
      SolidManureType.other:0.105902046051912
   },
   "VN":{
      SolidManureType.cattle:0.289461071985541,
      SolidManureType.pigs:0.253613640613564,
      SolidManureType.sheep_goats:0.00536369937026225,
      SolidManureType.laying_hen_litter:0.053200369466612,
      SolidManureType.horses:0,
      SolidManureType.other:0.397191100774241
   }
}

#from GD_crop RootingDepth_L0 and RootingDepth_L1
# Mireille&Raphaël for Bell pepper, cabbage, cassava, cotton, eggplant, flax, guar, hemp, lentil, mango, mulberry
# Chloé's file for cashew, chilli, coffee, grape, peanut, potato, pineapple, strawberry, sugar beet, sugar cane,
# tea, tomato, wheat
# Castor bean: (Comar, Tilley et al. 2004)
# Chickpea: ecocrop (FAO)
# Coriander: http://veggieharvest.com/herbs/cilantro.html // http://files.hawaii.gov/dlnr/cwrm/publishedreports/PR200808.pdf
# Ginger: http://veggieharvest.com/herbs/ginger.html
# Millet: ask Sämi
# Sesame seed: ask Sämi
# Turmenic: ask Sämi
# Pomegranate: ask Sämi
#in m
ROOTING_DEPTH_PER_CROP = {
                        "almond": 1.5,
                        "apple": 1.5,
                        "apricot": 1.5,
    "asparagus_green": 0.5,
    "asparagus_white": 0.5,
                        "banana": 1.5,
    "bellpepper": 0.6,
    "blueberry": 0.45,
    "cabbage_red": 0.25,
    "cabbage_white": 0.25,
                        "carrot": 0.5,
    "cashew": 0.5,
    "cassava": 1.5,
    "castor_beans": 1.5,
    "chick_pea": 1.5,
    "chilli": 0.8,
                        "cocoa": 2.0,
                        "coconut": 1.5,
    "coffee_arabica": 1.2,
    "coffee_robusta": 1.2,
    "coriander": 0.33,
    "cotton": 1.35,
    "cranberry": 0.9,
    "eggplant": 0.8,
    "flax": 0.5,
    "ginger": 0.275,
    "grape": 1.5,
    "guar": 0.5,
    "hemp": 0.5,
    "lemon": 1.5,
    "citruslime": 1.5,
    "lentil": 0.5,
                        "linseed": 0.9,
                        "maizegrain": 1.35,
                        "mandarin": 1.5,
    "mango": 1,
                        "mint": 0.5,
    "mulberry": 1,
                        "oat": 1.2,
                        "olive": 1.5,
                        "onion": 0.5,
    "orange_fresh": 1.5,
    "orange_processing": 1.5,
                        "palmtree": 1,
                        "peach": 1.5,
    "peanut": 0.5,
                        "pear": 1.5,
    "pearl_millet": 1.5,
                        "pineapple": 0.5,
    "pomegranate": 1.0,
    "potato": 0.3,
                        "rapeseed": 0.9,
    "raspberry": 0.9,
                        "rice": 0.6,
    "sesame_seed": 0.6,
                        "soybean": 0.95,
    "strawberry_fresh": 0.45,
    "strawberry_processing": 0.45,
    "sugarbeet": 0.9,
    "sugarcane": 1.5,
                        "sunflower": 1.35,
                        "sweetcorn": 1.35,
    "tea": 1.2,
    "tomato_fresh": 1.0,
    "tomato_processing": 1.0,
    "turmeric": 0.45,
    "wheat": 0.7
}

#from GD_crop SoilTypes_L1, line 6
SAND_CONTENT_PER_COUNTRY = {
                       "AR":0.040180143913853,
                       "AU":0.253381946701333,
                       "BE":0.0200364298724954,
                       "BR":0.0428501228501229,
                       "CA":0.0100422280913798,
                       "CL":0.0180752320468979,
                       "CN":0.0885942240701202,
                       "CO":0.0813253012048193,
                       "CR":0,
                       "CI":0.0149692595562684,
                       "EC":0.00570469798657718,
                       "FI":0,
                       "FR":0.00947032265169034,
                       "DE":0.0165961601041328,
                       "GH":0.00520252694165738,
                       "HU":0.0843688685415304,
                       "IN":0.0174722863091554,
                       "ID":0.0477489768076398,
                       "IL":0,
                       "IT":0,
                       "KE":0.0551962701158069,
                       "MX":0,
    "MA": 0.1237,
                       "NL":0,
                       "NZ":0.00861856685545432,
                       "PE":0.0285601474072124,
                       "PH":0.0111714975845411,
                       "PL":0.0572775058908827,
                       "RU":0.00505958625598585,
    "CS": 0.296,
                       "ZA":0.146219421793921,
                       "ES":0.00948241801659423,
                       "LK":0.0235294117647059,
                       "CH":0,
                       "TH":0.0037108744756373,
                       "TR":0.00243076655959719,
                       "UA":0.00950717889018238,
                       "US":0.0167799421157036,
                       "VN":0.0109721867823424
}

#from GD_crop HumusCcontent_L1
SOIL_CARBON_CONTENT_PER_COUNTRY = {
                            "AR":0.0148,
                            "AU":0.0063,
                            "BE":0.0132,
                            "BR":0.0121,
                            "CA":0.0428,
                            "CL":0.0223,
                            "CN":0.0229, #mean of other values
                            "CO":0.0382,
                            "CR":0.033,
                            "CI":0.0089,
                            "EC":0.0212,
                            "FI":0.1103,
                            "FR":0.0142,
                            "DE":0.0301,
                            "GH":0.0088,
                            "HU":0.0239,
                            "IN":0.0088,
                            "ID":0.0521,
                            "IL":0.0096,
                            "IT":0.011,
                            "KE":0.009,
                            "MX":0.0301,
    "MA": 0.0229,  # mean of other values
                            "NL":0.0637,
                            "NZ":0.0185,
                            "PE":0.0163,
                            "PH":0.0128,
                            "PL":0.034,
                            "RU":0.0389,
    "CS": 0.0229,  # mean of other values
                            "ZA":0.0058,
                            "ES":0.0125,
                            "LK":0.0088,
                            "CH":0.0209,
                            "TH":0.0101,
                            "TR":0.0098,
                            "UA":0.0233,
                            "US":0.0152,
                            "VN":0.0126
}

#src except unknown: EUROPEAN COMMISSION DIRECTORATE GENERAL JRC JOINT RESEARCH CENTRE Space Applications Institute European Soil Bureau
SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE = {
                        SoilTexture.unknown:0.032,#Panagos et al. 2014
                        SoilTexture.coarse:0.0115,
                        SoilTexture.medium:0.0311,
                        SoilTexture.medium_fine:0.0438,
                        SoilTexture.fine:0.0339,
                        SoilTexture.very_fine:0.017
                        }

#from GD_crop Soil_pH_L0
SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY = {
                       "AR":0,
                       "AU":0.4,
                       "BE":0.8,
                       "BR":0.95,
                       "CA":0.9,
                       "CL":0.5,
                       "CN":0.35,
                       "CO":0.95,
                       "CR":1,
                       "CI":1,
                       "EC":0.95,
                       "FI":1,
                       "FR":0.8,
                       "DE":0.8,
                       "GH":0.95,
                       "HU":0.8,
                       "IN":0.5,
                       "ID":1,
                       "IL":0,
                       "IT":0.8,
                       "KE":0.5,
                       "MX":0.33,
    "MA": 0.0,
                       "NL":0.8,
                       "NZ":0.95,
                       "PE":0.8,
                       "PH":1,
                       "PL":0.8,
                       "RU":0.9,
    "CS": 0.8,
                       "ZA":0.2,
                       "ES":0.6,
                       "LK":0.8,
                       "CH":0.8,
                       "TH":0.95,
                       "TR":0.33,
                       "UA":0.95,
                       "US":0.5,
                       "VN":1
                    }

#From GD_crop WaterNutrient_L1 column C
#  Mireille&Raphaël for Bell pepper, cabbage, cashew, cassava, chilli, cotton, eggplant, flax, grape, guar, hemp, lentil, mango, mulberry
# Castor bean:pdf  Castor_Bean_Moisture in documentation file;http://www.cropj.com/gharibzahedi_5_1_2011_1_7.pdf
# Chickpea: http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.548.9690&rep=rep1&type=pdf (leaf water content, averaged from graph p.37): http://etd.aau.edu.et/bitstream/123456789/10830/1/Getahun%20Yemata.pdf
# Coriander: http://www.academicjournals.org/article/article1390549943_Bhat%2520et%2520al.pdf
# Ginger: http://www.fao.org/fileadmin/user_upload/inpho/docs/Post_Harvest_Compendium_-_Ginger.pdf
# Millet: ask Sämi / Pauline: http://agropedia.iitk.ac.in/content/harvesting-and-storage-pearl-millet
# Sesame seed: ask Sämi / Pauline:http://www.globalsciencebooks.info/Online/GSBOnline/images/2010/SSB_4(1)/SSB_4(1)69-72o.pdf
# Turmenic: ask Sämi / Pauline: http://www.fao.org/3/a-ax446e.pdf
# Pomegranate: ask Sämi / Pauline: http://www.ijat-aatsea.com/pdf/v7_n6_11_November/6_IJAT_2011_7_6___R._Riyahi_FX.pdf
WATER_CONTENT_FM_RATIO_PER_CROP = {
        "almond": 0.0565,
        "apple": 0.849,
        "apricot": 0.853,
    "asparagus_green": 0.92,
    "asparagus_white": 0.92,
        "banana": 0.781,
    "bellpepper": 0.88,
    "blueberry": 0.8421,
    "cabbage_red": 0.9,
    "cabbage_white": 0.9,
        "carrot": 0.882,
    "cashew": 0.05,
    "cassava": 0.6,
    "castor_beans": 0.094,
    "chick_pea": 0.09,
    "chilli": 0.88,
        "cocoa": 0.056,
        "coconut": 0.446,
    "coffee_arabica": 0.102,
    "coffee_robusta": 0.102,
    "coriander": 0.0808,
    "cotton": 0.09,
    "cranberry": 0.8732,
    "eggplant": 0.93,
    "flax": 0.11,
    "ginger": 0.12,
    "grape": 0.81,
    "guar": 0.1,
    "hemp": 0.4,
    "lemon": 0.842,
    "citruslime": 0.842,
    "lentil": 0.08,
        "linseed": 0.1,
        "maizegrain": 0.14,
        "mandarin": 0.842,
    "mango": 0.84,
        "mint": 0.681,
    "mulberry": 0.7,
        "oat": 0.15,
        "olive": 0.748,
        "onion": 0.886,
    "orange_fresh": 0.842,
    "orange_processing": 0.842,
        "palmtree": 0.47,
        "peach": 0.873,
        "peanut": 0.05968,
        "pear": 0.829,
    "pearl_millet": 0.2,
        "pineapple": 0.87,#src: web
    "pomegranate": 0.78,
        "potato": 0.78,
        "rapeseed": 0.12,
    "raspberry": 0.8575,
        "rice": 0.131,
    "sesame_seed": 0.057,
        "soybean": 0.11,
    "strawberry_fresh": 0.895,
    "strawberry_processing": 0.895,
        "sugarbeet": 0.77,
        "sugarcane": 0.774,
        "sunflower": 0.06,
        "sweetcorn": 0.72,
        "tea": 0.0764,
    "tomato_fresh": 0.942,
    "tomato_processing": 0.942,
    "turmeric": 0.12,
        "wheat": 0.15
        }

#from GD_crop precipitation_L1 line 17
YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY = {
   "AR":0,
   "AU":0,
   "BE":0,
   "BR":0,
   "CA":0.535441893912093,
   "CL":0,
   "CN":0.0932626571867323,
   "CO":0,
   "CR":0,
   "CI":0,
   "EC":0,
   "FI":0.31411007733821,
   "FR":0,
   "DE":0.0717855087687475,
   "GH":0,
   "HU":0.0603055148410166,
   "IN":0,
   "ID":0,
   "IL":0,
   "IT":0,
   "KE":0,
   "MX":0,
    "MA": 0,
   "NL":0,
   "NZ":0,
   "PE":0,
   "PH":0,
   "PL":0.168512374426543,
   "RU":0.399109339441838,
    "CS": 0.073,
   "ZA":0,
   "ES":0,
   "LK":0,
   "CH":0.215816922864692,
   "TH":0,
   "TR":0.125603689935222,
   "UA":0.217717386416183,
   "US":0.20931054440831,
   "VN":0
}
