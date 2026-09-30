# Phase 3 descriptive and inferential statistics

**Population of inference: a hypothetical repeated-run interpretation of the fixed-parameter simulator, evaluated through one seeded trajectory—not Chennai residents, vehicles or actual bins.** The 2026 generator explicitly multiplies weekend arrivals by 1.12 and imposes seasonality; both tests below are *mechanism checks* of that scenario. One seed and one scenario year do not quantify uncertainty in real-world demand, implementation or costs.

## Declared grains and descriptive results

City-day generated mass: 49,946.09 kg/day mean; median 49,941.80; SD 4,975.86; Q1–Q3 45,861.63–53,429.08; IQR 7,567.45; 5th–95th 42,691.37–59,660.43; skewness 0.26; Tukey flags 0.

City-day overflow-slot share: 11.46 percentage points mean; median 11.47; SD 2.07; Q1–Q3 9.68–13.11; IQR 3.42; 5th–95th 8.36–14.69; skewness -0.13; Tukey flags 1.

Bin-year mean daily arrivals: 416.22 L/bin/day mean; median 384.28; SD 194.82; Q1–Q3 281.02–521.12; IQR 240.11; 5th–95th 133.81–808.77; skewness 0.75; Tukey flags 24.

Bin-year successful collections: 210.22 attempts/bin/year mean; median 191.00; SD 39.96; Q1–Q3 182.00–225.00; IQR 43.00; 5th–95th 178.00–305.05; skewness 1.43; Tukey flags 74. The useful integer mode is 180 services/bin-year.

Full observed-fill readings have mean 51.25%, median 49.92%, sample variance 864.70 percentage-points², and 5th–95th range 6.04–100.00%. This is a distribution of repeated, clipped synthetic sensor readings, not independent sample units. Detailed means, variance, quartiles, percentiles, skewness and outlier counts for all six bounded analysis grains are in `14_outputs/tables/phase3_eda/descriptive_statistics.csv`.

## Prespecified hypothesis tests

**Design shared by both tests.** Pair the mean of five weekdays with the mean of two weekend days inside each complete Monday–Sunday week (51 pairs; partial boundary weeks excluded). Test the mean paired difference with an intercept-only Newey–West/Bartlett HAC z statistic using four weekly lags. This choice handles measured serial correlation more honestly than treating millions of bin-slots as independent. Alpha is 0.05, two-sided; Holm adjusts the two p-values. The 95% CI is the estimate ±1.96 HAC SE. An eight-lag HAC result is a sensitivity check, not a second discovery test. Assumptions: comparable daily definitions, adequately long weekly series for asymptotic inference, and a stable dependence structure over this one scenario year. Annual seasonality, fixed seed and known generator design limit these assumptions and generalization.

### 1. Weekend generated mass

- **Business question:** Does this simulator generate different daily waste mass on weekends?
- **H₀:** The expected within-week weekend-minus-weekday generated mass is zero. **H₁:** The expected within-week difference is nonzero.
- **Test/assumptions:** 51 complete paired weeks; HAC(4) mean-difference z test, alpha 0.05, two-sided. Lag-one correlation of weekly differences is 0.77; Shapiro diagnostic p=0.0222, so an independent paired t-test would be poorly justified. The mean is strongly influenced by the simulator's programmed 1.12 weekend factor.
- **Statistic and p-value:** z=32.48; raw p=1.88e-231; Holm p=3.76e-231. HAC(8) sensitivity p=2.5e-141.
- **Effect size and 95% CI:** weekend minus weekday = 5,776.9 kg/city-day (11.97% of paired weekday mean; standardized paired effect dz=8.98); HAC(4) CI [5,428.3, 6,125.5] kg/day; HAC(8) CI [5,329.6, 6,224.3].
- **Business conclusion:** The simulated weekend burden is consistently higher and material for a hypothetical capacity-stress exercise. This confirms a deliberately encoded demand assumption; it does not prove an actual Chennai weekend effect.

### 2. Weekend physical-overflow share

- **Business question:** Does this simulator have a different overflow-slot share on weekends?
- **H₀:** The expected within-week weekend-minus-weekday overflow-slot share is zero. **H₁:** The expected within-week difference is nonzero.
- **Test/assumptions:** Same 51 weekly pairs, HAC(4), alpha 0.05, two-sided and Holm adjustment. The numerator is scheduled bin-slots with positive latent physical overflow; the denominator is all scheduled bin-slots. Lag-one correlation is -0.06; Shapiro diagnostic p=0.806. Sensor values clipped at 100% were not substituted for truth overflow.
- **Statistic and p-value:** z=29.99; raw p=1.28e-197; Holm p=1.28e-197. HAC(8) sensitivity p=9.4e-180.
- **Effect size and 95% CI:** weekend minus weekday = 1.450 percentage points (13.13% relative to the paired weekday mean; standardized paired effect dz=3.25); HAC(4) CI [1.355, 1.544] pp; HAC(8) CI [1.350, 1.549] pp.
- **Business conclusion:** The simulated overflow share rises on weekends under the current scenario. Given the already high 11.46% overall overflow-slot rate, model calibration and stress-testing matter more than the tiny p-value. No actual service-policy effect has been estimated.

## Statistical versus business significance and untestable claims

P-values describe variability inside this fixed-parameter simulator under the stated dependence model. They do **not** make a Chennai operational claim statistically credible. The large magnitude and near-certain direction mainly reflect the generator's programmed weekend factor and daily aggregation across 1,000 synthetic bins. Business significance would require verified local waste/collection volume, bin capacity, missed-service cost, overflow harm and a feasible alternative schedule. The present high overflow level suggests the current assumed arrival rate and once-daily service opportunity may be implausible; scenario sensitivity and field calibration are prerequisites.

Commercial-versus-residential comparisons are not tested because no verified land-use classification of these hypothetical bins exists. Population-density association is not tested because 2011 Census geographies are not crosswalked to current wards. Policy impact and optimization savings are not tested because there is one assumed collection policy and no optimized routes or measured baseline. Bin-level correlations in the EDA report are descriptive, partly mechanical and never causal.
