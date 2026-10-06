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
