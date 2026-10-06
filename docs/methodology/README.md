# Methodology Reference Documents

Upload the source documents (PDFs, guidebooks, spreadsheets) for each methodology into the subfolders below. These are the authoritative references for AgriTool's emission models.

## Folder structure

```
docs/methodology/
├── EEA_EMEP_2023/        # EMEP/EEA Air Pollutant Emission Inventory Guidebook 2023 (3.D Crop production & agricultural soils)
├── IPCC_2019/            # 2019 Refinement to the 2006 IPCC Guidelines, Vol. 4 (Ch. 5 Cropland, Ch. 11 N2O & CO2 from liming/urea)
├── Nemecek_2015/         # Nemecek et al. 2015 – ecoinvent / WFLDB methodological guidelines (P, heavy metals, NO3)
├── Nemecek_2022_OLCA/    # Nemecek et al. 2022 – Operationalising emission and toxicity modelling of pesticides (OLCA-Pest)
└── Nitrogen_balance/     # Nitrogen balance method documentation for NO3 leaching
```

The EMEP/EEA reference used below is
[`EEA_EMEP_2023/3.D Agricultural soils 2023 FINAL.pdf`](EEA_EMEP_2023/3.D%20Agricultural%20soils%202023%20FINAL.pdf).

## Emission → method mapping

| Element | Origin | Action | Compartment | Method |
|---|---|---|---|---|
| NH3 | N fertilizers | Volatilization | air | EEA/EMEP 2023* |
| NOx | N fertilizers | Volatilization | air | EEA/EMEP 2023 |
| N2O | N fertilizers | Volatilization | air | IPCC 2019, disaggregated |
| NO3 | N fertilizers | Leaching | water | Nitrogen balance* |
| P | P fertilizers | Run-off | water | Nemecek et al. 2015* |
| PO4 | P fertilizers | Erosion | water | Nemecek et al. 2015* |
| PO4 | P fertilizers | Leaching | water | Nemecek et al. 2015* |
| CO2 | Lime and Urea | Volatilization | air | IPCC 2019 |
| CH4 | Rice | Volatilization | air | IPCC 2019 |
| PM | Field operations | Volatilization | air | EEA/EMEP 2023 |
| Heavy metals | Fertilizers & PPP | Leaching | ground-water | Nemecek et al. 2015* |
| Heavy metals | Fertilizers & PPP | Erosion | surface water | Nemecek et al. 2015* |
| Pesticides | PPP | Volatilization | air | OLCA, Nemecek et al. 2022 |
| Pesticides | PPP | Volatilization (drift/runoff) | water | OLCA, Nemecek et al. 2022 |
| Pesticides | PPP | Application + volatilization | soil | OLCA, Nemecek et al. 2022 |

\* Method marked with an asterisk = advanced/tier-specific variant to be confirmed against the uploaded document.

## Conventions
- Name files as `<Author>_<Year>_<ShortTitle>.pdf`.
- Each implemented module in the codebase should cite the document and the specific chapter/table/equation it implements.

## EMEP/EEA 2023 crop-production methods

| Emission | Tier and method in the reference | Implementing module |
|---|---|---|
| NH3 from inorganic N fertilisers | Chapter 3.D, section 3.4.1, Equations (3)–(4), Table 3-2. Equation (3) allocates fertiliser N by normal/high-pH area when region-specific amounts are unavailable; Equation (4) applies the type- and pH-specific factors. Table 3-2 defines normal pH as ≤7.0 and high pH as >7.0. | `src/agritool/emissions/eea_emep_2023/ammonia.py` |
| NOx from fertiliser N | Tier 1, Chapter 3.D, section 3.3.1, Equation (1), and section 3.3.2, Table 3-1. The 0.04 kg NO2/kg N factor is already expressed as reported NO2 mass; NO is reported with NO2 as NOx. | `src/agritool/emissions/eea_emep_2023/nitrogen_oxides.py` |
| PM from field operations | Tier 2, Chapter 3.D, section 3.4.1, Equation (5), Tables 3-6–3-9. The tables give crop/operation factors for PM10 and PM2.5 under dry (Mediterranean) and wet (all other) climates. | `src/agritool/emissions/eea_emep_2023/particulate_matter.py` |

The NH3 Tier 2 table specifies a soil-pH adjustment but no climate adjustment; the ammonia API validates the supplied climate qualifier but does not apply a climate-dependent factor. The PM tables do not provide a Tier 2 TSP factor. Ecoinvent particulate flows are mutually exclusive fractions, so the module reports PM2.5 directly and derives PM2.5–10 as PM10 minus PM2.5.
