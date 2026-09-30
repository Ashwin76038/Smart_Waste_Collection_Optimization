"""Prespecified, autocorrelation-aware contrasts within one synthetic scenario year."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / '14_outputs/tables/phase3_eda'
STATS = ROOT / '07_statistics'
REPORT = ROOT / '14_outputs/reports/phase3_statistical_report.md'
ALPHA = 0.05


def hac_mean_test(differences, lags=4):
    """Intercept-only Newey-West/Bartlett asymptotic test for weekly paired differences."""
    x = np.asarray(differences, dtype=float)
    n = len(x)
    if n < 2 * lags + 10:
        raise ValueError('Too few complete weeks for the chosen HAC lag length')
    average = float(x.mean())
    centered = x - average
    long_run_variance = float(np.dot(centered, centered) / n)
    for lag in range(1, lags + 1):
        gamma = float(np.dot(centered[lag:], centered[:-lag]) / n)
        long_run_variance += 2 * (1 - lag / (lags + 1)) * gamma
    if long_run_variance <= 0:
        raise ValueError('Non-positive estimated long-run variance')
    se = float(np.sqrt(long_run_variance / n))
    z = average / se
    p = float(2 * stats.norm.sf(abs(z)))
    return {'n_weeks': n, 'mean_difference': average, 'median_difference': float(np.median(x)),
            'sd_weekly_difference': float(x.std(ddof=1)),
            'standardized_effect_dz': float(average / x.std(ddof=1)),
            'hac_lags': lags, 'hac_standard_error': se, 'test_statistic_z': float(z),
            'p_value_two_sided': p, 'ci95_lower': average - 1.95996398454 * se,
            'ci95_upper': average + 1.95996398454 * se,
            'lag1_autocorrelation': float(pd.Series(x).autocorr(lag=1)),
            'shapiro_p_diagnostic': float(stats.shapiro(x).pvalue),
            'positive_weeks': int((x > 0).sum())}


def complete_week_pairs(daily, metric):
    local = daily[['service_date', metric]].copy()
    local['week_start'] = local.service_date - pd.to_timedelta(local.service_date.dt.dayofweek, unit='D')
    local['weekend'] = local.service_date.dt.dayofweek >= 5
    grouped = local.groupby(['week_start', 'weekend'], observed=True).agg(
        mean=(metric, 'mean'), days=('service_date', 'size')).reset_index()
    values = grouped.pivot(index='week_start', columns='weekend', values='mean')
    counts = grouped.pivot(index='week_start', columns='weekend', values='days')
    mask = (counts[False] == 5) & (counts[True] == 2)
    result = values.loc[mask].rename(columns={False: 'weekday_mean', True: 'weekend_mean'}).reset_index()
    result['weekend_minus_weekday'] = result.weekend_mean - result.weekday_mean
    return result


def run():
    STATS.mkdir(parents=True, exist_ok=True)
    daily = pd.read_csv(TABLES / 'city_daily.csv', parse_dates=['service_date'])
    if len(daily) != 365 or int(daily.scheduled_readings.sum()) != 4_380_000:
        raise AssertionError('Phase 2 city-day grain/count changed')
    definitions = [
        ('weekend_generated_mass', 'generated_kg_simulated', 'kg per city-day',
         'Does this simulator generate different daily waste mass on weekends?',
         'The expected within-week weekend-minus-weekday generated mass is zero.',
         'The expected within-week difference is nonzero.'),
        ('weekend_overflow_slot_share', 'overflow_slot_pct', 'percentage points of scheduled bin-slots',
         'Does this simulator have a different overflow-slot share on weekends?',
         'The expected within-week weekend-minus-weekday overflow-slot share is zero.',
         'The expected within-week difference is nonzero.'),
    ]
    outputs = []
    all_pairs = []
    for test_id, column, unit, question, null, alternative in definitions:
        pairs = complete_week_pairs(daily, column)
        if len(pairs) != 51:
            raise AssertionError(f'Expected 51 full Monday–Sunday weeks, got {len(pairs)}')
        pairs['test_id'] = test_id
        pairs['unit'] = unit
        all_pairs.append(pairs)
        result = hac_mean_test(pairs.weekend_minus_weekday, lags=4)
        sensitivity = hac_mean_test(pairs.weekend_minus_weekday, lags=8)
        result.update({'test_id': test_id, 'unit': unit, 'business_question': question,
            'h0': null, 'h1': alternative,
            'mean_weekday': float(pairs.weekday_mean.mean()),
            'mean_weekend': float(pairs.weekend_mean.mean()),
            'relative_difference_pct': float(100 * result['mean_difference'] / pairs.weekday_mean.mean()),
            'p_value_hac8_sensitivity': sensitivity['p_value_two_sided'],
            'ci95_hac8_lower': sensitivity['ci95_lower'],
            'ci95_hac8_upper': sensitivity['ci95_upper']})
        outputs.append(result)
    all_pairs = pd.concat(all_pairs, ignore_index=True)
    all_pairs['data_origin'] = 'synthetic'
    all_pairs.to_csv(STATS / 'weekly_paired_contrasts.csv', index=False)

    # Holm adjustment is prespecified for the two related weekend questions.
    order = np.argsort([item['p_value_two_sided'] for item in outputs])
    running = 0.0
    for index, position in enumerate(order):
        adjusted = min(1.0, outputs[position]['p_value_two_sided'] * (len(outputs) - index))
        running = max(running, adjusted)
        outputs[position]['p_value_holm'] = running
        outputs[position]['reject_h0_at_0_05'] = running < ALPHA
    pd.DataFrame(outputs).to_csv(STATS / 'hypothesis_tests.csv', index=False)
    (STATS / 'hypothesis_tests.json').write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')

    a, b = outputs
    desc = pd.read_csv(TABLES / 'descriptive_statistics.csv')
    def statline(metric):
        row = desc.loc[desc.metric == metric].iloc[0]
        return (f"{row['mean']:,.2f} {row['unit']} mean; median {row['median']:,.2f}; "
                f"SD {row['std_dev']:,.2f}; Q1–Q3 {row['q1']:,.2f}–{row['q3']:,.2f}; "
                f"IQR {row['iqr']:,.2f}; 5th–95th {row['p05']:,.2f}–{row['p95']:,.2f}; "
                f"skewness {row['skewness']:.2f}; Tukey flags {int(row['tukey_outlier_count'])}.")
    report = f'''# Phase 3 descriptive and inferential statistics

**Population of inference: a hypothetical repeated-run interpretation of the fixed-parameter simulator, evaluated through one seeded trajectory—not Chennai residents, vehicles or actual bins.** The 2026 generator explicitly multiplies weekend arrivals by 1.12 and imposes seasonality; both tests below are *mechanism checks* of that scenario. One seed and one scenario year do not quantify uncertainty in real-world demand, implementation or costs.

## Declared grains and descriptive results

City-day generated mass: {statline('city_daily_generated_mass')}

City-day overflow-slot share: {statline('city_daily_overflow_slot_share')}

Bin-year mean daily arrivals: {statline('bin_mean_daily_arrival')}

Bin-year successful collections: {statline('bin_annual_successful_collections')} The useful integer mode is {desc.loc[desc.metric == 'bin_annual_successful_collections', 'mode_if_useful'].iloc[0]:.0f} services/bin-year.

Full observed-fill readings have mean {desc.loc[desc.metric == 'observed_fill_readings', 'mean'].iloc[0]:.2f}%, median {desc.loc[desc.metric == 'observed_fill_readings', 'median'].iloc[0]:.2f}%, sample variance {desc.loc[desc.metric == 'observed_fill_readings', 'variance'].iloc[0]:.2f} percentage-points², and 5th–95th range {desc.loc[desc.metric == 'observed_fill_readings', 'p05'].iloc[0]:.2f}–{desc.loc[desc.metric == 'observed_fill_readings', 'p95'].iloc[0]:.2f}%. This is a distribution of repeated, clipped synthetic sensor readings, not independent sample units. Detailed means, variance, quartiles, percentiles, skewness and outlier counts for all six bounded analysis grains are in `14_outputs/tables/phase3_eda/descriptive_statistics.csv`.

## Prespecified hypothesis tests

**Design shared by both tests.** Pair the mean of five weekdays with the mean of two weekend days inside each complete Monday–Sunday week (51 pairs; partial boundary weeks excluded). Test the mean paired difference with an intercept-only Newey–West/Bartlett HAC z statistic using four weekly lags. This choice handles measured serial correlation more honestly than treating millions of bin-slots as independent. Alpha is {ALPHA:.2f}, two-sided; Holm adjusts the two p-values. The 95% CI is the estimate ±1.96 HAC SE. An eight-lag HAC result is a sensitivity check, not a second discovery test. Assumptions: comparable daily definitions, adequately long weekly series for asymptotic inference, and a stable dependence structure over this one scenario year. Annual seasonality, fixed seed and known generator design limit these assumptions and generalization.

### 1. Weekend generated mass

- **Business question:** {a['business_question']}
- **H₀:** {a['h0']} **H₁:** {a['h1']}
- **Test/assumptions:** 51 complete paired weeks; HAC(4) mean-difference z test, alpha 0.05, two-sided. Lag-one correlation of weekly differences is {a['lag1_autocorrelation']:.2f}; Shapiro diagnostic p={a['shapiro_p_diagnostic']:.3g}, so an independent paired t-test would be poorly justified. The mean is strongly influenced by the simulator's programmed 1.12 weekend factor.
- **Statistic and p-value:** z={a['test_statistic_z']:.2f}; raw p={a['p_value_two_sided']:.3g}; Holm p={a['p_value_holm']:.3g}. HAC(8) sensitivity p={a['p_value_hac8_sensitivity']:.3g}.
- **Effect size and 95% CI:** weekend minus weekday = {a['mean_difference']:,.1f} kg/city-day ({a['relative_difference_pct']:.2f}% of paired weekday mean; standardized paired effect dz={a['standardized_effect_dz']:.2f}); HAC(4) CI [{a['ci95_lower']:,.1f}, {a['ci95_upper']:,.1f}] kg/day; HAC(8) CI [{a['ci95_hac8_lower']:,.1f}, {a['ci95_hac8_upper']:,.1f}].
- **Business conclusion:** The simulated weekend burden is consistently higher and material for a hypothetical capacity-stress exercise. This confirms a deliberately encoded demand assumption; it does not prove an actual Chennai weekend effect.

### 2. Weekend physical-overflow share

- **Business question:** {b['business_question']}
- **H₀:** {b['h0']} **H₁:** {b['h1']}
- **Test/assumptions:** Same 51 weekly pairs, HAC(4), alpha 0.05, two-sided and Holm adjustment. The numerator is scheduled bin-slots with positive latent physical overflow; the denominator is all scheduled bin-slots. Lag-one correlation is {b['lag1_autocorrelation']:.2f}; Shapiro diagnostic p={b['shapiro_p_diagnostic']:.3g}. Sensor values clipped at 100% were not substituted for truth overflow.
- **Statistic and p-value:** z={b['test_statistic_z']:.2f}; raw p={b['p_value_two_sided']:.3g}; Holm p={b['p_value_holm']:.3g}. HAC(8) sensitivity p={b['p_value_hac8_sensitivity']:.3g}.
- **Effect size and 95% CI:** weekend minus weekday = {b['mean_difference']:.3f} percentage points ({b['relative_difference_pct']:.2f}% relative to the paired weekday mean; standardized paired effect dz={b['standardized_effect_dz']:.2f}); HAC(4) CI [{b['ci95_lower']:.3f}, {b['ci95_upper']:.3f}] pp; HAC(8) CI [{b['ci95_hac8_lower']:.3f}, {b['ci95_hac8_upper']:.3f}] pp.
- **Business conclusion:** The simulated overflow share rises on weekends under the current scenario. Given the already high 11.46% overall overflow-slot rate, model calibration and stress-testing matter more than the tiny p-value. No actual service-policy effect has been estimated.

## Statistical versus business significance and untestable claims

P-values describe variability inside this fixed-parameter simulator under the stated dependence model. They do **not** make a Chennai operational claim statistically credible. The large magnitude and near-certain direction mainly reflect the generator's programmed weekend factor and daily aggregation across 1,000 synthetic bins. Business significance would require verified local waste/collection volume, bin capacity, missed-service cost, overflow harm and a feasible alternative schedule. The present high overflow level suggests the current assumed arrival rate and once-daily service opportunity may be implausible; scenario sensitivity and field calibration are prerequisites.

Commercial-versus-residential comparisons are not tested because no verified land-use classification of these hypothetical bins exists. Population-density association is not tested because 2011 Census geographies are not crosswalked to current wards. Policy impact and optimization savings are not tested because there is one assumed collection policy and no optimized routes or measured baseline. Bin-level correlations in the EDA report are descriptive, partly mechanical and never causal.
'''
    REPORT.write_text(report, encoding='utf-8')

    zone_top = pd.read_csv(TABLES / 'zone_annual_summary.csv', dtype={'zone_id': 'string'}).sort_values(
        'mean_arrival_l_bin_day', ascending=False).iloc[0]
    insights = [
        {'insight_id': 'I01', 'question': 'Which zones bear the highest simulated generation per bin?',
         'finding': f"Ward {zone_top.zone_id} ranks highest at {zone_top.mean_arrival_l_bin_day:.1f} generated L per hypothetical bin-day; high values reflect assumed bin demand factors.",
         'evidence': '05_sql/phase3_business_questions.sql#01_zone_generation; 14_outputs/tables/phase3_eda/zone_annual_summary.csv',
         'decision': 'Use as a calibration and prioritization hypothesis only.', 'data_origin': 'synthetic', 'confidence': 'scenario-only'},
        {'insight_id': 'I02', 'question': 'Are weekends different within the simulation?',
         'finding': f"Paired weekly generation contrast {a['mean_difference']:,.0f} kg/day; overflow contrast {b['mean_difference']:.2f} pp; both encoded by scenario design.",
         'evidence': '07_statistics/hypothesis_tests.csv; 14_outputs/reports/phase3_statistical_report.md',
         'decision': 'Stress-test weekend capacity; do not claim a real Chennai pattern.', 'data_origin': 'synthetic', 'confidence': 'mechanism check'},
        {'insight_id': 'I03', 'question': 'Is the scenario over-stressed?',
         'finding': '11.46% of scheduled slots have positive physical overflow; service attempts often occur near full.',
         'evidence': '14_outputs/tables/phase3_eda/phase3_metrics.json; 14_outputs/reports/phase3_eda_report.md',
         'decision': 'Calibrate arrival and service-frequency assumptions before comparing policies.', 'data_origin': 'synthetic', 'confidence': 'exact for this run'},
        {'insight_id': 'I04', 'question': 'Can route inefficiency be measured now?',
         'finding': 'No: distance is a deterministic 5 + 0.35 km per successful stop proxy.',
         'evidence': '05_sql/phase3_business_questions.sql#09_route_proxy; config/simulation_assumptions.md',
         'decision': 'Await actual road-network routing and fleet constraints.', 'data_origin': 'assumption', 'confidence': 'not estimable'},
        {'insight_id': 'I05', 'question': 'Can actual population or land-use drivers be inferred?',
         'finding': 'No verified present-ward Census crosswalk or bin land-use class exists.',
         'evidence': 'PROJECT_STATE.md; docs/source_verification.md',
         'decision': 'Keep demographic and commercial/residential tests out of this phase.', 'data_origin': 'official context plus synthetic operations', 'confidence': 'not estimable'},
    ]
    pd.DataFrame(insights).to_csv(ROOT / '14_outputs/tables/phase3_insight_log.csv', index=False)
    return outputs


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
