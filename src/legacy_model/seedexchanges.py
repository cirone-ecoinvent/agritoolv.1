"""Seed and seedling exchanges resolved from the ecoinvent Master Data (Fix F6).

Port of the seed functions of the specification package (AgriToolV.1/legacy_fixes/
reference_models.py): the reviewed mapping ``data/seed_exchange_mapping.csv`` gives, per crop
key, the exact name of the IntermediateExchange of the Master Data; the UUID and the unit always
come from the Master Data itself (``dataloader.load_intermediate_exchanges``). Legacy crop codes
that differ from the mapping keys are translated by ``data/crop_key_aliases.csv``.

The resolution fails loudly instead of silently dropping the input: unmapped crop, unreviewed row
(status ``proposed`` / ``to_decide``), exchange missing from the Master Data, or unit mismatch
between the template amount and the exchange.
"""
import csv
import difflib
import re
from collections import namedtuple

import config
import dataloader

SeedMappingRow = namedtuple("SeedMappingRow", ["exchange_name", "status"])
USABLE_STATUS = ("confirmed", "no_exchange")
MAPPING_FILE = "seed_exchange_mapping.csv"
ALIAS_FILE = "crop_key_aliases.csv"


def normalise_crop_key(name):
    """Canonical crop key: lower case, separators -> '_'."""
    key = re.sub(r"[\s\-/,.]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", key).strip("_")


def crop_key(legacy_crop_code):
    """Mapping key of a legacy crop code (alias table first, then normalisation)."""
    aliases = {r["legacy_crop_code"]: r["mapping_crop_key"] for r in dataloader.rows(ALIAS_FILE)}
    return normalise_crop_key(aliases.get(legacy_crop_code, legacy_crop_code))


def load_seed_mapping(path=None):
    """crop_key -> SeedMappingRow from the reviewed mapping CSV."""
    if path is None:
        rows = dataloader.rows(MAPPING_FILE)
    else:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return {normalise_crop_key(r["crop_key"]):
            SeedMappingRow(r["seed_exchange_name"].strip() or None, r["status"].strip())
            for r in rows}


def validate_seed_mapping(mapping, exchanges):
    """Mapped exchange names that do not exist in the master data (should be empty)."""
    return sorted({row.exchange_name for row in mapping.values()
                   if row.exchange_name and row.exchange_name not in exchanges})


def suggest_seed_exchanges(crop, exchanges, n=5):
    """Candidate seed / seedling exchange names for building the mapping (review by hand)."""
    words = normalise_crop_key(crop).split("_")
    pool = [e for e in exchanges if re.search(r"seed|seedling|sowing|planting", e, re.I)]
    hits = [e for e in pool if all(w in e.lower() for w in words)]
    return hits[:n] or difflib.get_close_matches("%s seed, for sowing" % crop, pool, n=n, cutoff=0.4)


def resolve_seed_exchange(crop, mapping, exchanges, expected_unit=None):
    """IntermediateExchange of the seed input of ``crop`` (a legacy code or a mapping key).

    Returns None only for crops marked ``no_exchange``; raises KeyError / ValueError otherwise.
    """
    key = crop_key(crop)
    if key not in mapping:
        raise KeyError("No seed mapping for crop '%s' (key '%s'). Candidates: %s"
                       % (crop, key, suggest_seed_exchanges(crop, exchanges)))
    row = mapping[key]
    if row.status not in USABLE_STATUS:
        raise ValueError("Seed mapping for '%s' has status '%s': review it first" % (crop, row.status))
    if row.status == "no_exchange":
        return None
    if row.exchange_name not in exchanges:
        raise KeyError("Mapped exchange '%s' for '%s' not in master data" % (row.exchange_name, crop))
    exchange = exchanges[row.exchange_name]
    if expected_unit is not None and exchange.unit != expected_unit:
        raise ValueError("Unit mismatch for '%s': exchange in %s, amount in %s"
                         % (crop, exchange.unit, expected_unit))
    return exchange


_MASTER_DATA_CACHE = {}


def master_data_exchanges():
    """Intermediate exchanges of the configured Master Data file (cached per path)."""
    path = config.require_master_data_path()
    if path not in _MASTER_DATA_CACHE:
        _MASTER_DATA_CACHE[path] = dataloader.load_intermediate_exchanges(path)
    return _MASTER_DATA_CACHE[path]
