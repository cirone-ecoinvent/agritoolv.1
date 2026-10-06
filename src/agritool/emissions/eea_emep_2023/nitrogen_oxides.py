"""Tier 1 NOx emissions from fertiliser nitrogen."""

from agritool.models import Emission, EmissionFactor, nonnegative

_DEFAULT_FACTOR = EmissionFactor(
    0.04,
    "kg NO2/kg N",
    "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.3.2, Table 3-1",
)


def nitrogen_oxides_from_n_fertilizers(
    nitrogen_kg: float, factor: EmissionFactor | None = None
) -> Emission:
    """Calculate NOx reported as NO2 from total applied fertiliser N.

    Uses EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.3.1, Equation (1),
    and section 3.3.2, Table 3-1. The default EF is 0.04 kg NO2/kg N, so no
    additional conversion from N mass is required. NO has no Tier 2 method.
    """
    nonnegative(nitrogen_kg, "nitrogen_kg")
    selected_factor = _DEFAULT_FACTOR if factor is None else factor
    if not isinstance(selected_factor, EmissionFactor):
        raise ValueError("factor must be an EmissionFactor")
    if selected_factor.unit != "kg NO2/kg N":
        raise ValueError("NOx requires a factor in kg NO2/kg N")
    return Emission(
        flow="Nitrogen oxides",
        amount_kg=nitrogen_kg * selected_factor.value,
        methodology=(
            "EMEP/EEA Guidebook 2023, Chapter 3.D, section 3.3.1, "
            "Equation (1), and section 3.3.2, Table 3-1; NO emissions are "
            "reported together with NO2 as NOx."
        ),
        factor_source=selected_factor.source,
    )
