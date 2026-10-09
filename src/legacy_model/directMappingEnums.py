from enum import Enum




class Plantprotection(Enum):
    spraying="plantprotection_spraying"
    flaming="plantprotection_flaming"
    other="plantprotection_other"

class Soilcultivation(Enum):
    decompactation="soilcultivation_decompactation"
    tillage_chisel="soilcultivation_tillage_chisel"
    tillage_spring_tine_weeder="soilcultivation_tillage_spring_tine_weeder"
    tillage_rotary_harrow="soilcultivation_tillage_rotary_harrow"
    tillage_sprint_tine_harrow="soilcultivation_tillage_sprint_tine_harrow"
    tillage_hoeing_earthing_up="soilcultivation_tillage_hoeing_earthing_up"
    tillage_plough="soilcultivation_tillage_plough"
    tillage_roll="soilcultivation_tillage_roll"
    tillage_rotary_cultivator="soilcultivation_tillage_rotary_cultivator"
    other="soilcultivation_other"

class Sowingplanting(Enum):
    sowing="sowingplanting_sowing"
    planting_seedlings="sowingplanting_planting_seedlings"
    planting_potatoes="sowingplanting_planting_potatoes"
    other="sowingplanting_other"

class Fertilisation(Enum):
    fertilizing_broadcaster="fertilisation_fertilizing_broadcaster"
    liquid_manure_vacuum_tanker="fertilisation_liquid_manure_vacuum_tanker"
    solid_manure="fertilisation_solid_manure"
    other="fertilisation_other"

class Harvesting(Enum):
    chopping_maize="harvesting_chopping_maize"
    threshing_combine_harvester="harvesting_threshing_combine_harvester"
    picking_up_forage_self_propelled_loader="harvesting_picking_up_forage_self_propelled_loader"
    beets_complete_havester="harvesting_beets_complete_havester"
    potatoes_complete_havester="harvesting_potatoes_complete_havester"
    making_hay_rotary_tedder="harvesting_making_hay_rotary_tedder"
    loading_bales="harvesting_loading_bales"
    mowing_motor_mower="harvesting_mowing_motor_mower"
    mowing_rotary_mower="harvesting_mowing_rotary_mower"
    removing_potatoes_haulms="harvesting_removing_potatoes_haulms"
    windrowing_rotary_swather="harvesting_windrowing_rotary_swather"
    other="harvesting_other"

class OtherWorkProcesses(Enum):
    baling="otherworkprocesses_baling"
    chopping="otherworkprocesses_chopping"
    mulching="otherworkprocesses_mulching"
    transport_tractor_trailer="otherworkprocesses_transport_tractor_trailer"
    other="otherworkprocesses_other"

class PlasticDisposal(Enum):
    landfill="eol_plastic_landfill"
    incineration="eol_plastic_incineration"


class Biowaste(Enum):
    incineration = "eol_biowaste_incineration"
    anae_digestion = "eol_biowaste_anae_digestion"
    composting = "eol_biowaste_composting"
    other = "eol_biowaste_other"
