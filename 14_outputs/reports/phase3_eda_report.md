# Phase 3 exploratory analysis — hypothetical Chennai bin scenario

**Evidence boundary.** All bin, reading, collection and vehicle-day measures below are synthetic. GCC ward IDs and OSM road-node coordinates are real source context, but the bins at those coordinates are hypothetical. Generated mass uses an assumed 0.12 kg/L density. This report does not estimate current municipal waste, route savings or operational performance in Chennai.

## Scope and reconciliation

The existing 1,000-bin scenario contains 4,380,000 scheduled two-hour slots in 2026. 4,314,693 have an observed fill value; missing telemetry remains in the denominator of scheduled slots. Phase 3 SQL reconciles all 4,380,000 fact rows through bin- and zone-day marts and all 218,959 collection attempts. Bounded Python data frames and DuckDB aggregates underpin the charts; the full fact was not loaded into Pandas.

## Exploratory findings

- **Fill and collection.** The observed fill median is 49.9% (IQR 27.0–74.5%). Bins experienced a median 191 successful services over the scenario year. The distribution reflects the generator's 72%/48-hour due rule and sensor noise; it is not evidence of actual early collection.
- **Generated volume.** The simulator generated 18,230.3 tonnes equivalent over the year under the fixed density assumption. Ward 108 has the highest normalized mean (741.7 L/hypothetical bin-day), which is an assumed demand hot spot, not an official ward waste estimate.
- **Calendar shape.** Mean generated mass is 48.3 t/weekday and 54.1 t/weekend day. This difference is expected because a 1.12 weekend multiplier was coded into the simulator. November has the highest simulated mean daily mass (55.7 t/day), reflecting the imposed cosine seasonality. The local-hour chart similarly displays imposed intraday factors.
- **Overflow and service timing.** 501,938 scheduled bin-slots (11.46%) had positive latent physical overflow, totalling 16,977,804 L. 210,221 collections succeeded (including 6,108 partial services), and 8,738 due attempts were missed. The missed-attempt share is 3.99%. The latent-truth diagnostic found 133 successful services under 35% pre-service fill, but 110,578 attempts at ≥95% pre-service fill or positive overflow. Median latent pre-service fill is 95.4%. These thresholds are exploratory flags, not municipal standards; the high stress level calls for calibration before policy comparisons.
- **Geography and associations.** The bin-level Spearman association between gross generated volume/capacity and overflow days is 0.95 (Pearson 0.88). Both quantities depend on the same generator and capacity assumptions, so this is not a causal or transferable estimate. The coordinate plot shows hypothetical risk at real mapped road nodes; it does not identify installed bins.
- **Vehicle-day proxy.** 1 of 18,200 active vehicle-days have fewer than four successful stops. Distance is exactly the assumed 5 + 0.35 km per successful stop, so stops per km and its scatter cannot diagnose real routing inefficiency. No truck travel, depot access or service time was measured.

## Descriptive-statistics and outlier interpretation

`14_outputs/tables/phase3_eda/descriptive_statistics.csv` records mean, median, useful integer modes, sample variance and standard deviation, quartiles/IQR, 5th/95th percentiles, skewness and Tukey outlier counts at explicit city-day, bin-year or vehicle-day grains. A Tukey outlier is a screening flag, not a defective record. Sensor fill is clipped at 0–100%, so skewness and near-boundary frequencies are partly measurement design. The file does not attach naive confidence intervals to 4.38M correlated readings; the statistical report uses weekly aggregates and autocorrelation-aware intervals for two defined contrasts.

## Figures and next decision

Figures `01`–`11` in `14_outputs/charts/phase3/` cover distributions, normalized geography, calendar patterns, overflow, service, vehicle proxies and correlation. Review the 11.46% overflow-slot rate, latent timing flags, capacity and daily-service assumptions before any optimization claim. A field-calibration dataset or a range of clearly labelled scenarios is needed to judge real business significance. Forecasting and routing are intentionally outside Phase 3.
