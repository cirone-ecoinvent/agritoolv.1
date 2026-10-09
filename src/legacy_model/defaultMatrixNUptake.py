
#from GD_crop Nuptake_L1
# country: =SI(ESTNUM(B4),""""&B$3&""":"&B4&",","")
#glo: =MOYENNE(B4:AM4)
# kg/ha
NITROGEN_UPTAKE_PER_CROP_PER_COUNTRY = {
   "almond":{
      "CN":78.1224116559,
      "US":87.3459815169,
      "GLO":82.7341965864
   },
   "apple":{
      "CL":40.2640395,
      "CN":26.99167375,
      "IT":38.18634975,
      "US":34.183586375,
      "GLO":34.90641234375
   },
   "apricot":{
      "FR":35.7159625,
      "IT":36.5128915,
      "ES":25.73099415,
      "TR":34.06197415,
      "GLO":33.005455575
   },
    "asparagus_green": {
        "CN": 32.71717158668,
        "FR": 25.68640244716,
        "PE": 68.99638897312,
        "GLO": 42.4666543356533
    },
    "asparagus_white": {
        "CN": 32.71717158668,
        "FR": 25.68640244716,
        "PE": 68.99638897312,
        "GLO": 42.4666543356533
    },
   "banana":{
      "CO":52.83253974144,
      "CR":96.47326369392,
      "EC":72.67488532896,
      "IN":70.84038114048,
      "GLO":73.2052674762
   },
   "bellpepper": {
      "IN": 150.0,
      "GLO": 150.0
   },
    "blueberry": {
        "CA": 5.26649866,
        "US": 11.3787048,
        "GLO": 8.32260173
    },
    "cabbage_red": {
      "IN": 247.0,
      "GLO": 247.0
   },
    "cabbage_white": {
        "IN": 247.0,
        "GLO": 247.0
    },
   "carrot":{
      "CN":127.499931365653,
      "IL":235.28964621637,
      "NL":208.007116674627,
      "GLO":190.265564752217
   },
   "cashew": {
      "IN": 100.0,
      "GLO": 100.0
   },
   "cassava": {
      "IN": 100.0,
      "GLO": 100.0
   },
    "castor_beans": {  # src: http://ecocrop.fao.org/ecocrop/srv/en/cropView?id=1866
        "GLO": 30.0
    },
    "chick_pea": {  # src: http://www.phytojournal.com/archives/2017/vol6issue1/PartF/6-1-71-853.pdf
        # Pae 395, table 2, line "control"
        "IN": 36.95,
        "GLO": 36.95,
    },
   "chilli": {
      "IN": 150.0,
      "GLO": 150.0
   },
   "cocoa":{
      "CI":29.549965219908,
      "GH":26.753456482116,
      "ID":27.409084681848,
      "GLO":27.904168794624
   },
   "coconut":{
      "IN":61.91392770746,
      "ID":68.2422362331,
      "PH":54.43853729502,
      "GLO":61.5315670785267
   },
    "coffee_arabica": {
      "BR":38.3095135438293,
      "ID":26.6116889445975,
      "VN":52.2567319724059,
      "GLO":39.0593114869442
   },
    "coffee_robusta": {
        "BR": 38.3095135438293,
        "ID": 26.6116889445975,
        "VN": 52.2567319724059,
        "GLO": 39.0593114869442
    },
    "coriander": {  # src: Pdf : Coriander_1 in Documentation file
        "IN": 54.9,
        "GLO": 54.9
    },
   "cotton": {
      "IN": 41.04,
      "GLO": 41.04
   },
    "cranberry": {
        "CL": 11.17043,
        "US": 36.0372579,
        "GLO": 23.60384395
    },
   "eggplant": {
      "IN": 180.0,
      "GLO": 180.0
   },
   "flax": {
      "CN": 25.0,
      "FR": 20.0,
      "GLO": 25.0
   },
    "ginger": {  # src: http://www.researchjournal.co.in/upload/assignments/6_28-30-7.pdf
        "IN": 92.26,
        "GLO": 92.26
    },
    "grape": {
      "IN": 30.0,
      "GLO": 30.0
   },
   "guar": {
      "IN": 45.0,
      "GLO": 45.0
   },
   "hemp": {
      "CN": 100.0,
      "GLO": 100.0
   },
    "lemon": {
      "MX":41.2479101056,
      "ES":45.7209038516,
      "TR":79.5207612988,
      "GLO":55.4965250853333
   },
    "citruslime": {
        "MX": 41.2479101056,
        "ES": 45.7209038516,
        "TR": 79.5207612988,
        "GLO": 55.4965250853333
    },
   "lentil": {
      "IN": 0.0,
      "GLO": 0.0
   },
   "linseed":{
      "CA":83.636946,
      "RU":87.403911,
      "GLO":85.5204285
   },
   "maizegrain":{
      "AR":134.169425339474,
      "GLO":134.169425339474
   },
   "mandarin":{
      "CN":31.8874438996,
      "ES":46.6502755884,
      "GLO":39.268859744
   },
   "mango": {
      "IN": 120.0,
      "GLO": 120.0
   },
   "mint":{#NOTE: IT assumption based on WFLDB 3 applied N
      "IN": 160.0,
      "US": 294.0,
      "GLO": 227.0
   },
   "mulberry": {
      "CN": 400.0,
      "IN": 400.0,
      "GLO": 400.0
   },
   "oat":{
      "CA":62.0985962727273,
      "FI":72.8517035454545,
      "GLO":67.4751499090909
   },
   "olive":{
      "IT":30.98532942872,
      "ES":30.39879281632,
      "GLO":30.69206112252
   },
   "onion":{
      "CN":75.923349955,
      "NL":54.059539175,
      "NZ":97.03050072,
      "GLO":75.67112995
   },
    "orange_fresh": {
      "BR":57.4817377208,
      "ZA":75.6243849188,
      "ES":49.4900887464,
      "US":69.6466147516,
      "GLO":63.0607065344
   },
    "orange_processing": {
        "BR": 57.4817377208,
        "ZA": 75.6243849188,
        "ES": 49.4900887464,
        "US": 69.6466147516,
        "GLO": 63.0607065344
    },
   "palmtree":{
      "ID":100.941465,
      "GLO":100.941465
   },
   "peach":{
      "CN":36.5395203,
      "IT":40.5097098,
      "ES":37.5038643,
      "GLO":38.1843648
   },
   "peanut":{
      "AR":188.25691582992,
      "CN":260.54820030624,
      "IN":91.8405720288,
      "GLO":180.21522938832
   },
   "pear":{
      "AR":39.5896568,
      "BE":45.3603098,
      "CN":29.7466444,
       "GLO": 38.2322036666667
   },
    "pearl_millet": {
        # Canada: pdf Millet_1 in Documentation file
        # India: http://krishikosh.egranth.ac.in/bitstream/1/35296/1/agronomy%202.pdf
        # Nigeria: pdf Millet_2 in Documentation file
        "IN": 84.315,
        "GLO": 59.6575
    },
    "pineapple": {
    },
    "pomegranate": {  # src: Pomegranate_1 pdf in Documentation file
        "GLO": 87.0
    },
   "potato":{
      "CN":56.2998042722222,
      "IN":77.1066293055555,
      "RU":47.6033150777778,
      "UA":54.4075200666667,
      "US":161.412378188889,
      "GLO":79.3659293822222
   },
   "rapeseed":{
      "CA":74.08278955,
      "GLO":74.08278955
   },
    "raspberry": {
        "CS": 9.008745673,
        "RU": 10.25305402,
        "US": 17.59920378,
        "GLO": 12.287001158
    },
   "rice":{
      "CN":124.39576463864,
      "IN":64.53203313212,
      "GLO":94.46389888538
   },
    "sesame_seed": {
        # src: https://www.researchgate.net/publication/265976147_RESPONSE_OF_NITROGEN_LEVELS_ON_YIELD_OF_SESAME_Sesamum_indicum_L
        "IN": 35.0,
        "GLO": 35.0
    },
   "soybean":{
      "AR":229.0021075,
      "GLO":229.0021075
   },
    "strawberry_fresh": {
      "ES":59.525506575,
      "CH":27.68312549,
      "US":89.11134746,
       "MA": 67.45745777,
       "MX": 63.57942609,
      "GLO":58.7733265083333
   },
    "strawberry_processing": {
        "ES": 59.525506575,
        "CH": 27.68312549,
        "US": 89.11134746,
        "MA": 67.45745777,
        "MX": 63.57942609,
        "GLO": 58.7733265083333
    },
   "sugarbeet":{
      "FR":306.4666007,
      "DE":233.8137721,
      "RU":116.0003976,
      "US":203.34608905,
      "GLO":214.9067148625
   },
   "sugarcane":{
      "IN":121.049343369984,
      "GLO":121.049343369984
   },
   "sunflower":{
      "FR":118.65142575,
      "HU":108.823732875,
      "RU":58.811828625,
      "UA":80.470269,
      "GLO":91.6893140625
   },
   "sweetcorn":{
      "HU":45.464463198,
      "TH":33.307381569,
      "US":71.865095907,
      "GLO":50.212313558
   },
   "tea":{
      "CN":62.2732571,
      "KE":102.60123875,
      "LK":77.224432625,
      "GLO":80.699642825
   },
    "tomato_fresh": {
      "IT":116.45748305354,
      "MX":64.59263010414,
      "NL":1025.3085686322,
      "ES":162.08163536506,
      "CH":398.38761154694,
      "GLO":353.365585740376
   },
    "tomato_processing": {
        "IT": 116.45748305354,
        "MX": 64.59263010414,
        "NL": 1025.3085686322,
        "ES": 162.08163536506,
        "CH": 398.38761154694,
        "GLO": 353.365585740376
    },
    "turmeric": {
        # src: https://www.researchgate.net/profile/Bijan_Majumdar/publication/236969066_Effect_of_nitrogen_and_farmyard_manure_on_yield_and_nutrient_uptake_of_turmeric_and_different_forms_of_inorganic_N_build_up_in_an_acidic_Alfisol_of_Meghalaya/links/0c96051a83ee37dd9e000000.pdf
        "IN": 42.5,
        "GLO": 42.5
    },
   "wheat":{
      "AU":44.0064062958333,
      "CA":68.0685096666667,
      "GLO":56.03745798125
   }
}