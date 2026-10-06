"""Direct emissions calculation blocks for field crops."""

from agritool.models import Emission, EmissionFactor, nonnegative


def direct_soil_n2o(nitrogen_kg: float, factor: EmissionFactor) -> Emission:
    """Calculate the EF1 nitrogen-input term, excluding grazing and organic soils.

    nitrogen_kg is total kg N, not kg fertilizer or kg N per hectare.
    The factor is in kg N2O-N/kg N; 44/28 converts N2O-N mass to N2O.
    """
    nonnegative(nitrogen_kg, "nitrogen_kg")
    if factor.unit != "kg N2O-N/kg N":
        raise ValueError("direct soil N2O requires a factor in kg N2O-N/kg N")
    return Emission(
        flow="Dinitrogen monoxide",
        amount_kg=nitrogen_kg * factor.value * (44 / 28),
        methodology="IPCC 2006 Volume 4 Chapter 11, Equation 11.1: EF1 input term",
        factor_source=factor.source,
    )
