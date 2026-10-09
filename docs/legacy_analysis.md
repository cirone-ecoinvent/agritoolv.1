# Legacy agritool (sri-crop-tool) analysis

Analysis of the legacy ecoinvent LCI calculation tool for crop production, repository
`C:\python\sri-crop-tool` (Quantis "ALCIG" / "LCI Generator", Maven artifact
`com.quantis_intl:lci-generator:1.3.4-EI`). This is a read-only analysis: no file in the legacy
repository was modified and the legacy application was not run by the author of this report.

Conventions used throughout:

- **[V]** verified directly in the source code, resources or documents of the repository.
- **[I]** inferred (methodological attribution, intent, or behaviour not directly stated in code or docs).
- Paths are relative to `C:\python\sri-crop-tool\`; `src/main/python/` is abbreviated `py/`,
  `src/main/java/com/quantis_intl/lcigenerator/` is abbreviated `java/`.
- Line numbers refer to the files as of git commit `a0a434a` (master, 2023-08-24).

Disclosure: one automated exploration subagent used during this analysis ran the legacy Python unit
tests and a few stdlib introspection snippets with a local Python 3.14 interpreter, against the
instruction not to execute the legacy code. Nothing was written to the repository (`git status` is
clean, no `__pycache__` folders). Its test results are reported in section 7.9 and are explicitly
labelled; they were not re-run.

---

## 1. Overview

### 1.1 Purpose and scope

The tool turns a filled Excel data-collection template (one crop, one country, one hectare and one
crop cycle) into an ecoSpold2 activity dataset for the crop production activity, expressed per kg
of harvested main product. It covers [V]:

- 67 crops and 39 countries (`src/main/resources/crops.properties`, `countries.properties`).
- Inputs: seeds/seedlings/trees, irrigation water, mineral N/P/K/Ca/Mg/Zn fertilisers and other
  minerals, liquid and solid manure, compost and sewage sludge, pesticides (140 herbicides, 102
  fungicides, 106 insecticides), field work (diesel per operation group), energy, water, materials,
  greenhouses, wastes.
- Direct field emissions: NH3, N2O, NOx, NO3 leaching, phosphorus (leaching, run-off, erosion), heavy
  metals (Cd, Cu, Zn, Pb, Ni, Cr, Hg) to soil and water, CO2 from urea and liming, pesticide active
  ingredients to soil, water balance, COD/DOC/TOC/BOD5 from waste water, land occupation and
  transformation, land-use change as a parametrised formula, CO2 uptake and energy content of the
  harvested biomass.
- Defaults for almost every input when the user leaves a cell empty (country- and crop-specific
  tables generated from an internal Quantis workbook referred to as "GD_crop").

The documented methodology is `src/main/dart/web/Ecoinvent_Tool_Model_Description_20191015.pdf`
(Quantis: Faist Emmenegger, Delerce-Mauris, Porté; final report dated 30 January 2018), which states
that the models are aligned with the World Food LCA Database (WFLDB) guidelines (Nemecek et al. 2015)
[V, from the PDF text].

### 1.2 History

[V] git history: 354 commits on `master`, no tags. First commit 2015-03-05 ("Implement
ManureModel", cporte); model implementation 2015; ecoinvent/ecoSpold adaptation and move from
Angular 1 to AngularDart 4 Oct-Dec 2017; new crops, uncertainties, LUC per kg and the ecoinvent
template Jan-Jun 2018 (v1.3.0-EI); v1.3.2-EI to v1.3.4-EI Nov 2018 - Oct 2019 (last functional
commit 2019-10-16, "update guidance for new crop and tool model description"); README-only commits
2021-2023. Authors: cdelerce (176 commits), cporte (174), cedric-roussel (5), Alexandre Herbert (1).
A branch `origin/francesco-branch` has one extra commit (2025-05-20, comments only).

### 1.3 Architecture

Three languages and three runtimes [V]:

| Layer | Technology | Location | Role |
|---|---|---|---|
| Frontend | Dart 1.24 / AngularDart 4 (`src/main/dart/pubspec.yaml`) | `src/main/dart/` | Login, template download, Excel upload, warnings display, download of the generated `.spold` file |
| Backend | Java 8, Maven, Guice 3, RESTEasy + Jetty + Shiro (from proprietary Quantis jars `stack`, `login`), MyBatis + MySQL, Apache POI 3.17, JAXB | `src/main/java/` | HTTP API, Excel parsing and validation, user/license/generation persistence, ecoSpold2 (and legacy SimaPro CSV) writing |
| Model layer | Python 3 (stdlib `http.server`, `enum`, `ChainMap`; only external dependency `python-dateutil`) | `src/main/python/` | Default values, unit conversions, all emission models, output mapping |

The Java backend and the Python model layer are separate OS processes. Java calls Python over HTTP
(`POST http://localhost:11001/computeLci`, JSON in / JSON out) through
`java/PyBridgeService.java:51-68`; the Python server is `py/bootstrap.py:9-29`. There is no
Jython and no subprocess call.

### 1.4 Module dependency map

```
Dart frontend (src/main/dart)
  tool_page / process_generation_steps  --HTTP multipart--> POST app/api/computeLci
                                        --HTTP form-------> POST app/api/generateScsv (dbOption=ECOINVENT)
          |
          v
Java backend (java/)
  Bootstrap.main ----> QtsStack (proprietary) + guice/CoreModule
  api/Api.computeLci ----> imports/ExcelInputReader ----> imports/{NumericExtractor, StringFromListExtractor,
         |                        |                         StringExtractor, DateExtractor, LabelForBlockTags,
         |                        |                         PropertiesLoader, ValueGroup, SingleValue, Origin}
         |                        +--> ErrorReporterImpl (errors/warnings)
         +--> dao/MybatisGenerationDao, license/LicenseService (MySQL)
  api/Api.generateScsv ---> ValueGroup.flattenValues() --> PyBridgeService --HTTP JSON--> Python
         |
         +--> EcospoldFileWriter ----> ecospold/{EcospoldTemplateIntermediaryExchanges,
         |         |                    EcospoldTemplateSubstanceUsages, StandardUncertaintyMetadata,
         |         |                    AvailableUnit, UUIDType5}
         |         +--> ecospold/{PossibleElementaryExchangesCache, PossibleIntermediateExchangesCache,
         |                        PossibleActivityNamesCache, PossibleActivityLinkCache,
         |                        PossiblePropertyCache, PossibleParametersCache} <-- ecoinvent master-data XML
         |         +--> ecospold/{GeographyMappingCache, CropsEcospoldRefsCache} <-- resources
         +--> ScsvFileWriter ----> scsv/* (WFLDB / SimaPro CSV, legacy, not reachable from the UI)

Python model layer (py/)
  bootstrap.py --> modelsSequence.ModelsSequence
        allInputs = DefaultValuesWrapper(ChainMap(NonStrictInputMapping(raw, EXCEL_INPUT_MAPPING_RULES),
                                                  intermediateValues, outputMapping.output),
                                         DEFAULTS_VALUES_GENERATORS)
        inputMappings.py, excelInputMappingRules.py      (raw key -> model key, enums)
        defaultGeneration.py  <-- defaultTables.py, defaultMatrix{YieldPerYear, NUptake,
                                  EvapoTranspiration, Seed, TotalManure, TotalMineralFert, TotalPesticides}.py
        models/{fertilisermodel, manuremodel, otherorganicfertilisermodel, seedmodel, erosionmodel,
                irrigationmodel, co2model, nmodel, pmodel, hmmodel, packmodel, lucmodel}.py
                <-- models/atomicmass.py, models/modelEnums.py, directMappingEnums.py
        outputMapping.OutputMapping  --> flat dict of output variables (per ha and crop cycle)
```

### 1.5 End-to-end data flow (summary)

1. The user uploads the template. `Api.computeLci` (`java/api/Api.java:112-183`) checks extension
   and size (10 MB), parses it with `ExcelInputReader.getInputDataFromFile`, stores warnings and the
   file on disk, creates a `generation` row and checks the license. No calculation happens here [V].
2. The user requests the file. `Api.generateScsv` (`Api.java:242-266`) retrieves the parsed
   `ValueGroup`, flattens it to a `Map<String,Object>` and posts it to Python.
3. `ModelsSequence.executeSequence` (`py/modelsSequence.py:28-54`) runs the models in a fixed order
   and fills `OutputMapping.output`, a flat `dict` whose values are per hectare and per crop cycle.
4. `Api.onResult` (`Api.java:298-325`) streams the ecoSpold2 file produced by
   `EcospoldFileWriter.writeModelsOutputToEcospoldFile` (`java/EcospoldFileWriter.java:122-304`),
   which divides every amount by `yield_main_product_per_crop_cycle` so the dataset is per kg of
   main product.

---

## 2. How to run

### 2.1 Entry points

| Component | Entry point | Notes |
|---|---|---|
| Java backend | `java/Bootstrap.java:37-58` (`main`) | `args[0]` = path of a properties file for the proprietary `QtsStack`; with no argument, defaults from `getDefaultProperties()` (`Bootstrap.java:60-84`): port 7879, dev mode, web folder `src/main/dart/web`, MySQL schema `lcigenerator_test` user `root`/`root` on localhost, `pyBridge.url=http://localhost:11001/computeLci`, uploaded-files folder from env var `ALCIG_UPLOADED_FILES_FOLDER`. Login secret hardcoded at `Bootstrap.java:53`. |
| Python model server | `py/bootstrap.py:27-29` | `python bootstrap.py` from `src/main/python`; listens on `localhost:11001`; host/port hardcoded (`#TODO: Read from external properties`, line 5). |
| Dart frontend | `src/main/dart/web/index.dart` | Dev: `pub serve web --port=36123` (installation guide); when served on port 36123 the API base is `http://localhost:7879/`, otherwise relative `app/`. |
| HTTP API | `java/api/Api.java` (`/`), `PublicApi.java` (`pub/`), `PublicAlcigApi.java` (`pub/principal/`), `LicenseApi.java` (`/license`) | Mounted by the stack under `app/api/` [I from frontend URLs]. Generation endpoints: `GET userGenerations`, `POST computeLci` (multipart: `uploadFile`, `filename`, `generationId`, `canBeStored`), `POST generateScsv` (form: `generationId`, `dbOption`). |

### 2.2 Required inputs and prerequisites

- The Excel template `src/main/dart/web/LCI-Database_Data-collection_Crop_v2.xlsx` (see section 3).
- **ecoinvent master-data XML files** in the uploaded-files folder, read at startup by the caches
  (`java/ecospold/Possible*Cache.java`): `ElementaryExchanges.xml`, `IntermediateExchanges.xml`,
  `ActivityNames.xml`, `ActivityIndex.xml`, `Parameters.xml`, `Properties.xml`. They are **not in
  the repository**; the application throws `IllegalStateException` if one is missing
  (e.g. `PossibleElementaryExchangesCache.java:35-40`). The ecoinvent version they came from is not
  recorded anywhere in the repository [V].
- MySQL (README: Docker `mysql:5.7` with `skip_ssl`; installation guide: MySQL <= 5.7). Schema:
  `src/main/sql/script.sql` creates `generation`, `license`, `registrationRequest` and updates
  `mailTemplate`; it depends on the `user_std` table created by the proprietary `login` project's
  script, which is not in the repository [V].
- Proprietary Quantis jars in `lib/` (`stack-0.2.7`, `login-0.1.10`, `common-formats-0.0.3`),
  without source code; `pom.xml:148-154` declares `lib/` as a file-based Maven repository.

### 2.3 Build and deployment

- Build: `mvn package` with Java 8 (`pom.xml:51-52`), `maven-shade-plugin` fat jar, and
  `dart-maven-plugin` running `pub get` / `pub build` with `dartSdk=/usr/lib/dart` (`pom.xml:59-92`).
- Installation guide: `Ecoinvent LCI calculation tool - Installation guide_2019-07-02.pdf` (repo
  root). Prerequisites listed there [V, PDF text]: MySQL <= 5.7, Dart SDK 1.24.3, Java 8, Python 3,
  IntelliJ; build the Quantis `stack`, `login`, `common` projects with `mvn install`; run
  `script.sql` of stack, login and alcig in that order, then `test_data.sql` (test user
  `user1`/`test`); set `ALCIG_UPLOADED_FILES_FOLDER` with trailing slash.
- Production (README.md, 2023): AWS eu-central-1, URL `https://agritool.ecoinvent.org/#/tool`; an
  AWS dev-proxy terminates SSL and routes `/app` to the Java backend on port 10042 and `/` to nginx
  serving the frontend from `$HOME/quantis/alcig-ei/web`; two systemd units `agri_java.service` and
  `agri_python.service`; JVM `-Xmx1G`; binaries were copied from the previous host (Infomaniak), not
  rebuilt; user self-registration does not work and users are inserted in the database by hand.
  No production properties file is in the repository, so how port 10042 is configured is unknown [I].

### 2.4 Runtime environment and dependency status

| Dependency | Version in repo | Status (as of 2026) |
|---|---|---|
| Java | 1.8 source/target | Works on JDK 8 only without changes: `javax.xml.bind` (JAXB) is used (`EcospoldFileWriter.java:302`) but not declared in `pom.xml`; removed from the JDK in Java 11. |
| Guice (+ servlet, multibindings) | 3.0 (2011) | Pinned ("Can't be higher as it will use guice 4", `pom.xml:201`); very old. |
| mybatis / mybatis-guice / typehandlers-jsr310 | 3.5.1 / 3.7.1 / 1.0.2 | Old but functional. |
| mysql-connector-java | 8.0.16 | Old; known CVEs in that line. |
| HikariCP | 3.3.1 | Old. |
| Apache POI poi-ooxml | 3.17 (2017) | Uses `Cell.CELL_TYPE_STRING` int constants (`ExcelInputReader.java:159`) removed in POI 4+/5. Known CVEs. |
| bval-jsr / validation-api | 1.1.2 / 1.1.0 | Validation call is commented out (`EcospoldFileWriter.java:297-300`). |
| junit | 4.12 (test) | No Java tests exist. |
| Quantis `stack` / `login` / `common-formats` | 0.2.7 / 0.1.10 / 0.0.3 | Proprietary, no source; bring transitively Jetty 9.4.18, RESTEasy 3.0.19, Jackson 2.9.8 (deprecated `JSR310Module`, `PyBridgeService.java:78`), Shiro 1.3.2, Guava, logback 1.2.3 [V from the `.pom` files in `lib/`]. All outdated. |
| Dart / AngularDart | SDK >=1.24 <2.0, angular 4.x, `pub build` transformers | Dart 1 and transformer-based builds are discontinued; cannot be built with current Dart SDKs. |
| Python | 3 (>= 3.4: `enum`, `ChainMap`, `super()` without args, `http.server`) | No version pin, no requirements file; `python-dateutil` needed (`py/defaultGeneration.py:1`). |
| MySQL | 5.7 | End of life (Oct 2023). |

---

## 3. Input: the Excel template

### 3.1 Workbook structure [V]

`src/main/dart/web/LCI-Database_Data-collection_Crop_v2.xlsx`, version string `v2.0.0` in
`Template!A1`. Sheets: `Introduction`, `User Guidance` (same rows as Template with guidance text in
column E), `Template` (the one read by the code), `Lists` (hidden; dropdown sources).

Functional unit stated in the User Guidance: 1 ha and 1 crop cycle; "If no data or answer, just
leave '-'. Enter 0 where the amount is such."

### 3.2 How the Java reader locates and types values [V]

`java/imports/ExcelInputReader.java`:

1. The first sheet whose name starts with `Template` is used (`:59-61`); otherwise the error
   "The file must contain a tab named Template".
2. **Hidden row 1 (index 0)** holds the file version in A1 (read into `fileVersion` but never
   validated, `:151-152`) and the column markers `label_column` (C), `country_column` (D),
   `data_column` (E), `comment_column` (F), `source_column` (G) (`:154-232`). All five must be
   present exactly once; anything else in row 1 only triggers a warning.
3. **Hidden column A** holds a machine tag on each data row (`METADATA_COLUMN_INDEX = 0`). Rows are
   scanned with `loadNextMeaningfulRow` (`:430-455`), which skips rows where both the tag and the
   data cell are blank.
4. `crop` (row 5) and `country` (row 6) must be the first two tagged rows and their value is read
   from the **country column (D)**, not from the data column (`readCropOrCountry`, `:241-259`). They
   are the only **mandatory** inputs: an unknown label produces an *error* (`StringFromListExtractor
   .extractMandatory`, `:140-154`), and any error aborts the upload with HTTP 400.
5. Every other tagged row is dispatched by `readOtherRows` (`:261-297`) on membership of the tag in
   hardcoded sets:
   - `LabelForBlockTags.LABELS_FOR_NUMERIC` (pesticide blocks `total_herbicides`,
     `total_fungicides`, `total_insecticides`) -> `readBlock` (`:315-370`);
   - `LabelForBlockTags.LABELS_FOR_RATIO` (`total_composttype`, `total_sewagesludge`,
     `total_plantprotection`, `total_soilcultivation`, `total_sowingplanting`,
     `total_fertilisation`, `total_harvesting`, `total_otherworkprocesses`) -> `readRatioBlock`
     (`:372-428`);
   - `StringFromListExtractor.TAGS_TO_MAP` (dropdowns: `organic_certified`, `climate_zone_1`,
     `climate_zone_specific`, `cultivation_type`, `tillage_method`, `anti_erosion_practice`);
   - `StringExtractor.TAGS_FOR_STRING` (free text: `record_entry_by`, `collection_method`,
     `data_treatment_extrapolations`, `data_treatment_uncertainty`, `comment`);
   - `DateExtractor.TAGS_FOR_STRING` (4 dates; Excel date cell or text `dd.MM.yy`);
   - `NumericExtractor.TAGS_FOR_NUMERIC` (75 tags) and `TAGS_FOR_RATIO` (57 tags).
   A filled cell whose tag is in none of these sets gives the warning "This cell will be ignored".
6. Inside a block, untagged rows follow until the tag `end` or a different tag. The **label text in
   column C** (the user's dropdown choice) is mapped to a key via `LabelForBlockTags` maps or via the
   reversed `herbicides/fungicides/insecticides.properties`; an unknown label is stored as `other`
   with a warning (`:343-365`, `:400-423`).
7. Empty values: `""`, any `<...>` placeholder and `-` count as empty (`dataCellIsFilled`,
   `:299-308`). `warnIfDefaultExists` is an empty TODO (`:310-313`).
8. Post-processing: `ValueGroup.groupValues` (`java/imports/ValueGroup.java:81-120`) groups loose
   `ratio_<group>_<item>` tags into `RatioValueGroup`s keyed by `total_<group>`;
   `validateSumsAndRatios` (`ExcelInputReader.java:477-554`) normalises ratio groups that do not sum
   to 1 (warning), adds an `other` remainder to part groups whose detail is lower than the total, or
   raises the total when the detail is higher (warning); hardcoded aggregation of pesticide totals
   (`pest_total` vs herbicides+fungicides+insecticides, producing `pest_remains`) and of machinery
   diesel (`total_machinery_diesel` vs the six operation groups, producing
   `remains_machinery_diesel`). `validateDates` warns if the main harvest is less than 15 days
   after the previous harvest.
9. The values travel as a `ValueGroup` tree of `SingleValue` objects (key, value, comment, source,
   `Origin` = Excel cell coordinates + label, or `DEFAULT_VALUE` / `GENERATED_VALUE`).
   `flattenValues()` (`ValueGroup.java:122-133`, `:228-247`, `:286-305`) produces the flat map sent
   to Python: plain keys, `ratio_<group>_<item>`, `part_<group>_<item>`, `total_<group>`. Dates are
   serialised by Jackson as `[y, m, d]` arrays; Python rebuilds them with
   `date(d[0], d[1], d[2])` (`py/defaultGeneration.py:161-164`) [V].

### 3.3 Validation rules and units [V]

- Numeric cells: non-numeric or negative -> warning, value dropped (default used)
  (`NumericExtractor.java:196-219`). Ratio cells: additionally > 1 -> warning, dropped (`:221-241`).
- Dropdowns: a value not in the hardcoded map -> warning, dropped (`StringFromListExtractor.java:122-138`).
- Errors (blocking): missing/duplicated column markers, missing `crop`/`country` rows or unknown
  crop/country label, unreadable workbook, wrong extension, file > 10 MB, no "Template" sheet.
- **Units are never read.** The unit text in column D (e.g. `[kg N]`, `[%]`, `[m3]`) is for the
  user only; every `DoubleSingleValue` is created with unit `"TODO"` (`NumericExtractor.java:193,
  240`; `ValueGroup.java:193 // TODO: Handle Unit`). The code therefore assumes the template's
  fixed units. Cells labelled `[%]` are read as ratios 0-1 (`extractRatio` rejects values > 1), so
  they only work when the Excel cell is percent-formatted (Excel stores 0.5 for 50 %); a plain `50`
  is dropped with a warning [V].
- Warnings are returned to the frontend as JSON (`ErrorReporterImpl.ErrorReporterResult{type,
  context{cell,label}, message}`) and persisted in `generation.warnings`.

### 3.4 Field inventory (Template sheet, rows 5-203) [V, from a stdlib XML dump of the workbook]

Column "Default" is the Python default generator used when the cell is empty
(`py/defaultGeneration.py:432-587`, see section 4.1); "req." = mandatory in Java.

**Selectors and metadata**

| Row | Tag (col. A) | Label | Unit in template | Type | Required | Default |
|---|---|---|---|---|---|---|
| 5 | `crop` | Select your crop | - | dropdown (67 crops, `Lists!I`) | **yes** | none |
| 6 | `country` | Select your country | - | dropdown (39 countries, `Lists!J`) | **yes** | none |
| 10 | `record_entry_by` | Record / Data entry by | [-] | text | no | not used by ecoSpold writer |
| 11 | `collection_method` | Collection method | [-] | text | no | idem |

**Agricultural system**

| Row | Tag | Label | Unit | Type | Default |
|---|---|---|---|---|---|
| 14 | `climate_zone_1` | Climate zone 1 | [-] | dropdown: Cool / Temperate / Warm climate | `temperate_climate` |
| 15 | `climate_zone_specific` | Climate zone 2 | [-] | dropdown (31 Köppen-style zones, filtered by zone 1) | derived from zone 1 (`ClimateDefaultGenerator`) |
| 16 | `average_annual_precipitation` | Average annual precipitation | [mm per year] | numeric | country table, 0 if not open ground |
| 17 | `nb_wet_days_per_year` | Number of wet days per year | [#] | numeric | 180 |
| 18 | `mean_elevation_m` | Mean elevation | [m] | numeric | 700 |
| 20 | `cultivation_type` | Type of cultivation | [-] | dropdown: open ground; greenhouse open ground unheated/heated; greenhouse hydroponic unheated/heated | `open_ground` (pre-filled) |
| 21 | `organic_certified` | Certified organic agriculture | [-] | yes/no | `no` (pre-filled) |
| 22 | `drainage` | Drainage | [% of area] | ratio | 0.0 (`drained_part`) |
| 24 | `harvest_date_previous_crop` | Harvest date previous crop | [dd.mm.yy] | date | used only for `crop_cycle_per_year` (default 1.0) |
| 25 | `soil_cultivating_date_main_crop` | Soil cultivating date | [dd.mm.yy] | date | read, never used by models |
| 26 | `sowing_date_main_crop` | Sowing date | [dd.mm.yy] | date | read, never used by models |
| 27 | `harvesting_date_main_crop` | Harvesting date | [dd.mm.yy] | date | see row 24 |
| 28 | `seeds` | Seeds, arable crops and vegetables | [kg] | numeric | crop/country matrix (`NB_SEEDS_...`), else 0 |
| 29 | `nb_seedlings` | Number of seedlings | [#] | numeric | matrix (`NB_SEEDLINGS_...`) |
| 30 | `nb_planted_trees` | Number of planted trees | [#] | numeric | matrix (`NB_PLANTED_TREES_...`, all empty -> 0) |
| 31 | `orchard_lifetime` | Lifetime of orchard | [#] | numeric | 3 (sugarcane) / 20 |
| 32 | `tillage_method` | Tillage method | [-] | dropdown (6 + unknown) | `unknown` (factor 1.0) |
| 33 | `anti_erosion_practice` | Anti-erosion practice | [-] | dropdown (5 + unknown) | `unknown` (factor 1.0) |
| 35 | `total_wateruse` | Total water use for irrigation | [m3] | numeric | `WaterUseDefaultGenerator` (ET matrix / efficiency x yield) |
| 38 | `yield_main_product_per_crop_cycle` | Main product | [kg FM per ha and crop cycle] | numeric | yield matrix / crop cycles |
| 40-42 | `yield_BP1..3_per_crop_cycle` | by-product (name chosen in the label cell: biowaste, coconut husk, flax seeds, mulberry, straw, waste wood untreated) | [kg FM per ha and crop cycle] | numeric | `""` (no co-product) |

**Fertilisers**

| Row | Tag | Label | Unit | Default |
|---|---|---|---|---|
| 45 | `total_fertnmin` | N total applied by mineral fertilisers | [kg N] | pre-filled **0**; if emptied: crop/country matrix `NITROGEN_FROM_MINERAL_FERT_...` |
| 46-55 | `ratio_fertnmin_{ammonia_liquid, ammonium_nitrate, an_phosphate, ammonium_sulphate, di_ammonium_phosphate, lime_ammonium_nitrate, mono_ammonium_phosphate, potassium_nitrate, urea, urea_an}` | share of N per fertiliser type | [%] | country table `FERT_N_RATIO_PER_COUNTRY` |
| 57 | `total_fertpmin` | P total | [kg P2O5] | pre-filled 0; else 0 |
| 58-64 | `ratio_fertpmin_{an_phosphate, di_ammonium_phosphate, ground_basic_slag, mono_ammonium_phosphate, hypophosphate_raw_phosphate, superphosphate, triple_superphosphate}` | | [%] | `FERT_P_RATIO_PER_COUNTRY` |
| 66 | `total_fertkmin` | K total | [kg K2O] | pre-filled 0; else 0 |
| 67-70 | `ratio_fertkmin_{patent_potassium, potassium_nitrate, potassium_salt_kcl, potassium_sulphate_k2so4}` | | [%] | `FERT_K_RATIO_PER_COUNTRY` |
| 72 | `fert_other_total_mg` | Mg total applied | [kg Mg] | 0 |
| 73 | `fert_other_dolomite_in_mg` | weight share of dolomite in Mg fertiliser | [%] | 1.0 |
| 74 | `total_fertotherca` | Ca total applied | [kg Ca] | 0 |
| 75-77 | `ratio_fertotherca_{carbonation_limestone, limestone, seaweed_limestone}` | | [%] | flat 1/3 each |
| 78 | `total_fertotherzn` | Zn total applied | [kg Zn] | 0 |
| 79-81 | `ratio_fertotherzn_{zinc_sulfate, zinc_oxide, other}` | | [%] | flat 1/3 each |
| 83-88 | `fert_other_{borax, gypsum, kaolin, manganese_sulfate, portafer, sulfite}` | | [kg] | not defaulted (absent -> not exported) |
| 90 | `total_manureliquid` | Manure, liquid | [m3] | pre-filled 0; else matrix `TOTAL_MANURE_LIQUID_...` |
| 91-94 | `ratio_manureliquid_{cattle, pig, laying_hen, other}` | | [%] | `MANURE_LIQUID_RATIO_PER_COUNTRY` |
| 95 | `total_manuresolid` | Manure, solid | [kg] | pre-filled 0; else matrix `TOTAL_MANURE_SOLID_...` |
| 96-101 | `ratio_manuresolid_{cattle, pig, sheep_goat, laying_hen, horses, other}` | | [%] | `MANURE_SOLID_RATIO_PER_COUNTRY` |
| 102-104 | `total_composttype` + 2 dropdown rows (9 compost types) | Compost and other organic fertiliser | [kg], [%] | 0; flat shares |
| 105-107 | `total_sewagesludge` + 2 dropdown rows (liquid, dehydrated, dried) | Sewage sludge | [kg], [%] | 0; flat shares |

**Pesticides**

| Row | Tag | Label | Unit | Default |
|---|---|---|---|---|
| 109 | `pest_total` | Total a.i. of any pesticide | [g] | pre-filled 0; else matrix `TOTAL_PESTICIDES_...` |
| 111-116 | `total_herbicides` + 3 dropdown rows + 2 free-text rows, `end` | | [g] | - |
| 118-123 | `total_fungicides` + 3 + 2, `end` | | [g] | - |
| 125-130 | `total_insecticides` + 3 + 2, `end` | | [g] | - |
| 132 | `pest_horticultural_oil` | Horticultural oil | [kg] | 0 |

**Machinery (diesel per operation group, share per operation)**

| Row | Tag | Unit | Default |
|---|---|---|---|
| 134 | `total_machinery_diesel` | [kg] | - (remainder -> `remains_machinery_diesel`) |
| 136-138 | `total_plantprotection` + 2 dropdown rows (Spraying, Flaming, Other) | [kg], [%] | 0; `{other: 1}` |
| 140-142 | `total_soilcultivation` + 2 rows (9 tillage operations + Other) | | 0; `{other: 1}` |
| 144-146 | `total_sowingplanting` + 2 rows (Sowing, Planting seedlings, Planting potatoes, Other; "Planting trees" exists in the dropdown but not in the Java map -> `other`) | | 0; `{other: 1}` |
| 148-150 | `total_fertilisation` + 2 rows (broadcaster, vacuum tanker, solid manure, Other) | | 0; `{other: 1}` |
| 152-154 | `total_harvesting` + 2 rows (11 operations + Other) | | 0; `{other: 1}` |
| 156-158 | `total_otherworkprocesses` + 2 rows (baling, chopping, mulching, transport, Other) | | 0; `{other: 1}` |
| 160 | `total_machinery_gazoline` | [kg] | 0 |

**Utilities, materials, greenhouse, wastes**

| Row | Tag | Unit | Default |
|---|---|---|---|
| 163-165 | `energy_electricity_{low_voltage_at_grid, photovoltaic_produced_locally, wind_power_produced_locally}` | [kWh] | none (absent -> not exported) |
| 167-177 | `energy_{diesel_excluding_diesel_used_in_tractor, lignite_briquette, hard_coal_briquette, fuel_oil_light, fuel_oil_heavy, natural_gas, wood_pellets_humidity_10_percent, wood_chips_fresh_humidity_40_percent, wood_logs, heat_district_heating, heat_solar_collector}` | [kg], [Nm3], [MJ] | none |
| 179-181 | `utilities_wateruse_{ground, surface, non_conventional_sources}` | [m3] | 0 |
| 184-187 | `materials_{fleece, silage_foil, covering_sheet, bird_net}` | [kg] | 0 |
| 189-191 | `greenhouse_{plastic_tunnel, glass_roof, plastic_roof}` | [m2] | 0 |
| 193-195 | `total_eol_plastic_disposal_fleece_and_other`, `ratio_eol_{landfill, incineration}` | [kg], [%] | sum of materials; 0.5 / 0.5 |
| 196-200 | `total_biowaste`, `ratio_biowaste_{incineration, anae_digestion, composting, other}` | [kg], [%] | 0; `{other: 1}` |
| 201-202 | `eol_waste_water_{to_treatment_facility, to_nature}` | [m3] | 0; sum of `utilities_wateruse_*` |
| 203 | `cod_in_waste_water` | [mg/L] | 0 |

Pre-filled zeros (rows 45, 57, 66, 90, 95, 109) exist so that the country/crop defaults are **not**
applied unless the user deletes the 0 (git commit 8743769 "put zero when we don't want default
values") [V].

### 3.5 Tags known to the code but absent from the template [V]

`ratio_irr_{surface_no_energy, surface_electricity, surface_diesel, sprinkler_electricity,
sprinkler_diesel, drip_electricity, drip_diesel}`, `ratio_wateruse_{ground, surface,
non_conventional_sources}` (removed from the template by commit 83c975d "remove unused water rows";
their country defaults are always used), `data_quality_*` (6 tags), `data_treatment_extrapolations`,
`data_treatment_uncertainty`, `comment`, `yearly_precipitation_as_snow` (marked DEPRECATED),
`drying_yield_to_be_dryied`, `drying_humidity_before_drying`, `drying_humidity_after_drying`
(`NumericExtractor.java:166-168`, no consumer in Python). Conversely every column-A tag in the
template is recognised by the Java reader.


---

## 4. Calculation logic

### 4.1 Orchestration, input resolution and defaults [V]

`py/modelsSequence.py:21-54`. The inputs object is

```python
DefaultValuesWrapper(ChainMap(NonStrictInputMapping(validatedInputs, EXCEL_INPUT_MAPPING_RULES),
                              self._intermediateValues, self.outputMapping.output),
                     DEFAULTS_VALUES_GENERATORS)
```

Resolution order for a key: (1) a mapping rule in `py/excelInputMappingRules.py:190-237` (rename,
enum conversion, or a `MapMappingRule` that assembles `{Enum: raw[ratio_field]}` with 0.0 for missing
members and `KeyError` if none is present); otherwise the raw Java key; (2) intermediate values
computed by previous models; (3) outputs already written; (4) the default generator in
`py/defaultGeneration.py:432-587`. Defaults are not cached and no log of default usage exists
(`defaultGeneration.py:50`, and the `#TODO: Should we log usage of default value?` in every model).

Execution order (`executeSequence`): as-is outputs -> fertiliser model (NH3, HM) -> manure model
(N, P2O5, HM, NH3) -> other organic fertiliser model (N, P2O5, HM, NH3) -> seed model (HM) ->
erosion (0 if not open ground) -> irrigation -> CO2 -> N -> P -> HM -> packaging -> LUC + land
occupation -> machinery -> waste water -> pesticides.

Key derived quantities (`defaultGeneration.py`):

| Quantity | Rule | Lines |
|---|---|---|
| `crop_cycle_per_year` | from the two harvest dates: `1 / (years + months/12 + (days // 14)/24)`; 1.0 if dates missing or incoherent | 158-173 |
| `precipitation_per_crop_cycle` [m3/ha] | `average_annual_precipitation [mm] x 10 / crop_cycle_per_year` | 242-244 |
| `yield_main_product_per_crop_cycle` | matrix yield per year / crop cycles | 247-249 |
| `yield_main_product_dry_per_crop_cycle` | `(1 - water_content[crop]) x yield` | 260-267 |
| `water_use_total` [m3/ha] | `ET[crop][country] (m3/t) / (sum share_i x eff_i) x yield / 1000`, eff = 0.45 surface, 0.75 sprinkler, 0.9 drip | 176-208 |
| `climate_zone_specific` | cool -> `snow_winter_continental`; temperate -> `warm_summer_dry_warm`; else `equatorial_summer_dry` | 137-144 |
| `soil_texture` | from clay and sand fractions (thresholds 0.18, 0.35, 0.60 clay; 0.15, 0.65 sand) | 223-239 |
| `slope` | 0.00 for rice, 0.03 otherwise; `slope_length` 50 m | 252-257, 499 |
| `nitrogen_uptake_by_crop` | matrix; pineapple = 0.02 x dry yield | 335-343 |
| `nitrogen_from_crop_residues` | see 4.5 | 374-429 |
| `CO2_from_yield` | `C_content[crop] x 44/12 x dry yield` | 270-273 |
| `energy_gross_calorific_value` | `GCV[crop] x dry yield` if in table, else `CO2_from_yield x 11.5` | 276-282 |
| `orchard_lifetime` | 3 (sugarcane) / 20 | 300-305 |
| `seed_quantities` | `{crop: nb_planted_trees | nb_seedlings | seeds}` by crop group, else 0 | 308-320 |
| `hm_land_use_category` | arable -> arable; grasslands -> permanent grassland; else horticultural | 211-220 |

### 4.2 Ammonia (NH3)

Three sources are computed separately and summed in `NModel._compute_total_due_ammonia`
(`py/models/nmodel.py:74-75`); the total is exported as `ammonia_total` (air, non-urban).

**Mineral fertilisers** - `py/models/fertilisermodel.py:197-212` [V]:

```
NH3 [kg NH3/ha] = 17/14 x sum_m  N_m x ( p x EFa[climate][m] + (1 - p) x EFb[climate][m] )
```

with `N_m = nitrogen_from_mineral_fert x share_m`, `p = soil_with_ph_under_or_7` (country table),
`climate = climate_zone_1`; for hydroponic greenhouses climate is forced to temperate and p to 1.
Emission factors `_EF_NH3N_MIN_N_FERT_PH_UNDER_OR_SEVEN` / `_PH_OVER_SEVEN` (`:75-143`), kg NH3-N
per kg N, 10 fertiliser types x 3 climates x 2 pH classes. Documented source: EMEP/EEA Guidebook
2016, chapter 3.D, Table 3-2 (model description section 2.1) [V doc]; the code has no source
comment. The 10 code values per climate match the documentation table (MAP/DAP/"other complex" =
0.04/0.06/0.05 etc.) [V]. Mapping of code types to EEA rows is implicit: `an_phosphate`,
`potassium_nitrate` -> "other complex NK, NPK", `lime_ammonium_nitrate` -> CAN, `ammonia_liquid`
-> anhydrous ammonia (code comments `:81-85`).

**Manure** - `py/models/manuremodel.py:175-179` [V]:

```
NH3 = 17/14 x ( sum_liquid  TANconc_l [kg N/m3] x V_l [m3/ha] x liquid_manure_part_before_dilution
              + sum_solid   TANconc_s [kg N/t]  x M_s [kg/ha] / 1000 )
```

`_NH3N_CONCENTRATION_IN_LIQUID_MANURE` / `_SOLID_MANURE` (`:82-94`) are written as
`TAN content x emission fraction` (e.g. cattle slurry `2.75 x 0.55`, solid cattle `1.05 x 0.79`,
horses `0.7 x 0.9`, laying hens `6.3 x 0.69`); "other" = sum-product with world proportions
(1.7765461, 2.00410305). No source comment [V]. Methodology [I]: EMEP/EEA Tier 2 manure-spreading
emission fractions of TAN; the TAN and N concentrations resemble Swiss GRUDAF values (Flisch et al.
2009 is cited in the documentation for P2O5 and N contents). `liquid_manure_part_before_dilution`
defaults to 0.5 (`defaultGeneration.py:471`), i.e. the entered slurry volume is assumed to be 50 %
undiluted manure.

**Compost and sewage sludge** - `py/models/otherorganicfertilisermodel.py:128-130` [V]:

```
NH3 = ( sum_c TAN_EF_c [kg/t] x M_c [kg/ha] + sum_s TAN_EF_s x M_s ) / 1000
```

Factors `_NH3N_CONCENTRATION_CONTENT_ORG_COMPOST/_SLUDGE` (`:79-96`) are "TAN x fraction" products,
source comment "Agribalyse Table 67 * Table 154". **The 17/14 conversion is not applied here**, so
the result is kg NH3-N but is summed with kg NH3 in `nmodel.py:75` [V inconsistency].

### 4.3 Nitrogen oxides (NOx) - `py/models/nmodel.py:80-81` [V]

```
NOx [kg NO2/ha] = N_fert_total x 0.04 x (14/30) x (46/14)        # = 0.06133 x N_fert_total
N_fert_total = nitrogen_from_all_manure + nitrogen_from_mineral_fert + nitrogen_from_other_orga_fert
```

Documentation (section 2.3): EEA 2016 3.D Table 3-1, 0.04 kg NO-N... converted to 0.018667 kg
NOx-N/kg N, "calculated after subtraction of the N volatilized as NH3", reported as NO2. **The code
does not subtract the NH3-N before applying the factor** [V discrepancy with the documentation].
Crop residue N is not included (consistent with the doc). Output key `Nox_as_n2o_air` (misnamed;
it is NOx as NO2).

### 4.4 Nitrous oxide (N2O) - `py/models/nmodel.py:83-85, 117-118` [V]

```
N2O-N_direct = 0.01 x ( N_fert_total + N_crop_residues + 14/17 x NH3_total + 14/46 x NOx_as_NO2 )
N2O [kg N2O/ha] = 44/28 x ( N2O-N_direct + 0.0075 x NO3-N_leached )
```

Documented as IPCC 2006 Tier 1 (EF1 = 0.01, EF5 = 0.0075) [V doc]. Deviations between code and
documentation: (a) the term `Nsom` (N mineralised from soil organic matter) in the documented formula
has no counterpart in the code; (b) the NH3-N and NOx-N terms are **added** to the N input in the
code (the IPCC indirect-deposition pathway EF4 = 0.01 is thus merged into the direct term with the
same factor; mathematically equivalent to EF1 = EF4 = 0.01 applied to N applied + N volatilised,
which double counts the volatilised N as both applied and redeposited) [I interpretation];
(c) the flooded-rice factor EF1FR = 0.003 mentioned in the documentation is not implemented
(`grep` finds no rice case in `nmodel.py`) [V]. For hydroponic greenhouses every N output except
NH3 is set to 0 in `OutputMapping.mapNModel` (`py/outputMapping.py:65-69`).

### 4.5 Nitrate leaching (NO3) - `py/models/nmodel.py:90-115, 120-124` [V]

```
W   [mm]     = (precipitation_per_crop_cycle + water_use_total) [m3/ha] x 0.1
Corg[kg C/ha]= organic_carbon_content [kg C/kg soil] x bulk_density_of_soil [kg/m3] x considered_soil_volume [m3/ha]
Norg[kg N/ha]= Corg / c_per_n_ratio x norg_per_ntotal_ratio
S   [kg N/ha]= N_fert_total - N2O-N_direct - 0.99 x 14/17 x NH3_total
NO3-N        = max(0, 21.37 + W / (clay_content x 100 x rooting_depth) x (0.0037 S + 0.0000601 Norg - 0.00362 U))
NO3 [kg/ha]  = NO3-N x 62/14 ;  to surface water = NO3 x drained_part ; to ground water = rest
```

with U = `nitrogen_uptake_by_crop`. Defaults: bulk density 1300 kg/m3, soil volume 5000 m3/ha,
C/N 11, rNorg 0.85, drained part 0, clay and Corg per country, rooting depth per crop
(`defaultGeneration.py:519-527`). Documented as SQCB-NO3 (Faist Emmenegger et al. 2009, after de
Willigen 2000) [V doc]; the regression coefficients 21.37 / 0.0037 / 0.0000601 / 0.00362 are
identical in doc and code. Deviations: the doc subtracts NH3, NOx **and** N2O losses from S; the
code subtracts N2O-N and 99 % of NH3-N but not NOx-N, and the factor 0.99 is unexplained [V].
The doc counts only the soluble N of organic fertilisers in S and reduces legume uptake to 40 %;
the code uses total manure N and the uptake matrix as is [V code; whether the matrix already
contains the 40 % reduction is not determinable]. The regression is applied with per-crop-cycle
water although it is documented per year [I]. Split ground/surface water by drainage is not in
the documentation (it mirrors the P model) [I].

**Nitrogen in crop residues** (`defaultGeneration.py:374-429`) [V]: for carrot, linseed, maize,
oat, peanut, potato, rapeseed, rice, soybean, sweetcorn, wheat:
`(DryYield x slope + intercept x 1000) x (N_AG x (1 - FracRemove) + R_BG x N_BG)` with crop-specific
numbers (e.g. maize 1.03 / 610 / 0.006 / 0.22 / 0.007; wheat 1.61 / 400 / 0.006 x 0.8 / 0.23 /
0.009); sugar beet `DryYield x (0.5 x 0.016 + 0.2 x 0.014)`; sugarcane `DryYield / 6 x 0.43 x 0.004`;
fixed kg N/ha for 11 vegetable/other crops (e.g. cabbage 180, lentil 76.87); 0 for all others
including all tree crops. [I] The slope/intercept/N-content values match IPCC 2006 Vol. 4
Ch. 11 Table 11.2 (the code comments cite only web sources for the newer crops).

### 4.6 Phosphorus - `py/models/pmodel.py` [V]

Land-use class per crop from `LAND_USE_CATEGORY_PER_CROP` (`defaultTables.py:1982`); yearly
averages divided by `crop_cycle_per_year`.

```
P2O5_liquid = p2o5_in_liquid_manure + p2o5_in_liquid_sludge                       # :86-87
P_gw  [kg P]  = Pgwl[class] / cycles x (1 + 0.2/80 x P2O5_liquid)                  # :89-92
PO4   = P_gw x 94.97/30.97 ; PO4_gw = PO4 x (1 - drained) ; PO4_sw_drained = (PO4 - PO4_gw) x 6   # :94-98
PO4_sw_runoff = 0 if slope < 0.03 else Prol[class] / cycles x (1 + 0.2/80 P2O5_min + 0.7/80 P2O5_liquid + 0.4/80 P2O5_solid) x 94.97/30.97   # :100-108
P_sw_erosion [kg P] = p_content_in_soil x eroded_soil_p_enrichment x eroded_reaching_river x eroded_soil / cycles   # :110-112
                    = 0.00095 x 1.86 x 0.2 x Ser / cycles
```

Tables (`:50-67`): `Pgwl` = 0.07 arable/vegetables/viticulture, 0.06 fruit trees/grassland,
0.055 alpine pastures; `Prol` = 0.175 arable/vegetables/viticulture, 0.25 fruit trees/intensive
grassland/alpine, 0.15 extensive grassland. Documented as SALCA-P (Prasuhn 2006) with 0.07/0.06
and 0.175/0.25/0.15 [V doc]; the extra classes (vegetables, viticulture, fruit trees, alpine) and
their values are not in the documentation [I: probably from Prasuhn 2006 directly]. Not documented:
the factor **6** applied to the drained fraction of leached phosphate reclassified as surface
water, the slope threshold of 3 % for run-off, and the division by crop cycles [V]. `PO4_surfacewater
= PO4_sw_drained + PO4_sw_runoff` (`outputMapping.py:77`). P2O5 inputs: manure concentrations
(`manuremodel.py:55-67`, kg P2O5/m3 and kg/t: cattle 1.5 / 2.7, pig 3.5 / 7.0, hens 17 / 25,
horses 5.0, sheep-goats 3.3, "other" world-proportion means), liquid sewage sludge 3.5 kg/t
(`otherorganicfertilisermodel.py:77`, "Walther Ryser 2001, Tab. 48"). Hydroponic -> all P outputs 0.

### 4.7 Soil erosion (USLE) - `py/models/erosionmodel.py` [V]

```
Ser [kg/(ha.yr)] = 1000 x R x K x LS x C x c2 x P                                           # :121-128
R  = f_zone(P_annual [mm], E [m], S = P_annual / nb_wet_days [mm/day])                         # :130-134, 31 formulas :75-114
LS = (slope_length x 3.28083 / 72.6)^m x (65.41 sin(s)^2 + 4.56 sin(s) + 0.065), m = 0.2/0.3/0.4/0.5 for s < 1 %, < 3.5 %, < 5 %, >= 5 %   # :136-149
C  = CROP_FACTOR_PER_CROP[crop]; K = SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE[texture]; c2 = tillage factor; P = practice factor
```

Tillage factors (`:58-64`): unknown/fall plough 1.0, spring plough 0.9, mulch 0.6, ridge 0.35,
zone 0.25, no-till 0.25. Practice factors (`:66-71`): none/unknown 1, cross slope 0.75, contour
0.5, strip cropping cross slope 0.37, strip cropping contour 0.25. K (`defaultTables.py:2776-2783`):
unknown 0.032 (Panagos et al. 2014), coarse 0.0115, medium 0.0311, medium-fine 0.0438, fine 0.0339,
very fine 0.017 (source comment: EC JRC European Soil Bureau). Documented: USLE as in Faist
Emmenegger et al. 2009, R from LANCA v2.0 (Bos et al. 2016) by climate zone, LS from Wischmeier &
Smith 1978 with `sin(S/100)`, K from Faist Emmenegger Table 7-2 / Panagos 2014, C/c2/P from Tables
7-3 to 7-5 [V doc]. The code applies `sin()` to the slope ratio exactly as the documented formula
does (ratio treated as an angle in radians) [V]. Erosion is 0 for any cultivation type other than
open ground (`modelsSequence.py:36-39`). The result is used by the P and heavy-metal models and is
not itself an ecoSpold flow.

### 4.8 Heavy metals - `py/models/hmmodel.py` [V]

For each element i in (Cd, Cu, Zn, Pb, Ni, Cr, Hg), all in mg/ha per crop cycle, then / 1e6 to kg:

```
Magro_i   = HM_manure_i + HM_mineral_fert_i + HM_other_org_i + HM_seed_i + HM_pesticide_i       # :154-159
A_i       = Magro_i / (Magro_i + Deposition_i / cycles)                                          # :161-162
Leach_i   = Leaching_i / cycles x A_i ; to surface water = x drained ; to ground water = x (1 - drained)   # :177-183
Eros_i    = SoilContent[landuse]_i x Ser / cycles x 0.86 x 0.2 x A_i                             # :185-188
Soil_i    = 0 if A_i == 0 else ( Magro_i - (Leach_i + Eros_i) / A_i ) x A_i                      # :190-193
Surface_i = Leach_i x drained + Eros_i
Soil_minus_uptake_i = Soil_i [kg] - DryYield [kg] x uptake_i      # uptake Cd 1.0154e-7 ... Hg 4.0556e-8 kg/kg   # :136-152
```

Constants: deposition mg/(ha.yr) `_HM_DEPOSITIONS` (700, 2400, 90400, 18700, 5475, 3650, 50);
leaching mg/(ha.yr) `_LEACHING_TO_GW` (50, 3600, 33000, 600, **Ni 0 "no value in src"**, 21200,
1.3); soil contents mg/kg `_SOIL_HM_CONTENT` for permanent grassland / arable / horticultural;
`_ACCUMULATION_FACTOR = 0.86`, `_EROSION_FACTOR = 0.2`; pesticides: Cu from `copper_cu` x 0.95
x 1000, Zn from mancozeb/metiram/propineb/zineb/ziram via molar Zn share x 0.95 x 1000
(`:71-88, 164-175`). Documented as SALCA-heavy metal (Freiermuth 2006): leaching Wolfensberger &
Dinkel 1997, soil contents Keller & Desaules 2001, deposition Freiermuth 2006 - the three tables in
the code match the documentation tables 2-4 [V]. **Discrepancy:** the documentation states an
accumulation factor `a = 1.86` ("according to Wilke & Schaub 1996 for P") while the code uses 0.86
[V]. The uptake coefficients (kg metal per kg dry yield) are not documented anywhere in the
repository; the documentation describes a switch parameter `heavy_metal_uptake`, which does not
exist in the ecoSpold output (the Python emits an unused string `hm_uptake_formula`) [V].

Heavy-metal inputs (all vectors ordered Cd, Cu, Zn, Pb, Ni, Cr, Hg):

- Mineral fertilisers (`fertilisermodel.py:145-190, 214-226`): mg per kg nutrient x kg nutrient;
  source comment "WLFDB Guidelines, tab. 23; Agribalyse methodology report v1.1 Table 80 for Hg";
  values match the documentation Table 6 (Desaules & Studer 1993) for the listed fertilisers;
  generic means for MAP, DAP, AN-phosphate, CAN, KNO3, liquid ammonia; Ca fertilisers use the "Lime
  kg CaO" row although the input is kg Ca [I unit mismatch]; `_HM_ZN_FERT_VALUES` puts 1e6 mg/kg at
  index 2 (Zn) for sulfate and oxide but at **index 3 (Pb) for `zn_other`** (`:189`) [V defect].
- Manure (`manuremodel.py:96-158, 184-214`): input types are redistributed to 8 Freiermuth manure
  classes (`_LIQUID/_SOLID_MANURE_TO_HM_MANURE`, e.g. liquid "other" = 0.33 cattle liquid + 0.33
  cattle slurry + 0.25 pig + 0.09 hens), then `mg/kg DM x DM share x quantity`, where solid
  quantities are converted kg -> t (x 0.001) and liquid m3 x dilution share. Because the contents
  are mg/kg DM and the quantities end up in tonnes, the result is in **g/ha**, whereas every other
  source is in mg/ha [I, arithmetic from units stated in the code comments]. DM shares and contents
  match the documentation Table 7 (laying-hen litter = mean of belt and deep-pit rows) [V].
- Compost/sludge (`otherorganicfertilisermodel.py:98-114, 132-141`): mg/kg DM x DM x kg
  (source comments: Freiermuth 2006 Table 13; vinasse without Cd/Cr/Hg; stone meal all zeros).
- Seeds (`seedmodel.py:85-170`): mg/kg DM x DM x `seed_quantities[crop]`; most crops use the
  Freiermuth generic mean (0.1, 6.6, 32, 0.54, 1.04, 0.55, 0.04); for tree and seedling crops the
  quantity is a **count of plants but is multiplied as if it were kg** [V].

Hydroponic cultivation sets all HM outputs to 0 (`outputMapping.py:105-111`).

### 4.9 CO2 from urea and liming - `py/models/co2model.py` [V]

```
CO2 = 1.57 x ( N_urea + part_of_urea_in_UAN x N_ureaAN )                  # _UREA_N_TO_CO2_FACTOR = 60/28 x 12/60 x 44/12
    + (100.09/40.08 x 44.01/100.09) x ( Ca_limestone + Ca_carbonation_limestone + Ca_seaweed_limestone )   # kg Ca -> CaCO3 -> CO2
    + (184.4/24.3 x 2 x 44/184.4) x Mg_from_fertiliser x magnesium_as_dolomite                 # kg Mg -> CaMg(CO3)2 -> 2 CO2
```

Factors are derived stoichiometrically from `py/models/atomicmass.py`. Defaults:
`part_of_urea_in_UAN` 0.5, `magnesium_as_dolomite` 1.0 (`defaultGeneration.py:507-509`).
Documented: IPCC 2006 worst case, 1.57 kg CO2/kg urea-N, 0.44 kg CO2/kg limestone, 0.48 kg
CO2/kg dolomite [V doc]; the code applies the same chemistry to Ca and Mg mass instead of product
mass, and attributes all Ca of "seaweed limestone" to CaCO3 although `outputMapping.py:92` converts
the same input to Ca(OH)2 for the product input [I inconsistency]. Exported as
`CO2_from_fertilisers` -> "Carbon dioxide, fossil".

### 4.10 Irrigation and water balance [V]

- `py/models/irrigationmodel.py:41-77`: evapotranspiration = `water_use_total x sum(share x eff)`,
  remainder split 20 % river / 80 % groundwater; exported as `wfldb_water_to_*` and **not used by
  the ecoSpold writer**.
- `OutputMapping.mapIrrigationQuantities` (`py/outputMapping.py:51-59`): the ecoSpold flows are
  `water_use_total x EI_IRR_RATIO_TO_{AIR,RIVER,GROUNDWATER}[country]` (`defaultTables.py:1928-1980`,
  14 countries + GLO 0.55 / 0.09 / 0.36; no source comment; the documentation cites Gmünder et al.
  2019, ecoinvent irrigation report) and the product input "irrigation" = `water_use_total` m3.
  Irrigation-technology and water-source shares (`IRR_TECH_RATIO_PER_COUNTRY`,
  `IRR_WATERUSE_RATIO_PER_COUNTRY`) are exported as enum keys but no ecoSpold template consumes them.

### 4.11 Land use change, occupation and transformation [V]

- `py/models/lucmodel.py:23-47`: `crop_type = _CROP_TO_CROP_TYPE[crop]` (annual / perennial /
  "Paddy rice"); `crop_specific = RELATIVE_EXPANSION[crop][country] / cycles`;
  `shared = max(0, EXPANSION_ALL_CROPS[country]) / cycles`;
  `luc_formula = "<crop_specific> * LUC_crop_specific + <shared> * (1-LUC_crop_specific)"`
  (if the crop has no entry for the country, the formula degenerates to the float `shared`).
  Java writes an intermediate exchange named `"land use change, <type> crop"` (kg) with amount 0,
  `isCalculatedAmount = true` and `mathematicalRelation = "(<luc_formula>) / <yield>"`, plus the
  dataset parameter `LUC_crop_specific = 1` (`EcospoldFileWriter.java:371-380, 665-679`). The
  emission factors themselves are therefore in the linked ecoinvent LUC dataset, not in the tool
  [I]. Tables: `_EXPANSION_ALL_CROPS_TOTAL_PER_COUNTRY` (39 countries, "country averages column
  AD", values can be negative) and `_RELATIVE_AREAS_EXPANSION_PER_CROP_PER_COUNTRY` (67 crops,
  FAOSTAT item names in comments) `lucmodel.py:50-1810`. Documented: Blonk "Direct Land Use Change
  Assessment Tool" (WFLDB-adapted 2015-06-11a), PAS 2050-1, FAOSTAT 1989-2012, 20-year amortisation,
  crop-specific (default) vs shared-responsibility allocation [V doc].
- `OutputMapping.mapLucModel` (`outputMapping.py:117-144`): occupation = `10000 / cycles` m2.yr
  to `occupation_annual_{irr|non-irr|organic_irr|organic_non-irr|greenhouse}` or
  `occupation_peren_{irr|non-irr}` (irrigated if `water_use_total > 0`); transformation from/to
  = 10000 m2 (annual) or `10000 / orchard_lifetime` (perennial). **Rice ("Paddy rice") falls in
  neither branch (`# else TODO: Rice`) and gets no occupation/transformation flows** [V].
  SOC and N2O from land management change described in the documentation (2.9.2.2) are not
  implemented in the tool [V].

### 4.12 Pesticides [V]

`RegroupPesticides` (`excelInputMappingRules.py:181-187`) collects every raw `part_herbicides_*`,
`part_fungicides_*`, `part_insecticides_*` key (g/ha). `OutputMapping.mapPesticides`
(`outputMapping.py:153-168`) exports `pesti_<key>` (g) and `pestikg_<key>` (kg) plus
`pest_remains[_kg]` and `remains_{herbicides,fungicides,insecticides}[_kg]` (totals not detailed by
substance, computed by the Java reader). Java (`EcospoldFileWriter.java:267-283, 425-503`) creates
for each `pestikg_*`: an intermediate input (product from
`ecospold_pesticides_product_mapping.properties`, e.g. `pesti_herbicides_2_4_d=2,4-dichlorotoluene`,
uncertainty PESTICIDES_MANUFACTURING) and, unless the key ends with `_other`/`_unspecified`, an
elementary emission of 100 % of the amount to **soil, agricultural** (substance from
`ecospold_pesticides_substance_mapping.properties`, uncertainty PESTICIDES_EMISSION_TO_SOIL).
Remainders map to "pesticide, unspecified" without emission; horticultural oil maps to "naphtha"
input and "Mineral oil" emission to agricultural soil. Documented: 100 % of active ingredient to
agricultural soil (2.10) [V doc].

### 4.13 Other outputs [V]

- **Packaging** (`py/models/packmodel.py`): fertiliser mass = N + P2O5 + K2O + Mg + Ca + Zn (kg
  nutrient!), liquid = liquid ammonia N, solid = rest; pesticides = `pest_total` / 1000 all liquid;
  `ecoinvent_packaging_liquid = pest_liq x 3 + fert_liq x 2 + horticultural oil`,
  `ecoinvent_packaging_solid = pest_solid x 3 + fert_solid x 2` -> "packaging, for fertilisers or
  pesticides". No source; `wfldb_packaging_*` unused.
- **Waste water** (`outputMapping.py:146-151`): `COD [kg] = eol_waste_water_to_nature [m3] x
  cod [mg/L] x 0.001`; DOC = TOC = COD / 2.7; BOD5 = 0.5 x COD (documented, 2.6). Emitted to
  **ground water** in Java (`EcospoldTemplateSubstanceUsages.java:183-194`) although the water
  volume itself goes to surface water (`:180-182`).
- **CO2 uptake / energy** (4.1): "Carbon dioxide, in air" and "Energy, gross calorific value, in
  biomass" as resources (documented 2.12; the code uses a per-crop C content table from "GD_crop"
  rather than the 47.5 % default).
- **Machinery** (`outputMapping.py:170-178, 246-300`): diesel kg per operation group x share, then
  divided by a diesel intensity per ecoinvent operation dataset (e.g. plough 26.1 kg/ha, combine
  33.3 kg/ha, spraying 1.76 kg/ha, vacuum tanker 0.217 kg/m3, bale loading 0.0811 kg/unit,
  tractor-trailer transport 0.0436 kg/tkm); "other" and `remains_machinery_diesel` x 45.00450045
  MJ/kg to "diesel, burned in agricultural machinery"; petrol / 0.022075 (kg -> MJ). No source
  comment [I: ecoinvent machinery datasets' diesel inputs].
- **Energy** (`outputMapping.py:208-224`): fuel masses converted to MJ with 1/0.111 (lignite),
  1/0.0318 (hard coal), 1/0.02342 (light fuel oil), 1/0.025 (heavy), 1/0.0272 (natural gas, Nm3),
  1/0.0587, 1/0.0545, 1/0.0643 (wood pellets, chips, logs); diesel x 45.00450045; no source
  comment [I: lower heating values listed in the template's User Guidance].
- **Seeds, trees, trellis** (`outputMapping.py:36-45`): tree crops: `seeds_<crop> =
  nb_planted_trees / orchard_lifetime`, `rooting_up_trees = 1 / lifetime` (unused by Java),
  `need_trellis = 1` if >= 500 trees/ha -> "trellis system, wooden poles ..." (ha).
- **Greenhouses** (`outputMapping.py:23-26`): plastic tunnel m2 / 25 / orchard_lifetime; glass and
  plastic greenhouse m2 / orchard_lifetime (i.e. the 20-year default lifetime is reused as
  greenhouse lifetime) [V].
- **Metadata**: `record_entry_by`, `collection_method`, `comment` are exported by Python but
  **never written to the ecoSpold2 file** (only the legacy SCSV writer uses them) [V].

### 4.14 Documented methodology per model (summary)

| Model | Code | Source comment in code | Documented source (model description 2018) | Status |
|---|---|---|---|---|
| NH3 mineral | `fertilisermodel.py` | none | EMEP/EEA 2016, 3.D Tab. 3-2 | values match [V] |
| NH3 manure | `manuremodel.py` | none | "EMEP/EEA" (summary table only) | [I] EMEP/EEA Tier 2 TAN fractions, Swiss contents |
| NH3 compost/sludge | `otherorganicfertilisermodel.py` | Agribalyse Tab. 67 x 154 | - | no N->NH3 conversion [V] |
| NOx | `nmodel.py` | "0.04 is a ratio in kg NO/kg N" | EEA 2016 3.D Tab. 3-1 | NH3 not subtracted [V] |
| N2O | `nmodel.py` | none | IPCC 2006 Tier 1 | no Nsom, no rice EF [V] |
| NO3 | `nmodel.py` | none | SQCB-NO3 (Faist Emmenegger 2009) | coefficients match; S definition differs [V] |
| N crop residues | `defaultGeneration.py` | web links for new crops | - | [I] IPCC 2006 Tab. 11.2 |
| P | `pmodel.py` | none | SALCA-P (Prasuhn 2006) | extra classes, x6 drained factor, slope rule undocumented |
| Erosion | `erosionmodel.py` | none | USLE, LANCA R, Panagos K | consistent [V] |
| Heavy metals | `hmmodel.py`, inputs in 4 models | WFLDB Tab. 23, Agribalyse Tab. 80, Freiermuth 2006 Tab. 7/13, Walther Ryser 2001 | SALCA-HM (Freiermuth 2006) | accumulation factor 0.86 vs 1.86 [V]; uptake factors unsourced |
| CO2 urea/lime | `co2model.py` | stoichiometry | IPCC 2006 | consistent for urea; Ca/Mg basis differs |
| Irrigation split | `defaultTables.py` EI_IRR | none | Gmünder et al. 2019 | values not verifiable here |
| LUC | `lucmodel.py` | FAOSTAT item names | Blonk tool 2014 / PAS 2050-1 / WFLDB | only area ratios in the tool |
| Pesticides | `outputMapping.py` + Java | - | 100 % to agricultural soil | consistent [V] |
| COD/BOD | `outputMapping.py` | none | doc 2.6 | consistent [V] |

---

## 5. Hardcoded values

Everything below is embedded in source code or resource files and is a candidate for migration to
`C:\python\AgriToolV.1\data\*.csv` with a `sources.csv` entry. "Source" is what the code or
documentation says; blank means nothing is stated.

### 5.1 Python model constants (`py/models/`)

| # | Location | Name | Dimensions / unit | Source stated | Suggested CSV |
|---|---|---|---|---|---|
| 1 | `fertilisermodel.py:75-143` | `_EF_NH3N_MIN_N_FERT_PH_UNDER_OR_SEVEN`, `_PH_OVER_SEVEN` | 10 N-fertiliser types x 3 climates x 2 pH classes, kg NH3-N/kg N | doc: EMEP/EEA 2016 3.D Tab. 3-2 | `ef_nh3_mineral_fertiliser.csv` |
| 2 | `fertilisermodel.py:147-190` | `_HM_N/P/K/CA/ZN_FERT_VALUES` | 27 fertiliser types x 7 metals, mg/kg nutrient | WFLDB tab. 23; Agribalyse v1.1 Tab. 80 (Hg); doc Tab. 6 | `hm_content_mineral_fertiliser.csv` |
| 3 | `manuremodel.py:55-94` | `_P205_`, `_N_`, `_NH3N_CONCENTRATION_IN_LIQUID/SOLID_MANURE` | 4 liquid (kg/m3) + 6 solid (kg/t) types; NH3-N given as TAN x fraction | none ("Sumprod ... world proportions" for other) | `manure_nutrient_content.csv`, `ef_nh3_manure.csv` |
| 4 | `manuremodel.py:96-158` | `_LIQUID/_SOLID_MANURE_TO_HM_MANURE`, `_HM_MANURE_DM`, `_HM_MANURE_VALUES` | 10 input types -> 8 Freiermuth classes; DM share; 8 x 7 metals mg/kg DM | doc Tab. 7 (Menzi & Kessler 1998; Desaules & Studer 1993; Walther 2001) | `hm_content_manure.csv`, `manure_type_mapping.csv` |
| 5 | `otherorganicfertilisermodel.py:40-114` | `_COMPOST_DM`, `_SLUDGE_DM`, `_N_CONCENTRATION_ORG_*`, `_P205_..._SLUDGE`, `_NH3N_..._*`, `_HM_COMPOST/SLUDGE_VALUES` | 9 compost + 3 sludge types | Freiermuth 2006 Tab. 13; Walther Ryser 2001 Tab. 48; Agribalyse Tab. 67 x 154; WFLDB | `organic_fertiliser_properties.csv`, `hm_content_organic_fertiliser.csv` |
| 6 | `seedmodel.py:15-155` | `_SEED_DM`, `_HM_SEED_VALUES` | 67 crops; DM share; 7 metals mg/kg DM | Freiermuth 2006 Tab. 7 | `seed_properties.csv` |
| 7 | `nmodel.py:80-118` | 0.04 (NO), 0.01 (EF1), 0.0075 (EF5), 0.99, 21.37, 0.0037, 0.0000601, 0.00362, 0.1 (m3/ha -> mm) | scalars | doc: EEA 2016, IPCC 2006, SQCB | `parameters_nitrogen.csv` |
| 8 | `pmodel.py:50-67, 89-112` | `_AVERAGE_GROUND_WATER_P_LOSS_PER_LAND`, `_AVERAGE_RUNOFF_P_LOSS_PER_LAND`; 0.2/80, 0.7/80, 0.4/80, 6, 0.03 | 7 land-use classes, kg P/(ha.yr) | doc: Prasuhn 2006 (partial) | `parameters_phosphorus.csv` |
| 9 | `hmmodel.py:60-108, 136-152` | `_HM_DEPOSITIONS`, `_LEACHING_TO_GW`, `_SOIL_HM_CONTENT`, `_ACCUMULATION_FACTOR` 0.86, `_EROSION_FACTOR` 0.2, `_PEST_TO_SOIL_RATIO` 0.95, `_PEST_MW`, `_PEST_NB_ZN_ATOMS`, `_ZINC_MW`, 7 uptake coefficients | 7 metals; 3 land uses; 5 Zn fungicides | doc Tab. 2-4 (Freiermuth 2006; Wolfensberger & Dinkel 1997; Keller & Desaules 2001); uptake: none | `hm_deposition_leaching.csv`, `hm_soil_content.csv`, `hm_uptake.csv`, `zn_fungicides.csv` |
| 10 | `erosionmodel.py:53-114` | slope exponents, `_TILLAGE_METHOD_FACTOR`, `_ANTI_EROSION_PRACTICE_FACTOR`, `_EROSITIVITY_FACTOR_FORMULAE` (31 zones), LS constants 3.28083/72.6/65.41/4.56/0.065 | | doc: Faist Emmenegger 2009 Tab. 7-3..7-5; LANCA (Bos et al. 2016); Wischmeier & Smith 1978 | `erosion_factors.csv`, `r_factor_equations.csv` (coefficients per zone and equation form) |
| 11 | `irrigationmodel.py:32-34, 75-76` and duplicate in `defaultGeneration.py:185-187` | efficiencies 0.45 / 0.75 / 0.9; split 0.2 / 0.8 | | | `irrigation_efficiency.csv` |
| 12 | `co2model.py:26-30` | stoichiometric factors (derived from `atomicmass.py`) | | doc: IPCC 2006 | keep computed from `atomic_masses.csv` |
| 13 | `atomicmass.py` | 9 atomic masses, molar masses, 14 conversion factors | | | `atomic_masses.csv` |
| 14 | `packmodel.py:32-34` | dilution factors 2.0, 2.0, 3.0 | | | `packaging_factors.csv` |
| 15 | `lucmodel.py:50-1880` | `_EXPANSION_ALL_CROPS_TOTAL_PER_COUNTRY` (39), `_RELATIVE_AREAS_EXPANSION_PER_CROP_PER_COUNTRY` (67 crops x 3-38 countries), `_CROP_TO_CROP_TYPE` (67) | ratios | "country averages column AD"; FAOSTAT item names | `luc_expansion_country.csv`, `luc_expansion_crop_country.csv`, `crop_type.csv` |
| 16 | `defaultGeneration.py:374-429` | crop-residue coefficients for 25 crops | | web links | `crop_residue_n.csv` |
| 17 | `defaultGeneration.py:432-587` | scalar defaults (180 wet days, 700 m, 1300 kg/m3, 11, 5000 m3, 0.85, 0.5 UAN, 1.0 dolomite, 0.5 dilution, 50 m, 0.2, 1.86, 0.00095, 20/3 years, 0.5/0.5 plastic EoL, ...) | | doc for N model values | `default_parameters.csv` |

### 5.2 Default tables (`py/defaultTables.py`, `py/defaultMatrix*.py`)

| Table | Lines | Keys | Unit | Source comment |
|---|---|---|---|---|
| `CARBON_CONTENT_PER_CROP` | 18-88 | 67 crops | kg C/kg DM | "GD_crop GrossEnergy_C_L1"; biogeosciences-discuss bg-2017-322 for 2018 crops |
| `ANNUAL_PRECIPITATION_PER_COUNTRY` | 90-131 | 39 countries | mm/yr | GD_crop precipitation_L1 |
| `CLAY_CONTENT_PER_COUNTRY` | 133-184 | 39 | fraction | GD_crop SoilTypes_L1 |
| `CROP_FACTOR_PER_CROP` | 186-265 | 67 | USLE C | GD_crop; CORINE C-factor table (link) |
| `ENERGY_GROSS_CALORIFIC_VALUE_PER_CROP_PARTIAL` | 267-306 | 37 | MJ/kg DM | ecoinvent report no. 15a |
| `FERT_K_RATIO_PER_COUNTRY` | 308-544 | 39 x 4 | share | GD_crop |
| `FERT_N_RATIO_PER_COUNTRY` | 546-1016 | 39 x 10 | share | GD_crop MineralFertiliser_L1 |
| `FERT_P_RATIO_PER_COUNTRY` | 1018-1372 | 39 x 7 | share | GD_crop |
| `IRR_TECH_RATIO_PER_COUNTRY` | 1374-1728 | 39 x 7 | share | GD_crop IrrTechn_L0/L1 |
| `IRR_WATERUSE_RATIO_PER_COUNTRY` | 1730-1926 | 39 x 3 | share | GD_crop IrrWaterSource_L1 |
| `EI_IRR_RATIO_TO_AIR/_RIVER/_GROUNDWATER` | 1928-1980 | 14 + GLO | share | none (doc: Gmünder et al. 2019) |
| `LAND_USE_CATEGORY_PER_CROP` | 1982-2051 | 67 | enum | none |
| `MANURE_LIQUID_RATIO_PER_COUNTRY` | 2053-2289 | 39 x 4 | share | GD_crop OrgFertiliser_L1 |
| `MANURE_SOLID_RATIO_PER_COUNTRY` | 2291-2617 | 39 x 6 | share | GD_crop OrgFertiliser_L1 |
| `ROOTING_DEPTH_PER_CROP` | 2619-2688 | 67 | m | GD_crop RootingDepth; FAO ecocrop; "ask Sämi" |
| `SAND_CONTENT_PER_COUNTRY` | 2690-2731 | 39 | fraction | GD_crop SoilTypes_L1 |
| `SOIL_CARBON_CONTENT_PER_COUNTRY` | 2733-2774 | 39 | kg C/kg | GD_crop HumusCcontent_L1 |
| `SOIL_ERODIBILITY_FACTOR_PER_SOIL_TEXTURE` | 2776-2783 | 6 | t.h/(MJ.mm) | JRC European Soil Bureau; Panagos 2014 |
| `SOIL_WITH_PH_UNDER_OR_7_PER_COUNTRY` | 2786-2836 | 39 | fraction | GD_crop Soil_pH_L0 |
| `WATER_CONTENT_FM_RATIO_PER_CROP` | 2838-2907 | 67 | kg water/kg FM | GD_crop WaterNutrient_L1; FAO links |
| `YEARLY_PRECIPITATION_AS_SNOW_PER_COUNTRY` | 2909-2949 | 39 | fraction | GD_crop (deprecated) |
| `YIELD_PER_YEAR_PER_CROP_PER_COUNTRY` | `defaultMatrixYieldPerYear.py` | 67 x countries + GLO | kg/(ha.yr) | GD_crop Yield_2009_2012_L1 [I FAOSTAT 2009-2012] |
| `NITROGEN_UPTAKE_PER_CROP_PER_COUNTRY` | `defaultMatrixNUptake.py` | 67 x countries + GLO | kg N/ha | GD_crop Nuptake_L1; doc Annex 3; web sources |
| `EVAPO_TRANSPI_PER_CROP_PER_COUNTRY` | `defaultMatrixEvapoTranspiration.py` | 67 x countries + GLO | m3/t | GD_crop ETirr_m3t_L1; "Pfister file" |
| `NB_SEEDS_/NB_SEEDLINGS_/NB_PLANTED_TREES_PER_PARTIAL_CROP_PER_COUNTRY` | `defaultMatrixSeed.py` | 25 / 15 / 26 crops, GLO only | kg/ha, #/ha, (empty) | GD_crop Seeds_L0 etc. |
| `TOTAL_MANURE_LIQUID/SOLID_PER_CROP_PER_COUNTRY` | `defaultMatrixTotalManure.py` | 67 x countries | m3/ha, kg/ha | GD_crop ManureLiquid/Solid_L1 |
| `NITROGEN_FROM_MINERAL_FERT_PER_CROP_PER_COUNTRY` | `defaultMatrixTotalMineralFert.py` | 67 x countries | kg N/ha | GD_crop NMineral_L1 |
| `TOTAL_PESTICIDES_PER_CROP_PER_COUNTRY` | `defaultMatrixTotalPesticides.py` | 67 x countries | g/ha | GD_crop Pesticides_L1 |

"GD_crop" is an internal Quantis Excel workbook (the Python files even contain the Excel formulas
used to generate them, e.g. `=MOYENNE(B4:AM4)` for GLO); it is not in the repository [V].

### 5.3 Output mapping conversion factors (`py/outputMapping.py`)

Lines 188-237 (`_DIRECT_OUTPUT_MAPPING`): fuel LHV-type divisors (0.111, 0.0318, 0.02342, 0.025,
0.0272, 0.0587, 0.0545, 0.0643), diesel 45.00450045 MJ/kg, petrol 0.022075, fleece 0.017 kg/m2,
water 1000 kg/m3. Lines 239-300: liquid manure density 1006 kg/m3; machinery diesel intensities for
38 operations. Lines 89-99: Zn sulfate formula `Zn x ZnO/Zn / (0.478 - 0.00478 x ZnO/Zn)` (unexplained);
CaCO3, Ca(OH)2, MgSO4, dolomite stoichiometry. Lines 23-26: plastic tunnel lifetime 25. Lines 147-151:
COD factors 2.7 and 0.5. Line 42: trellis threshold 500 trees/ha. -> `unit_conversions.csv`,
`machinery_diesel_intensity.csv`.

### 5.4 Java constants and resources

| Location | Content | Suggested CSV |
|---|---|---|
| `java/ecospold/StandardUncertaintyMetadata.java` | 25 uncertainty classes: pedigree matrix (e.g. 2,1,1,1,1), basic variance, variance with pedigree (lognormal) | `uncertainty_classes.csv` |
| `java/scsv/StandardUncertaintyMetadata.java` | duplicate of the above for the SCSV path | drop |
| `java/ecospold/EcospoldTemplateSubstanceUsages.java:1-27` | 20 subcompartment UUIDs (ecoinvent) | `subcompartments.csv` |
| `java/ecospold/AvailableUnit.java` | 66 unit UUIDs and symbols | `units.csv` |
| `java/ecospold/EcospoldTemplateSubstanceUsages.java:53-223` | 60 elementary flow templates (name, subcompartment, unit, variable, uncertainty class) | `elementary_flow_mapping.csv` |
| `java/ecospold/EcospoldTemplateIntermediaryExchanges.java:27-1003` | 238 intermediate exchange templates (product name, unit, variable, uncertainty class, comment variable, 2 activity-name UUIDs) | `intermediate_exchange_mapping.csv` |
| `java/EcospoldFileWriter.java:32-75` | system model UUID, macro-economic scenario UUID, placeholder person UUID, file attributes 3.4, context UUID, soil-agricultural UUID `e1bc9a16-...` (`:482`), GLO UUID in `PossibleActivityLinkCache.java:97` | `ecospold_metadata.csv` |
| `java/imports/NumericExtractor.java`, `StringFromListExtractor.java`, `LabelForBlockTags.java`, `DateExtractor.java`, `StringExtractor.java` | template tag lists, dropdown label -> code maps (climate zones, cultivation types, tillage, anti-erosion, compost, sludge, operations) | `template_fields.csv`, `dropdown_vocabulary.csv` |
| `java/imports/ExcelInputReader.java:49-53` | pesticide and machinery aggregation groups | idem |
| `src/main/resources/crops.properties`, `countries.properties` | 67 crop codes/labels, 39 country codes/names | `crops.csv`, `countries.csv` |
| `herbicides/fungicides/insecticides.properties` | 140 / 102 / 106 active-ingredient keys and labels | `pesticide_active_ingredients.csv` |
| `ecospold_activity_name_mapping.properties`, `ecospold_main_output_mapping.properties` | crop -> ecoinvent activity name and reference product | `crop_ecoinvent_names.csv` |
| `ecospold_pesticides_product_mapping.properties`, `ecospold_pesticides_substance_mapping.properties` | 348 / 342 pesticide key -> product / elementary flow name | `pesticide_mapping.csv` |
| `pesticides_product_mapping.properties`, `pesticides_substance_mapping.properties` | SimaPro/WFLDB names (legacy) | drop |
| `ecospold/ecospold_geo_mapping.txt` (477 lines), `ecospold_geography_intersections.csv` (2437 lines) | geography UUID + shortname -> code; geography containment pairs | `geographies.csv`, `geography_intersections.csv` |
| `py/directMappingEnums.py`, enums in `models/*.py` | vocabularies for fertiliser, manure, compost, sludge, irrigation, machinery, waste types | `vocabularies.csv` |


---

## 6. Output: ecoSpold2 generation

### 6.1 Library and schema [V]

- XML is produced by `javax.xml.bind.JAXB.marshal(res, writer)` (`java/EcospoldFileWriter.java:302`)
  from the object model in the proprietary jar `lib/com/quantis_intl/common-formats/0.0.3/`
  (package `com.quantis_intl.commons.ecospold2.ecospold02`, namespace
  `http://www.EcoInvent.org/EcoSpold02`, i.e. the ecoSpold v2 format; roughly 120 generated `T*`
  classes). No XSD is in the repository and no schema validation is performed; the Bean-Validation
  block is commented out (`:297-300`).
- `fileAttributes`: majorRelease 3, minorRelease 4, revisions 1/1, context "ecoinvent"
  (`:69-75`). This is an ecoinvent release label chosen in 2018, not a schema version.
- Output: one `EcoSpold` root with `usedUserMasterData` (new activity names / intermediate
  exchanges when not found in master data) and one `activityDataset` (`:128-132`). File name:
  `<uploaded name>.spold` (`Api.java:302-310`; the `Content-Disposition` header has a typo
  "attachement" and a missing closing quote).

### 6.2 Master data and lookups [V]

All identifiers come from ecoinvent master-data XML files loaded at startup from the
uploaded-files folder (section 2.2):

| Cache (`java/ecospold/`) | File | Lookup key | Used for |
|---|---|---|---|
| `PossibleElementaryExchangesCache` | `ElementaryExchanges.xml` | (subcompartment UUID, flow name) -> `TValidElementaryExchange` (id, compartment, unit, properties) | every elementary flow |
| `PossibleIntermediateExchangesCache` | `IntermediateExchanges.xml` | product name -> `TValidIntermediateExchange` (id, unit, classification, properties) | reference product, co-products, all inputs |
| `PossibleActivityNamesCache` | `ActivityNames.xml` | activity name -> activityNameId | dataset activity name |
| `PossibleActivityLinkCache` | `ActivityIndex.xml` (lazy, per activityNameId) + `ecospold_geography_intersections.csv` + `countries.properties` | (activityNameId, country) -> provider dataset id | only PV and wind electricity inputs |
| `PossiblePropertyCache` | `Properties.xml` | property UUID -> name, unit | properties copied onto exchanges |
| `PossibleParametersCache` | `Parameters.xml` | name -> `TValidParameter` | the `LUC_crop_specific` parameter |
| `GeographyMappingCache` | classpath `ecospold_geo_mapping.txt` | country code -> `TGeography(UUID, shortname)` | dataset geography and provider search |
| `CropsEcospoldRefsCache` | classpath properties | crop code -> activity name, reference product name | dataset header |

Flow and product **names must match the master data exactly**; a missing name is printed with
`System.out.println("ERROR: ...")` and the exchange is dropped from the file without any
user-visible warning (`EcospoldFileWriter.java:393-397, 441-446, 484-488, 524-528`). A unit
mismatch with master data is also only printed (`:400-402, 532-534`).

### 6.3 Dataset header and identifiers [V]

| Element | Value / rule | Lines |
|---|---|---|
| Activity name | `ecospold_activity_name_mapping[crop]` (e.g. `almond production`) + `", organic"` if `organic_certified = yes`; no greenhouse suffix (`//FIXME`) | 146-150 |
| Activity `id` | UUID v5 (SHA-1, DNS namespace, `UUIDType5.java`) of `activityName + country + "<year-3>-01-01" + "<year>-12-31"` -> deterministic but **changes every calendar year** | 152-156 |
| `activityNameId` | from `ActivityNames.xml`, else UUID v5 of the name and an entry in `usedUserMasterData` | 158-165 |
| Geography | `ecospold_geo_mapping.txt[country]` | 135 |
| Time period | `(current year - 3)-01-01` to `current year-12-31`, `isDataValidForEntirePeriod = true` | 138-143 |
| Technology | empty `TTechnology` | 136 |
| Macro-economic scenario | "Business-as-Usual" `d9f57f0a-...` | 45-47 |
| General comment | `"Yield (kg): <yield>"`, `"Generated by ?"` | 171-172 |
| Type | 1 (unit process) | 173 |
| Classification, tags, synonyms, includedActivitiesStart | not set | 170, 174-175 |
| Modelling and validation | system model "Undefined" `8b738ea0-...`, sampling procedure "Literature data and manufacturer information", extrapolations "none" | 61-67 |
| Data entry / generator | person `788d0176-...` "[Current User]" `no@email.com`, copyright protected, access restricted 1 | 49-59 |
| Exchange `id` | `UUID.randomUUID()` for every exchange -> two runs on the same input give different files | 188, 324, 369, 430, 469, 510 |

### 6.4 Reference product and co-products [V]

- Reference product: `ecospold_main_output_mapping[crop]` (+ organic suffix), 1 kg, `outputGroup 0`;
  id from `IntermediateExchanges.xml` or UUID v5 + user master data (`:180-211`).
- Co-products: `yield_BP1..3_per_crop_cycle` with the Excel **label text** as product name (dropdown:
  biowaste, coconut husk, flax seeds, mulberry, straw, waste wood untreated), amount `yield_BP /
  yield_main`, `outputGroup 2`, no allocation properties (`:213-229, 317-355`).

### 6.5 Intermediate exchanges (inputs and wastes) [V]

Built by `buildIntermediateExchange` (`:363-423`) from the static arrays in
`java/ecospold/EcospoldTemplateIntermediaryExchanges.java` (238 entries: product name, unit, output
variable, uncertainty class, comment variable). Amount = `output[variable] / yield`; zero amounts
are skipped; `inputGroup 5`; classification and properties copied from master data; comment from
the Excel comment cell of `commentVariable`; wastes get `outputGroup 3` instead (`:239-247`).
Only the two `WithActivityIdTemplateIntermediaryExchange` entries (PV `6ddf5188-...`, wind
`2d9e8e52-...`) receive an `activityLinkId`, resolved per country by walking the geography
containment graph and falling back to GLO (`PossibleActivityLinkCache.java:48-106`). All other
inputs are unlinked market/product references.

Mapping summary (full list in the Java file; representative rows):

| Group | Variable(s) | ecoinvent product (unit) | Notes |
|---|---|---|---|
| Seeds, kg | `seeds_<crop>` | crop-specific seed products: wheat, maize, rice, soybean, sunflower, rapeseed, sugar beet, carrot, cotton, oat, pea, peanut, potato, linseed (kg) | proxies: cassava/turmeric -> "potato seed, at farm"; castor, coriander, flax, hemp, sesame -> "linseed seed, at farm"; guar -> soybean seed; lentil -> peanut seed; pearl millet -> wheat seed; chick pea -> pea seed |
| Seedlings, unit | `seeds_<crop>` | "onion seedling, for planting" (bellpepper, cabbage, chilli, eggplant, ginger, onion), "tomato seedling", "strawberry seedling" (strawberry, raspberry), "asparagus seedling", "mint seedling" | |
| Trees, unit | `seeds_<crop>` (= trees / orchard lifetime) | three exchanges each: "fruit tree seedling, for planting", "planting tree", "establishing orchard" | also used for sugarcane, tea, grape, pineapple, banana |
| Irrigation | `water_use_total` | "irrigation" (m3) | |
| N fertilisers | `fert_n_*` (kg N) | "ammonium nitrate, as N", "urea, as N", "ammonium sulfate, as N", "ammonia, liquid" (as NH3), "nitrogen fertiliser, as N" for UAN, MAP, DAP, AN-phosphate, CAN, KNO3 | |
| P fertilisers | `fert_p_*` (kg P2O5) | "phosphate fertiliser, as P2O5"; "phosphate rock, as P2O5, beneficiated, dry" for raw phosphate | |
| K fertilisers | `fert_k_*` (kg K2O) | "potassium chloride, as K2O" (KCl and patent potassium), "potassium sulfate, as K2O", "potassium fertiliser, as K2O" (KNO3) | |
| Ca, Mg, Zn, others | `*_as_limestone`, `*_as_seaweed_lime`, `*_as_mgso4`, `*_as_dolomite`, `*_as_zincsulfate`, `*_as_zincoxide`, `fert_other_*` | "lime", "magnesium sulfate", "dolomite", "zinc monosulfate", "zinc oxide", "kaolin", "manganese sulfate", "gypsum, mineral", "sulfite", "portafer", "borax, anhydrous, powder" | masses converted stoichiometrically in Python |
| Manure | `liquid_manure_*` (m3 x 1006 -> kg), `solid_manure_*` (kg) | "manure, liquid, cattle" (cattle, other), "manure, liquid, swine" (pig liquid **and solid**), "poultry manure, fresh", "manure, solid, cattle" (cattle, sheep/goat, horses, other), "poultry manure, dried" | |
| Compost, sludge | `composttype_*` | "compost", "vinasse, from fermentation of sugar beet", "poultry manure, dried", "stone meal", "horn meal" (horn meal, horn shavings); meat-and-bone meal, castor shell, feather meal and all sewage sludge types have **no product mapping** | |
| Field work | `<group>_<operation>` (ha, m3, kg, unit, tkm) | "tillage, ploughing", "combine harvesting", "sowing", "fertilising, by broadcaster", "liquid manure spreading, by vacuum tanker", "application of plant protection product, by field sprayer", ...; `*_other` and `remains_machinery_diesel` -> "diesel, burned in agricultural machinery" (MJ); flaming -> "heat, central or small-scale, natural gas" | |
| Energy | `energy_*` | "electricity, low voltage" (grid, PV), "electricity, high voltage" (wind), "heat, central or small-scale, natural gas / other than natural gas", "heat, district or industrial, ..." (MJ); "petrol, unleaded, burned in machinery" | |
| Water, materials, greenhouse | `utilities_wateruse_non_conventional_sources` (kg), `materials_*`, `greenhouse_*`, `need_trellis` | "tap water", "horticultural fleece" (m2), "polyethylene, high density, granulate", "plastic tunnel" (m2), "greenhouse, glass/plastic walls and roof" (m2.yr), "trellis system, wooden poles, soft wood, tar impregnated" (ha) | |
| Pesticides | `pestikg_*`, `pest_remains_kg`, `remains_*_kg`, `pest_horticultural_oil` | product per active ingredient from the properties file; "pesticide, unspecified"; "naphtha" | |
| Packaging | `ecoinvent_packaging_solid/liquid` | "packaging, for fertilisers or pesticides" | |
| LUC | `luc_formula` | "land use change, annual crop" / "land use change, perennial crop" (kg), amount 0, mathematical relation | |
| Wastes (`outputGroup 3`) | `eol_plastic_*`, `eol_biowaste_*`, `eol_waste_water_to_treatment_facility` | "waste polyethylene", "biowaste", "wastewater, average" (m3) | |

### 6.6 Elementary exchanges [V]

Built by `buildElementaryExchange` (`:505-549`) from `java/ecospold/EcospoldTemplateSubstanceUsages.java`
(60 entries). Lookup by (subcompartment UUID, name); amount = `output[variable] / yield`; zero or
missing variables skipped; `inputGroup 4` if the compartment is "natural resource", else
`outputGroup 4`; properties copied from master data.

| Flow name | Subcompartment (UUID constant) | Unit | Output variable | Uncertainty class |
|---|---|---|---|---|
| Carbon dioxide, in air | natural resource / in air (`RESOURCE_IN_AIR`) | kg | `CO2_from_yield` | CO2_ENERGY_BIOMASS |
| Energy, gross calorific value, in biomass | natural resource / biotic | MJ | `energy_gross_calorific_value` | CO2_ENERGY_BIOMASS |
| Water, river | natural resource / in water | m3 | `utilities_wateruse_ground` **and** `utilities_wateruse_surface` | UTILITIES_WATER |
| Occupation, annual crop, non-irrigated / irrigated / greenhouse; permanent crop, irrigated / non-irrigated | natural resource / land | m2.yr | `occupation_annual_[organic_]{irr,non-irr}`, `occupation_annual_greenhouse`, `occupation_peren_{irr,non-irr}` | LAND_OCCUPATION |
| Transformation, from/to annual crop {irrigated, non-irrigated, greenhouse}; from/to permanent crop {irrigated, non-irrigated} | natural resource / land | m2 | `transformation_{from,to}_{annual,peren}_*` | LAND_TRANSFORMATION |
| Ammonia | air / non-urban air or from high stacks | kg | `ammonia_total` | CH4_NH3_TO_AIR |
| Carbon dioxide, fossil | air / non-urban | kg | `CO2_from_fertilisers` | CO2_EMISSIONS |
| Nitrogen oxides | air / non-urban | kg | `Nox_as_n2o_air` | N2O_NOX_TO_AIR |
| Dinitrogen monoxide | air / non-urban | kg | `N2o_air` | N2O_NOX_TO_AIR |
| Water | air / non-urban | m3 | `ecoinvent_water_to_air` | CH4_NH3_TO_AIR (`//FIXME: Not the right ...`) |
| Nitrate | water / surface water; water / ground- | kg | `nitrate_to_surfacewater`, `nitrate_to_groundwater` | NO3_PO4_TO_WATER |
| Phosphorus | water / surface water | kg | `P_surfacewater_erosion` | NO3_PO4_TO_WATER |
| Phosphate | water / surface; water / ground- | kg | `PO4_surfacewater`, `PO4_groundwater` | NO3_PO4_TO_WATER |
| Cadmium, ion; Chromium, ion; Copper, ion; Lead; Mercury; Nickel, ion; Zinc, ion | water / surface; water / ground- | kg | `heavymetal_to_{surface,ground}_water_{cd,cr,cu,pb,hg,ni,zn}` | HM_TO_WATER |
| Water | water / surface; water / ground- | m3 | `ecoinvent_water_to_water_river`, `ecoinvent_water_to_water_groundwater` | WATER_EMISSIONS |
| Water | water / surface | m3 | `eol_waste_water_to_nature` | WASTE_MANAGEMENT |
| COD, DOC, TOC, BOD5 | water / **ground-** | kg | `cod/doc/toc/bod5_in_waste_water` | COD_IN_WASTEWATER |
| Cadmium, Chromium, Copper, Lead, Mercury, Nickel, Zinc | soil / agricultural | kg | `heavymetal_to_soil_minus_uptake_*` | HM_TO_SOIL |
| Mineral oil | soil / agricultural | kg | `pest_horticultural_oil` | PESTICIDES_EMISSION_TO_SOIL |
| <pesticide active ingredient> | soil / agricultural (`e1bc9a16-...`) | kg | `pestikg_*` via properties mapping | PESTICIDES_EMISSION_TO_SOIL |

Methane from rice and biogenic CO2 listed in the documentation's emission overview are not produced
by the tool [V].

### 6.7 Uncertainty [V]

`getUncertainty` (`EcospoldFileWriter.java:651-663`): every exchange with amount > 0 gets a
lognormal distribution with `meanValue = amount`, `mu = ln(amount)`, and the class constants
`variance` / `varianceWithPedigreeUncertainty` plus a fixed pedigree matrix from
`java/ecospold/StandardUncertaintyMetadata.java` (25 classes; e.g. SEEDS, FERTILISERS,
ENERGY_CARRIERS_FUEL_WORK: pedigree (2,1,1,1,1), variance 0.000589, with pedigree 0.001189;
N2O_NOX_TO_AIR (2,2,1,1,1) 0.02829 / 0.02899; NO3_PO4_TO_WATER 0.04109 / 0.04179; HM_TO_WATER
0.08636 / 0.08706; WASTE_MANAGEMENT (4,2,1,1,1)). The basic variances correspond to the ecoinvent
"basic uncertainty" factors of the pedigree approach [I]. Pedigree scores do not depend on the data
origin (user value vs default) [V].

### 6.8 Post-processing [V]

- `squashIntermediateExchanges` / `squashElementaryExchanges` (`:551-622`): exchanges with the
  same master-data id and the same input/output group are merged (amounts summed, comments
  concatenated "This exchange is an aggregation of amounts: ...", uncertainty rebuilt with the
  variance of the previous one). This is what merges, e.g., the three "lime" entries or the two
  "Water, river" entries.
- One dataset parameter `LUC_crop_specific = 1` with an explanatory comment (`:665-679`).
- `mathematicalRelation` is empty for all exchanges except the LUC one.

### 6.9 Resulting dataset structure [V, derived from the code path]

```
ecoSpold
  usedUserMasterData (activityName / intermediateExchange only when not in master data)
  activityDataset
    activityDescription: activity (id, activityNameId, name, generalComment, type 1), classification (none),
                         geography, technology (empty), timePeriod (year-3 .. year), macroEconomicScenario
    flowData
      intermediateExchange: reference product (outputGroup 0), co-products (outputGroup 2),
                            inputs (inputGroup 5; 0 to ~60 depending on data), wastes (outputGroup 3),
                            LUC exchange with mathematicalRelation
      elementaryExchange:   resources (inputGroup 4), emissions to air / water / soil (outputGroup 4)
      parameter:            LUC_crop_specific = 1
    modellingAndValidation: representativeness (system model Undefined, sampling procedure, extrapolations)
    administrativeInformation: dataEntryBy, dataGeneratorAndPublication (placeholders), fileAttributes 3.4
```

### 6.10 Legacy SimaPro CSV path [V]

`java/ScsvFileWriter.java` and `java/scsv/*` (`WfldbTemplateProductUsages.java`, 1323 lines of WFLDB
3.3 process names, `GlobalTemplateSubstanceUsages.java`, SimaPro substance names) write a
windows-1252 SimaPro CSV when `dbOption = WFLDB`. The frontend hardcodes `dbOption=ECOINVENT`
(`src/main/dart/lib/processGenerationSteps/process_generation_steps.html:138`, radio buttons
commented out), so this path is dead for the ecoinvent flavour but still compiled and still consumes
Python outputs (`wfldb_*`, metadata strings).

---

## 7. Technical debt and weak points

### 7.1 Build, runtime and maintainability

1. **Three languages and three runtimes** for one calculation; the Java/Python split is only
   there because the models were written in Python while the Quantis web stack is Java. The HTTP
   bridge is unauthenticated, on a fixed port, single-threaded (`HTTPServer`), with a bare
   `except: raise` (`py/bootstrap.py:17-19`).
2. **Proprietary, source-less dependencies** (`stack`, `login`, `common-formats`): the HTTP server,
   authentication, mail, MyBatis wiring and the whole ecoSpold2 object model cannot be inspected,
   patched or upgraded.
3. **Obsolete toolchain**: Java 8 only (undeclared JAXB), Guice 3.0, POI 3.17 API, Dart 1 /
   AngularDart 4 with `pub build` transformers (cannot be built today), MySQL 5.7, Jackson 2.9.8,
   Shiro 1.3.2, Jetty 9.4.18 (see 2.4). The production binaries were copied, not rebuilt (README).
4. **Master data outside the repository**: six ecoinvent XML files of unknown version must sit in the
   *uploads* folder; without them the server does not start. No record of the ecoinvent version,
   so flow/product UUIDs in generated files cannot be traced.
5. **Secrets and defaults in code**: login secret (`Bootstrap.java:53`), DB `root/root`,
   unauthenticated admin endpoints (`PublicAlcigApi.java:35 //FIXME: All this should be protected`).
6. **No reproducibility**: exchange ids are random v4 UUIDs; the activity id and time period depend
   on the calendar year of the run (`EcospoldFileWriter.java:139-156`).

### 7.2 Input handling

7. **No unit handling at all**: units are template text, the code stores `"TODO"`; percent cells
   depend on Excel formatting; m3 vs kg conversions are scattered (1006 kg/m3 slurry, 1000 kg/m3
   water) in `outputMapping.py`.
8. **Silent defaults**: an empty or invalid cell silently falls back to a country/crop default with
   at most a warning about the cell; nothing records which outputs were computed from defaults
   (`warnIfDefaultExists` is empty; `#TODO: Should we log usage of default value?` in all 12 models).
9. **Template coupling by hidden tags and label text**: block rows are matched by the *label string*
   of the dropdown (`LabelForBlockTags`), so a renamed dropdown entry silently becomes "other";
   template version `v2.0.0` is read but not validated; tags for 13 fields exist in Java but not
   in the template (3.5).
10. **Fragile block parsing** (`ExcelInputReader.java:293-295 // TODO: Not a good way to handle
    blocks`, `:509-512 // FIXME: This doesn't work ... memory leaks`): after a ratio block ends on
    the next `total_*` row, the same row is also processed as a single value before being re-read
    as a block (harmless duplicate today) [I from code reading]; the `part_` branch of
    `ValueGroup.groupValues` uses `substring(6)` for a 5-character prefix (`ValueGroup.java:106`,
    latent).
11. `pest_total` and `total_machinery_diesel` aggregation is a hardcoded special case
    (`ExcelInputReader.java:48-53, 509-553`).

### 7.3 Model layer

12. **Hardcoded data everywhere**: about 12 000 lines of Python (excluding tests), of which roughly 10 000 are literal
    tables (section 5), generated from an Excel workbook that is not in the repository and whose
    provenance comments are often "ask Sämi", "no src", "Strange assumption based on a strange PDF".
13. **Output/variable name mismatches that silently drop flows** [V]: `seeds_<crop>` produced for
    `asparagus_green/white`, `cabbage_red/white`, `coffee_arabica/robusta`, `lemon`, `citruslime`,
    `orange_fresh/processing`, `strawberry_fresh/processing`, `tomato_fresh/processing` and
    `sesame_seed` never match the Java variables `seeds_asparagus`, `seeds_cabbage`,
    `seeds_coffee`, `seeds_lemonlime`, `seeds_orange`, `seeds_strawberry`, `seeds_tomato`,
    `sesame_seed` -> no seed/seedling/tree input for 15 of 67 crops.
14. **Unit and index defects** [V unless noted]: `zn_other` heavy-metal vector assigns the zinc
    content to lead (`fertilisermodel.py:189`); manure heavy metals computed in g/ha and summed
    with mg/ha [I]; compost/sludge NH3 not converted from N to NH3
    (`otherorganicfertilisermodel.py:128-130`); tree/seedling counts used as kg in
    `seedmodel.py:167-170`; Ca fertiliser HM factors are per kg CaO but inputs are kg Ca;
    packaging mass sums kg nutrient, not kg product.
15. **Documented vs implemented differences** (section 4): NH3 not subtracted before NOx; no
    `Nsom` and no rice factor in N2O; NOx not subtracted and factor 0.99 in NO3 supply; HM
    accumulation factor 0.86 vs 1.86; undocumented x6 factor and 3 % slope rule in the P model;
    rice has no land occupation; SOC/land-management effects absent; `heavy_metal_uptake` switch absent.
16. **Duplicated code**: irrigation efficiency computed twice (`irrigationmodel.py:52-66`,
    `defaultGeneration.py:185-208`); heavy-metal vector handling repeated in four models;
    two `StandardUncertaintyMetadata` enums (ecospold and scsv); two complete exchange template
    sets (ecoSpold and WFLDB).
17. **Dead and broken code**: `raise "string"` (TypeError at runtime) in `inputMappings.py:17` and
    `defaultGeneration.py:68`; `NotFoundGenerator` unused; `wfldb_*`, `hm_uptake_formula`,
    `rooting_up_trees`, `heavymetal_to_soil_*` (without uptake), `PO4_surfacewater_drained/_ro`,
    irrigation-type quantities, metadata strings all produced but unused by the ecoSpold writer;
    `SoilTexture` enum members with stray commas (`modelEnums.py:13-15`); `yearly_precipitation_as_snow`
    deprecated but kept.
18. **Error handling**: Python raises bare `KeyError` on unknown crop/country/enum (no GLO fallback
    in per-country tables; safe only because the vocabularies are closed); Java prints lookup
    failures to stdout and drops the exchange.
19. **Comments in French and English mixed**, misleading names (`Nox_as_n2o_air`, `p2O5` vs
    `p2o5`, `fall_plaw`, `havester`, `generateScsv` producing ecoSpold).

### 7.4 Tests

20. **No Java tests** (`junit` is declared, `src/test/java` does not exist).
21. Python tests (`src/test/python/models/`, 13 files, 1-6 assertions each, `unittest`) are not
    discoverable (the test package is also named `models`, no `__init__.py`), require
    `PYTHONPATH=src/main/python`, and several reference inputs or modules that no longer exist
    (`test_transportmodel.py` imports `models.transportmodel`, absent from the repository;
    `test_seedmodel.py` uses the old crop code `asparagus`; `test_irrigationmodel.py` expects the
    key `m_Irr_water_to_air`) [V by reading]. Results reported by the exploration subagent that
    ran them (not re-run by the author): pass for co2, luc, manure, otherorganicfertiliser,
    pmodel; missing-input errors for erosion, fertiliser, hm, pack; stale names for irrigation and
    seed; numeric mismatch for nmodel (389.1168 vs expected 389.1357); import error for transport.
22. No end-to-end test, no reference input/output pair, no validation of the generated XML.

### 7.5 FIXME/TODO inventory [V]

92 `TODO`/`FIXME`/`NOTE` markers (32 in Python, 60 in Java). The ones with functional impact:
`ExcelInputReader.java:152` (version not validated), `:269`, `:293`, `:312`, `:511-512`;
`NumericExtractor.java:193, 240` (unit "TODO"); `ValueGroup.java:193` (units); `EcospoldFileWriter
.java:148` (no greenhouse/organic naming beyond organic); `EcospoldTemplateSubstanceUsages.java:131`
(wrong uncertainty for water to air); `GeographyMappingCache.java:23` (mapping not validated);
`PublicAlcigApi.java:35` (unprotected admin API); `Api.java:81` (app version never filled);
`outputMapping.py:120, 144, 189`; `lucmodel.py:1866` (rice); `defaultGeneration.py:50, 65, 454-456`.

---

## 8. Open questions

Items that could not be settled from the repository and need the methodology owner or the original
developers (Quantis):

1. **Source of the N-leaching regression coefficients** (21.37, 0.0037, 0.0000601, 0.00362) beyond
   the SQCB citation, and the reason for the factor 0.99 on NH3-N and for omitting NOx-N in the
   N supply `S` (`nmodel.py:88, 100`). Also whether the regression (documented per year) is meant
   to be applied per crop cycle with per-cycle water.
2. **N2O**: is the omission of `Nsom` intentional? Is the addition of volatilised N (NH3-N, NOx-N)
   to the direct term the intended way to represent the IPCC indirect pathway? Rice EF1FR?
3. **Heavy metals**: accumulation factor 0.86 (code) vs 1.86 (doc); origin of the seven uptake
   coefficients (`hmmodel.py:139-151`); intended unit of the manure contribution (mg vs g); the
   `zn_other` vector; nickel leaching = 0.
4. **Manure**: origin of the N, P2O5 and TAN concentrations and emission fractions
   (`manuremodel.py:55-94`), of the "world proportions" behind the "other" categories, of the 50 %
   default `liquid_manure_part_before_dilution`, and of the 1006 kg/m3 density.
5. **Phosphorus**: origin of the land-use classes beyond arable/grassland (vegetables, viticulture,
   fruit trees, alpine pastures) and their values; the x6 factor for drained leaching to surface
   water; the 3 % slope threshold; whether the division by crop cycles is intended for yearly averages.
6. **Irrigation**: origin of `EI_IRR_RATIO_*` (14 countries only; GLO 0.55/0.09/0.36) and whether
   they correspond to Gmünder et al. 2019; origin of the ET matrix ("Pfister file") and of the
   technology/source shares.
7. **"GD_crop" workbook**: does ecoinvent hold the Quantis workbook from which all `defaultTables.py`
   and `defaultMatrix*.py` were generated (yield 2009-2012, N uptake, N mineral, manure, pesticides,
   soil, precipitation, fertiliser mixes)? Without it every default table is unsourced.
8. **LUC**: are the expansion ratios (`lucmodel.py`) the output of the "WFLDB-adapted Blonk tool
   2015-06-11a"? Which ecoinvent "land use change, annual/perennial crop" datasets are expected to
   exist for the mathematical relation to resolve, and is the per-country GLO fallback acceptable?
9. **Crop residues**: confirm the IPCC 2006 Table 11.2 origin of the coefficients and the
   simplified below-ground term; sources for the fixed kg N/ha values.
10. **Machinery and energy factors**: the diesel intensities per operation (`outputMapping.py:246-300`),
    45.00450045 MJ/kg diesel, 0.022075 kg/MJ petrol, the fuel LHV divisors, 0.017 kg/m2 fleece, the
    zinc-sulfate formula with 0.478 / 0.00478, and the plastic-tunnel lifetime of 25.
11. **Packaging** factors (2, 2, 3) and the use of kg nutrient as fertiliser mass.
12. **Seeds**: intended handling of seedling and tree counts in the heavy-metal model; the 15
    crops whose seed inputs are lost; whether `nb_planted_trees` defaults (all empty) were meant
    to stay empty.
13. **Master data**: which ecoinvent version (3.4? 3.5?) the six XML files on the production server
    come from; whether the 20 subcompartment UUIDs, the unit UUIDs, the system-model UUID and the
    activity-name UUIDs for PV and wind are still valid.
14. **ecoSpold conventions**: is `fileAttributes 3.4` intended; is the yearly-changing activity id
    acceptable; should metadata (`record_entry_by`, `collection_method`, comments, data-quality
    scores) be written into the dataset; should COD/DOC/TOC/BOD5 go to ground water and groundwater
    use to "Water, river"; is the fixed pedigree per flow family acceptable.
15. **Scope**: is the WFLDB/SimaPro path to be kept or dropped; are greenhouse and hydroponic
    systems (NH3-only, erosion 0, occupation "greenhouse") within the scope of the new tool;
    rice (no occupation, no CH4, no EF1FR) and the 2018 "new crops" with weak sources (castor,
    chickpea, coriander, ginger, millet, sesame, turmeric, pomegranate).
16. **Percent cells**: confirm that the template's `[%]` cells are percent-formatted so that Excel
    stores fractions; otherwise all ratio inputs > 1 are silently dropped.
17. **Dates**: `soil_cultivating_date_main_crop` and `sowing_date_main_crop` are read but unused;
    `harvest_date_previous_crop` drives `crop_cycle_per_year` with a 14-day granularity rule;
    is the documented "12 months unless more than one season" rule intended?

---

## Appendix A. Files consulted

Source: all files under `src/main/python/`, `src/main/java/com/quantis_intl/lcigenerator/`
(`Api.java`, `Bootstrap.java`, `PyBridgeService.java`, `EcospoldFileWriter.java`, `UUIDType5.java`,
`ErrorReporterImpl.java`, `imports/*`, `ecospold/*`, `guice/CoreModule.java`; `scsv/*`, `dao/*`,
`license/*`, `model/*` read via subagent), `src/main/resources/*`, `src/main/sql/script.sql`,
`src/test/python/models/*`, `pom.xml`, `lib/**/*.pom`, `README.md`, `.gitignore`, `src/main/dart/
pubspec.yaml`, `web/index.dart`, `lib/**/*.dart` (via subagent). Documents: `Ecoinvent_Tool_Model_
Description_20191015.pdf` (text extracted with pdftotext), `Guidance_New_crop_20191008.pdf`,
`ALCIG_methodology.pdf`, `Ecoinvent LCI calculation tool - Installation guide_2019-07-02.pdf` (via
subagent), `LCI-Database_Data-collection_Crop_v2.xlsx` (sheet XML dumped with a stdlib script).
Git history via `git log`. No legacy code was executed by the author (see disclosure at the top).

