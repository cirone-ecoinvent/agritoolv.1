"""Normalize calculated emissions without coupling equations to database mapping."""

from collections.abc import Iterable

from agritool.models import Emission, nonempty, nonnegative


def build_inventory(
    emissions: Iterable[Emission],
    reference_product: str,
    production_amount: float,
    production_unit: str,
) -> dict:
    """Prepare JSON-serializable emissions per unit of reference product.

    Production and emissions must cover the same system and assessment period.
    Flow names still require mapping to a specific ecoinvent release.
    """
    nonempty(reference_product, "reference_product")
    nonempty(production_unit, "production_unit")
    nonnegative(production_amount, "production_amount")
    if production_amount == 0:
        raise ValueError("production_amount must be greater than zero")
    exchanges = []
    for emission in emissions:
        amount = emission.amount_kg / production_amount
        nonnegative(amount, "normalized emission amount")
        exchanges.append(
            {
                "flow": emission.flow,
                "amount": amount,
                "unit": "kg",
                "compartment": emission.compartment,
                "methodology": emission.methodology,
                "factor_source": emission.factor_source,
            }
        )
    return {
        "reference_product": reference_product,
        "reference_amount": 1,
        "reference_unit": production_unit,
        "mapping_status": "unmapped",
        "exchanges": exchanges,
    }
