import dataloader
from models.atomicmass import NH3_TO_N_FACTOR, NO2_TO_N_FACTOR, N_TO_NO3_FACTOR,\
    N_TO_N2O_FACTOR, N_TO_NO2_FACTOR


class NModel(object):
    """Inputs:
      crop: crop code ("rice" = flooded rice, EF1FR)
      soc_change_kg_c: kg C / (ha*crop cycle), change of soil organic carbon (negative = loss)
      luc_from_forest_or_grassland: "yes" / "no" (C:N ratio 15 / 11 for the mineralised N)
      ammonia_due_to_manure: kg NH3 / (ha*crop cycle)
      ammonia_due_to_mineral_fert: kg NH3 / (ha*crop cycle)
      ammonia_due_to_other_orga_fert: kg NH3 / (ha*crop cycle)
      bulk_density_of_soil: kg/m3
      c_per_n_ratio: ratio
      clay_content: ratio
      considered_soil_volume: m3/ha
      drained_part: ratio
      nitrogen_from_all_manure: kg N / (ha*crop cycle)
      nitrogen_from_crop_residues: kg N / (ha*crop cycle)
      nitrogen_from_mineral_fert: kg N / (ha*crop cycle)
      nitrogen_from_other_orga_fert: kg N / (ha*crop cycle)
      nitrogen_uptake_by_crop: kg N / (ha*crop cycle)
      norg_per_ntotal_ratio: ratio
      soluble_nitrogen_from_organic_fert: kg N / (ha*crop cycle), TAN of manure, compost and sludge
      organic_carbon_content: kg C/kg soil,
      average_annual_precipitation: mm/year
      crop_cycle_per_year: ratio (occupation period = 1 / crop_cycle_per_year years)
      rooting_depth: m
      water_use_total: m3/(ha*crop cycle)

    Outputs:
      m_N_ammonia_total: kg NH3 / (ha*crop cycle)
      m_N_nitrate_to_groundwater: kg NO3 / (ha*crop cycle)
      m_N_nitrate_to_surfacewater: kg NO3 / (ha*crop cycle)
      m_N_N2o_air: kg N2O / (ha*crop cycle)
      m_N_Nox_as_n2o_air: kg NOx as N2O / (ha*crop cycle)
    """

    _input_variables = [
                        "crop",
                        "soc_change_kg_c",
                        "luc_from_forest_or_grassland",
                        "ammonia_due_to_manure",
                        "ammonia_due_to_mineral_fert",
                        "ammonia_due_to_other_orga_fert",
                        "bulk_density_of_soil",
                        "c_per_n_ratio",
                        "clay_content",
                        "considered_soil_volume",
                        "drained_part",
                        "nitrogen_from_all_manure",
                        "nitrogen_from_crop_residues",
                        "nitrogen_from_mineral_fert",
                        "nitrogen_from_other_orga_fert",
                        "nitrogen_uptake_by_crop",
                        "norg_per_ntotal_ratio",
                        "soluble_nitrogen_from_organic_fert",
                        "organic_carbon_content",
                        "average_annual_precipitation",
                        "crop_cycle_per_year",
                        "rooting_depth",
                        "water_use_total"
                       ]

    def __init__(self, inputs):
        #TODO: Should we log usage of default value?
        for key in NModel._input_variables:
            setattr(self, key, inputs[key])
        self.last_nitrogen_supply = None  # S of the last compute(), for tests and reports

    def compute(self):
        self._check_fractions()
        total_fert_nitrogen = self._compute_total_fert_nitrogen()
        ammonia_total = self._compute_total_due_ammonia()
        nox = self._compute_nox_as_no2(total_fert_nitrogen, ammonia_total)
        flooded_rice = self._is_flooded_rice()
        n2o_direct_as_n = self._compute_direct_n2o_as_n(total_fert_nitrogen, 0.0, 0.0, flooded_rice)
        no3asNleach = self.computeNO3leachAsN(ammonia_total, nox, n2o_direct_as_n)
        n2o = self._compute_n2o_total(total_fert_nitrogen, self.nitrogen_from_crop_residues,
                                      self._compute_n_som(), ammonia_total, nox, no3asNleach,
                                      flooded_rice)
        no3gw, no3sw = self._split_n3oasNleach_between_ground_and_surface_waters(no3asNleach)
        return {"m_N_ammonia_total": ammonia_total,
                "m_N_nitrate_to_groundwater": no3gw,
                "m_N_nitrate_to_surfacewater": no3sw,
                "m_N_N2o_air": n2o,
                "m_N_Nox_as_n2o_air": nox}

    def _compute_total_due_ammonia(self):
        return self.ammonia_due_to_mineral_fert + self.ammonia_due_to_manure + self.ammonia_due_to_other_orga_fert

    def _compute_total_fert_nitrogen(self):
        return self.nitrogen_from_all_manure + self.nitrogen_from_mineral_fert + self.nitrogen_from_other_orga_fert

    def _compute_nox_as_no2(self, total_fert_nitrogen, ammonia_total):
        """NOx [kg NO2/ha] from mineral and organic N (Fix F1, reference_models.nox).

        EF = 0.04 kg NO2/kg N (EEA 2016, 3.D Tab. 3-1, note a: reported as NO2), stored as
        ef_nox_n = 0.012174 kg NOx-N/kg N in model_parameters.csv, applied to the N applied
        minus the N volatilised as NH3, then converted to NO2 with 46/14.
        Deviation from Quantis (2019), which converted the factor with 14/30 as if it were
        expressed as NO (0.018667 kg NOx-N/kg N, +53 %) and did not subtract the NH3-N.
        """
        n_base = max(total_fert_nitrogen - NH3_TO_N_FACTOR * ammonia_total, 0.0)
        return dataloader.param("ef_nox_n") * n_base * N_TO_NO2_FACTOR

    def _is_flooded_rice(self):
        """Flooded crops get EF1FR (IPCC 2006 Tab. 11.1): column "flooded" of data/crop_types.csv
        (only rice; the template has no flooding input)."""
        return dataloader.table("crop_types.csv", numeric=False)[self.crop]["flooded"] == "yes"

    def _compute_n_som(self):
        """N mineralised from soil organic carbon loss [kg N] (IPCC F_SOM; Fix F2).

        N_som = max(-delta_SOC, 0) / C:N, with C:N 15 for land converted from forest or
        grassland and 11 for cropland (Quantis 2019 section 2.9.1.2). The SOC change comes
        from the land-use / land-management block (0 in the legacy template), which must not
        report this N2O itself (SALCAfieldN, Nemecek et al. 2023 ESM1 Eq. 5).
        """
        cn_ratio = dataloader.param("cn_ratio_luc" if self.luc_from_forest_or_grassland == "yes"
                                    else "cn_ratio_cropland")
        return max(-self.soc_change_kg_c, 0.0) / cn_ratio

    def _compute_direct_n2o_as_n(self, n_applied, n_crop_residues, n_som, flooded_rice):
        """Direct N2O-N [kg N], IPCC 2006 Eq. 11.1: EF1 (or EF1FR for flooded rice) x
        (N applied + N in crop residues + N mineralised from SOC loss)."""
        ef1 = dataloader.param("ef1_flooded_rice" if flooded_rice else "ef1_direct_n2o")
        return ef1 * (n_applied + n_crop_residues + n_som)

    def _compute_n2o_total(self, n_applied, n_crop_residues, n_som, nh3_kg, nox_kg,
                           no3_as_n, flooded_rice):
        """N2O [kg N2O] = 44/28 x (direct + indirect) (Fix F2, reference_models.n2o).

        direct   = EF1 or EF1FR x (N applied + N residues + N_som)   (IPCC 2006 Eq. 11.1)
        indirect = EF4 x (NH3-N + NOx-N) + EF5 x leached NO3-N       (Eq. 11.9 and 11.10)
        The legacy code added the volatilised N to the direct term with EF1 (numerically
        the same as EF4 = 0.01) and had no N_som and no rice factor.
        """
        direct = self._compute_direct_n2o_as_n(n_applied, n_crop_residues, n_som, flooded_rice)
        indirect = dataloader.param("ef4_volatilisation") \
            * (NH3_TO_N_FACTOR * nh3_kg + NO2_TO_N_FACTOR * nox_kg) \
            + dataloader.param("ef5_leaching") * no3_as_n
        return N_TO_N2O_FACTOR * (direct + indirect)

    def computeNO3leachAsN(self, ammonia_total, nox, n2o_direct_as_n):
        corg = self._compute_carbon_in_soil_orga_matter()
        s = self._compute_nitrogen_supply(nh3_as_n=NH3_TO_N_FACTOR * ammonia_total,
                                          nox_as_n=NO2_TO_N_FACTOR * nox,
                                          n2o_as_n=n2o_direct_as_n)
        self.last_nitrogen_supply = s
        norg = self._compute_nitrogen_in_soil_orga_matter(corg)
        return self._compute_nitrogen_leaching(s, norg)

    def _compute_carbon_in_soil_orga_matter(self):  # kg C/kg soil * kg soil/m3 * m3/ha -> kg C/ha
        return self.organic_carbon_content * self.bulk_density_of_soil * self.considered_soil_volume

    def _compute_nitrogen_supply(self, nh3_as_n, nox_as_n, n2o_as_n):
        """N supply S of the SQCB-NO3 regression [kg N] (Fix F3, reference_models.nitrate_leaching).

        S = N_mineral + soluble N_organic - (NH3-N + NOx-N + direct N2O-N), never negative.
        The legacy code used the total organic N, subtracted only 99 % of the NH3-N and no
        NOx-N; Quantis (2019) section 2.4 counts only the soluble part of the organic N and
        subtracts all gaseous losses.
        """
        s = (self.nitrogen_from_mineral_fert + self.soluble_nitrogen_from_organic_fert
             - nh3_as_n - nox_as_n - n2o_as_n)
        return max(s, 0.0)

    def _check_fractions(self):
        """Clay content must be a fraction (Annex 1 of Quantis 2019 gives ratios, e.g. 0.30)."""
        if not 0.0 < self.clay_content < 1.0:
            raise ValueError("clay_content must be a fraction in (0, 1), got %r" % self.clay_content)

    def _compute_nitrogen_in_soil_orga_matter(self, carbon_in_soil):
        return carbon_in_soil / self.c_per_n_ratio * self.norg_per_ntotal_ratio

    def _compute_nitrogen_leaching(self, s, nitrogen_in_soil):
        """Leached NO3-N [kg N per crop cycle], SQCB-NO3 regression (Quantis 2019 section 2.4)
        applied per crop cycle (decision D1, reference_models.nitrate_leaching):

        N = 21.37 x t + P / (c x L) x (0.0037 x S + 0.0000601 x Norg x t - 0.00362 x U)

        t = occupation period [yr] = 1 / crop_cycle_per_year; P = annual precipitation +
        irrigation of the cycle expressed per year [mm/yr]; c = clay [%]; L = rooting depth [m];
        S and U are cycle totals. Identical to the documented annual formula for t = 1.
        Coefficients from model_parameters.csv (Faist Emmenegger et al. 2009).
        """
        t = self._duration_years()
        res = dataloader.param("sqcb_intercept") * t \
              + self._compute_annual_water_in_mm() / (self.clay_content * 100 * self.rooting_depth) \
              * (dataloader.param("sqcb_coef_s") * s
                 + dataloader.param("sqcb_coef_norg") * nitrogen_in_soil * t
                 - dataloader.param("sqcb_coef_u") * self.nitrogen_uptake_by_crop)
        return max(0.0, res)

    def _duration_years(self):
        """Occupation period of the crop cycle in years (harvest to harvest)."""
        return 1.0 / self.crop_cycle_per_year

    def _compute_annual_water_in_mm(self):
        """Precipitation plus irrigation on an annual basis [mm/yr]: the irrigation of the
        cycle [m3/ha] is converted to mm (x 0.1) and divided by the occupation period."""
        return self.average_annual_precipitation + self.water_use_total * 0.1 / self._duration_years()

    def _split_n3oasNleach_between_ground_and_surface_waters(self, no3asNleach):
        nitrate = no3asNleach * N_TO_NO3_FACTOR
        surface = nitrate * self.drained_part
        ground = nitrate - surface
        return (ground, surface)
