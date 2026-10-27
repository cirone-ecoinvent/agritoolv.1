"""Single data-access module for all external parameters and lookup tables.

Every constant used by the models (emission factors, model parameters, heavy-metal contents,
mappings, ecoinvent master data) is read from CSV files in ``<repo>/data`` through this module,
so sources can be updated or replaced without touching the calculation code. The provenance of
each file is recorded in ``data/sources.csv`` and ``data/SOURCES.md``.

CSV conventions: UTF-8, comma delimiter, dot decimal separator, one header row, units stated in
the column names or in a dedicated ``unit`` column. Empty cells mean "not available" (NA).
"""
import csv
import xml.etree.ElementTree as ET
from collections import namedtuple
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
# Raw input files supplied by FC (Master Data, FAOSTAT downloads, source workbooks). Git-ignored
# and read only by the scripts that build or check the tables of DATA_DIR, never by the models.
EXTERNAL_DATA_DIR = DATA_DIR / "external_data"

IntermediateExchange = namedtuple("IntermediateExchange", ["uuid", "name", "unit"])


def data_path(filename):
    """Absolute path of a data file; raises if it does not exist."""
    path = DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError("Data file not found: %s" % path)
    return path


@lru_cache(maxsize=None)
def rows(filename):
    """All rows of a CSV file as a tuple of dicts (values as strings).

    Completely empty rows (e.g. ",,,,," lines appended by spreadsheet-like editors) are skipped.
    """
    with open(data_path(filename), newline="", encoding="utf-8") as f:
        return tuple(row for row in csv.DictReader(f)
                     if any((value or "").strip() for value in row.values()))


@lru_cache(maxsize=None)
def params():
    """Scalar model parameters from ``model_parameters.csv`` as {name: float}."""
    return {row["name"]: float(row["value"]) for row in rows("model_parameters.csv")}


def param(name):
    """One scalar parameter from ``model_parameters.csv``."""
    try:
        return params()[name]
    except KeyError:
        raise KeyError("Parameter '%s' not found in model_parameters.csv" % name)


def _to_float_or_none(value):
    return float(value) if value not in ("", None) else None


@lru_cache(maxsize=None)
def table(filename, key_column=None, numeric=True):
    """A CSV table keyed by its first column (or ``key_column``).

    Returns {key: {column: value}}. With ``numeric=True`` every non-key column is converted to
    float, empty cells become None; columns that cannot be converted are kept as strings.
    """
    out = {}
    for row in rows(filename):
        key = row[key_column] if key_column else row[next(iter(row))]
        rec = {}
        for col, val in row.items():
            if col == (key_column or next(iter(row))):
                continue
            if numeric:
                try:
                    rec[col] = _to_float_or_none(val)
                except ValueError:
                    rec[col] = val
            else:
                rec[col] = val
        out[key] = rec
    return out


def crop_country_table(filename, column):
    """{crop: {country: float}} of a table with one row per crop and country (columns crop, country)."""
    out = {}
    for row in rows(filename):
        out.setdefault(row["crop"], {})[row["country"]] = float(row[column])
    return out


def metal_row(filename, key, metals):
    """Heavy-metal vector {metal: mg value} for one table row; NA (empty cell) -> 0.0."""
    row = table(filename)[key]
    return {m: (row.get(m) or 0.0) for m in metals}


HM_TABLE = "hm_salca2023_table1.csv"
HM_METALS = ("Cd", "Cu", "Zn", "Pb", "Ni", "Cr", "Hg")


def hm_entry(name):
    """One row of SALCAheavymetal 2023 Table 1 (data/hm_salca2023_table1.csv) by its English name.

    Returns {"Cd": ..., ..., "Hg": ..., "dm": kg DM/kg, "unit": concentration unit}. Raises a
    KeyError naming the table when the row does not exist.
    """
    rows = table(HM_TABLE, key_column="name_en")
    if name not in rows:
        raise KeyError("'%s' is not a row of %s" % (name, HM_TABLE))
    row = rows[name]
    entry = {m: (row.get(m) or 0.0) for m in HM_METALS}
    entry["dm"] = row["dm_kg_per_kg"]
    entry["unit"] = row["concentration_unit"]
    return entry


def single_metal_row(filename, metals):
    """Heavy-metal vector of a one-row table (deposition, leaching); NA -> 0.0."""
    row = next(iter(table(filename).values()))
    return {m: (row.get(m) or 0.0) for m in metals}


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def load_intermediate_exchanges(path, sheet="IntermediateExchanges", name_col="name",
                                id_col="id", unit_col="unitName"):
    """Load ecoinvent Master Data intermediate exchanges, keyed by exact English name.

    Accepts the ecoSpold2 master-data XML (``IntermediateExchanges.xml``, namespace-agnostic) or
    a table (``.xlsx`` sheet / ``.csv``) with the given column names. Returns
    {name: IntermediateExchange(uuid, name, unit)}.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("Master data file not found: %s" % path)
    records = []
    suffix = path.suffix.lower()
    if suffix == ".xml":
        for el in ET.parse(path).getroot().iter():
            if _local(el.tag) != "intermediateExchange":
                continue
            name = unit = ""
            for child in el:
                lang = child.get("{http://www.w3.org/XML/1998/namespace}lang", "en")
                if _local(child.tag) == "name" and lang == "en":
                    name = (child.text or "").strip()
                elif _local(child.tag) == "unitName" and lang == "en":
                    unit = (child.text or "").strip()
            records.append((el.get("id", ""), name, unit))
    elif suffix in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook  # optional dependency, only for xlsx master data
        ws = load_workbook(path, read_only=True, data_only=True)[sheet]
        it = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(it)]
        try:
            i_id, i_name, i_unit = (header.index(c) for c in (id_col, name_col, unit_col))
        except ValueError:
            raise ValueError("Sheet '%s' must have columns %r; found %r"
                             % (sheet, (id_col, name_col, unit_col), header))
        records = [(str(r[i_id]), str(r[i_name]).strip(), str(r[i_unit]))
                   for r in it if r[i_name]]
    else:
        with open(path, newline="", encoding="utf-8") as f:
            records = [(r[id_col], r[name_col].strip(), r[unit_col]) for r in csv.DictReader(f)]
    return {name: IntermediateExchange(uuid, name, unit) for uuid, name, unit in records if name}


@lru_cache(maxsize=None)
def load_intermediate_exchange_properties(path, sheet="IntermediateExchanges prop."):
    """Properties of the Master Data intermediate exchanges, read only from the ``.xlsx`` workbook.

    Returns {(product name, property name): amount}. Elemental contents (nitrogen content,
    phosphorus content, ...) are given by the Master Data on a dry-mass basis.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("Master data file not found: %s" % path)
    from openpyxl import load_workbook  # optional dependency, only for xlsx master data
    it = load_workbook(path, read_only=True, data_only=True)[sheet].iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    i_name, i_prop, i_amount = (header.index(c) for c in ("name", "propertyName", "amount"))
    return {(str(r[i_name]).strip(), str(r[i_prop]).strip()): float(r[i_amount])
            for r in it if r[i_name] and r[i_amount] is not None}


FERTILISER_BASIS_TABLE = "fertiliser_product_basis.csv"


def fertiliser_nutrient_content(master_data_path, model_variable):
    """kg of the amount basis (N, P2O5, K2O or Ca) per kg of the Master Data fertiliser product.

    From ``fertiliser_product_basis.csv``: the elemental content (property ``md_property`` of the
    Master Data, or ``fallback_content`` where the property is missing) times the dry mass of the
    product, divided by the same content of ``basis_product`` (the generic "as N / as P2O5 /
    as K2O" product), which converts P and K to P2O5 and K2O with the Master Data's own values.
    """
    row = table(FERTILISER_BASIS_TABLE)[model_variable]
    props = load_intermediate_exchange_properties(str(master_data_path))
    name, prop = row["md312_name"], row["md_property"]
    content = props.get((name, prop), row["fallback_content"])
    if content is None:
        raise KeyError("No '%s' for '%s' in the Master Data and no fallback in %s"
                       % (prop, name, FERTILISER_BASIS_TABLE))
    content *= props.get((name, "dry mass"), 1.0)
    if row["basis_product"]:
        content /= props[(row["basis_product"], prop)]
    return content
