"""Direct emissions calculation blocks for livestock."""

from agritool.models import Emission, EmissionFactor, nonnegative


def enteric_methane(average_animals: float, factor: EmissionFactor) -> Emission:
    """Calculate annual CH4 for one livestock category using its annual mean herd."""
    nonnegative(average_animals, "average_animals")
    if factor.unit != "kg CH4/head/year":
        raise ValueError("enteric methane requires a factor in kg CH4/head/year")
    return Emission(
        flow="Methane",
        amount_kg=average_animals * factor.value,
        methodology="IPCC 2006 Volume 4 Chapter 10, Equation 10.19: Tier 1",
        factor_source=factor.source,
    )
