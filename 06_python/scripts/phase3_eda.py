"""Phase 3 exploratory analysis of the existing, explicitly synthetic scenario.

Large telemetry stays in DuckDB; Python receives bounded aggregates and summaries.
No forecasting, routing or causal claims are made here.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / '03_data/processed/waste.duckdb'
TABLES = ROOT / '14_outputs/tables/phase3_eda'
CHARTS = ROOT / '14_outputs/charts/phase3'
REPORT = ROOT / '14_outputs/reports/phase3_eda_report.md'
NOTE = 'Synthetic operations, hypothetical 2026 • not observed Chennai bin data'


def save_chart(fig, name):
    fig.text(0.5, 0.012, NOTE, ha='center', fontsize=8, color='#555555')
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(CHARTS / name, dpi=150, bbox_inches='tight')
    plt.close(fig)


def summarize(values, name, unit, discrete=False):
    s = pd.Series(values).dropna().astype(float)
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mode = s.mode().iloc[0] if discrete and len(s) else np.nan
    return {'metric': name, 'unit': unit, 'n': int(len(s)),
            'mean': float(s.mean()), 'median': float(s.median()),
            'mode_if_useful': float(mode) if discrete else np.nan,
            'variance': float(s.var(ddof=1)), 'std_dev': float(s.std(ddof=1)),
            'q1': float(q1), 'q3': float(q3), 'iqr': float(iqr),
            'p05': float(s.quantile(.05)), 'p95': float(s.quantile(.95)),
            'skewness': float(stats.skew(s, bias=False)),
            'tukey_outlier_count': int(((s < low) | (s > high)).sum())}


def run():
    TABLES.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(DB), read_only=True)
    try:
        city = c.execute('''SELECT service_date_local AS service_date,
            SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
            SUM(overflow_l_simulated) AS overflow_l_simulated,
            SUM(successful_collections) AS successful_collections,
            SUM(missed_collections) AS missed_collections,
            SUM(scheduled_readings) AS scheduled_readings
            FROM zone_daily_metrics GROUP BY service_date ORDER BY service_date''').df()
        overflow_slots = c.execute('''SELECT CAST(service_date_local AS DATE) AS service_date,
            COUNT(*) FILTER (WHERE overflow_l_true > 0) AS overflowing_slots,
            COUNT(*) AS scheduled_slots
            FROM simulation_truth GROUP BY service_date ORDER BY service_date''').df()
        city = city.merge(overflow_slots, on='service_date', validate='one_to_one')
        city['service_date'] = pd.to_datetime(city['service_date'])
        city['overflow_slot_pct'] = 100 * city.overflowing_slots / city.scheduled_slots
        city['weekday'] = city.service_date.dt.day_name()
        city['weekend'] = city.service_date.dt.dayofweek >= 5
        city['month'] = city.service_date.dt.month
        city['trailing_7day_kg'] = city.generated_kg_simulated.rolling(7, min_periods=1).mean()
        city['data_origin'] = 'synthetic'
        city.to_csv(TABLES / 'city_daily.csv', index=False)

        bins = c.execute('''SELECT b.bin_id, b.zone_id, b.latitude, b.longitude,
            b.capacity_l, b.demand_factor,
            COUNT(*) AS days, SUM(d.arrivals_l_simulated) / COUNT(*) AS mean_arrival_l_day,
            100.0 * SUM(d.arrivals_l_simulated) / (COUNT(*) * b.capacity_l) AS gross_capacity_pct_day,
            COUNT(*) FILTER (WHERE d.overflow_l_simulated > 0) AS overflow_days,
            SUM(d.overflow_l_simulated) AS annual_overflow_l_simulated,
            SUM(d.successful_collections) AS successful_collections,
            SUM(d.missed_collections) AS missed_collections,
            AVG(d.mean_observed_fill_pct) AS mean_observed_fill_pct
            FROM bin_daily_metrics d JOIN dim_bin b USING (bin_id)
            GROUP BY b.bin_id,b.zone_id,b.latitude,b.longitude,b.capacity_l,b.demand_factor
            ORDER BY b.bin_id''').df()
        bins['data_origin'] = 'synthetic bins at real OSM road nodes'
        bins.to_csv(TABLES / 'bin_annual_summary.csv', index=False)
        zones = c.execute('''SELECT zone_id, MAX(bins) AS bins, COUNT(*) AS days,
            SUM(arrivals_l_simulated) * 0.12 AS generated_kg_simulated,
            SUM(arrivals_l_simulated) / SUM(bins) AS mean_arrival_l_bin_day,
            SUM(overflow_l_simulated) AS overflow_l_simulated,
            7.0 * SUM(successful_collections) / SUM(bins) AS collections_per_bin_week
            FROM zone_daily_metrics GROUP BY zone_id ORDER BY zone_id''').df()
        zones['data_origin'] = 'synthetic'
        zones.to_csv(TABLES / 'zone_annual_summary.csv', index=False)

        fill_hist = c.execute('''SELECT LEAST(100, FLOOR(fill_level_pct / 5) * 5)::INTEGER AS fill_bucket_lower_pct,
            COUNT(*) AS received_readings FROM fact_bin_readings
            WHERE fill_level_pct IS NOT NULL GROUP BY 1 ORDER BY 1''').df()
        fill_hist['data_origin'] = 'synthetic'
        fill_hist.to_csv(TABLES / 'fill_histogram.csv', index=False)
        fill_stats = c.execute('''SELECT COUNT(*) AS observed_n,
            AVG(fill_level_pct) AS mean_fill_pct, MEDIAN(fill_level_pct) AS median_fill_pct,
            VAR_SAMP(fill_level_pct) AS variance_fill_pct2,
            STDDEV_SAMP(fill_level_pct) AS sd_fill_pct,
            QUANTILE_CONT(fill_level_pct, .25) AS q1_fill_pct,
            QUANTILE_CONT(fill_level_pct, .75) AS q3_fill_pct,
            QUANTILE_CONT(fill_level_pct, .05) AS p05_fill_pct,
            QUANTILE_CONT(fill_level_pct, .95) AS p95_fill_pct,
            SKEWNESS(fill_level_pct) AS skew_fill
            FROM fact_bin_readings WHERE fill_level_pct IS NOT NULL''').df().iloc[0].to_dict()

        service = c.execute('''SELECT collection_status, COUNT(*) AS attempts,
            SUM(collected_kg) AS collected_kg_simulated,
            AVG(collected_kg) AS mean_collected_kg_attempt
            FROM collection_events GROUP BY collection_status ORDER BY collection_status''').df()
        service['data_origin'] = 'synthetic'
        service.to_csv(TABLES / 'service_status.csv', index=False)
        timing = c.execute('''SELECT COUNT(*) AS attempts,
            COUNT(*) FILTER (WHERE e.collection_status IN ('collected','partial')) AS successful_attempts,
            COUNT(*) FILTER (WHERE e.collection_status IN ('collected','partial')
              AND 100 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l < 35) AS early_successes_lt35_pct,
            COUNT(*) FILTER (WHERE 100 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l >= 95
              OR t.overflow_l_true > 0) AS near_full_or_overflow_attempts,
            MEDIAN(100 * (t.inventory_l_true + t.removed_l_true) / t.capacity_l) AS median_pre_service_fill_pct_true
            FROM collection_events e JOIN simulation_truth t ON e.collection_id=t.reading_id''').df().iloc[0].to_dict()
        route = c.execute('''SELECT service_date_local, vehicle_id, successful_stops,
            missed_stops, collected_kg_simulated, distance_km_assumed
            FROM route_daily_metrics''').df()
        route['data_origin'] = 'synthetic stops; assumed distance'
        route.to_csv(TABLES / 'route_day_summary.csv', index=False)
    finally:
        c.close()

    # Descriptive distributions are at declared grains, not 4.38M pseudo-independent bins.
    descriptions = [
        summarize(city.generated_kg_simulated, 'city_daily_generated_mass', 'kg/day'),
        summarize(city.overflow_slot_pct, 'city_daily_overflow_slot_share', 'percentage points'),
        summarize(bins.mean_arrival_l_day, 'bin_mean_daily_arrival', 'L/bin/day'),
        summarize(bins.successful_collections, 'bin_annual_successful_collections', 'attempts/bin/year', True),
        summarize(bins.overflow_days, 'bin_annual_overflow_days', 'days/bin/year', True),
        summarize(route.successful_stops, 'route_proxy_successful_stops', 'stops/vehicle-day', True),
    ]
    descriptions.append({'metric': 'observed_fill_readings', 'unit': 'fill percentage points',
        'n': int(fill_stats['observed_n']), 'mean': float(fill_stats['mean_fill_pct']),
        'median': float(fill_stats['median_fill_pct']), 'mode_if_useful': np.nan,
        'variance': float(fill_stats['variance_fill_pct2']), 'std_dev': float(fill_stats['sd_fill_pct']),
        'q1': float(fill_stats['q1_fill_pct']), 'q3': float(fill_stats['q3_fill_pct']),
        'iqr': float(fill_stats['q3_fill_pct'] - fill_stats['q1_fill_pct']),
        'p05': float(fill_stats['p05_fill_pct']), 'p95': float(fill_stats['p95_fill_pct']),
        'skewness': float(fill_stats['skew_fill']), 'tukey_outlier_count': np.nan})
    pd.DataFrame(descriptions).to_csv(TABLES / 'descriptive_statistics.csv', index=False)

    # Associations are descriptive and partly mechanical under the generator.
    corr_vars = ['gross_capacity_pct_day', 'overflow_days', 'successful_collections', 'mean_observed_fill_pct']
    corr = bins[corr_vars].corr(method='spearman')
    corr.to_csv(TABLES / 'bin_spearman_correlations.csv')
    rho = float(corr.loc['gross_capacity_pct_day', 'overflow_days'])
    pearson = float(bins[['gross_capacity_pct_day', 'overflow_days']].corr().iloc[0, 1])

    # 1. Full-fact histogram is aggregated in DuckDB; no 4.38M-row pandas load.
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(fill_hist.fill_bucket_lower_pct, fill_hist.received_readings / 1e6,
           width=4.4, color='#166b8b')
    ax.set(xlabel='Observed fill bucket (%; 5-point width)', ylabel='Readings (millions)',
           title='Simulated observed fill distribution')
    save_chart(fig, '01_fill_distribution.png')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(bins.successful_collections, bins=25, color='#6a5acd', edgecolor='white')
    ax.set(xlabel='Successful collections per hypothetical bin in 2026', ylabel='Bins',
           title='Collection frequency distribution')
    save_chart(fig, '02_collection_frequency.png')

    top = zones.sort_values('mean_arrival_l_bin_day', ascending=False).head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.zone_id, top.mean_arrival_l_bin_day, color='#18794e')
    ax.set(xlabel='Generated litres per hypothetical bin-day', ylabel='GCC ward ID',
           title='Highest simulated generation, normalized for bin count')
    save_chart(fig, '03_zone_generation.png')

    hourly = pd.read_csv(ROOT / '14_outputs/tables/phase3_sql/05_hourly_generation.csv')
    hourly = hourly.sort_values('local_hour')
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(hourly.local_hour, hourly.mean_arrival_l_per_bin_slot, marker='o', color='#d55e00')
    ax.set_xticks(hourly.local_hour)
    ax.set(xlabel='Local hour at start of two-hour slot (IST)',
           ylabel='Mean generated L/bin-slot', title='Assumed intraday demand profile')
    save_chart(fig, '04_hourly_arrivals.png')

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(city.service_date, city.generated_kg_simulated / 1000, color='#c1d4de', lw=.9, label='Daily')
    ax.plot(city.service_date, city.trailing_7day_kg / 1000, color='#164b6b', lw=1.8, label='Trailing 7-day mean')
    ax.set(xlabel='Hypothetical service date', ylabel='Generated tonnes/day (assumed 0.12 kg/L)',
           title='Daily simulated generation')
    ax.legend(frameon=False)
    save_chart(fig, '05_daily_generation.png')

    fig, ax = plt.subplots(figsize=(7, 4.5))
    weekday = city.loc[~city.weekend, 'generated_kg_simulated'] / 1000
    weekend = city.loc[city.weekend, 'generated_kg_simulated'] / 1000
    ax.boxplot([weekday, weekend], tick_labels=['Weekday', 'Weekend'], showfliers=True)
    ax.set(ylabel='Generated tonnes per day', title='Weekday/weekend scenario variation')
    save_chart(fig, '06_weekend_generation.png')

    monthly = pd.read_csv(ROOT / '14_outputs/tables/phase3_sql/11_monthly_seasonality.csv')
    monthly['service_month'] = pd.to_datetime(monthly.service_month)
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.plot(monthly.service_month, monthly.mean_generated_kg_day / 1000,
             color='#166b8b', marker='o', label='Generation')
    ax1.set(ylabel='Mean generated tonnes/day', xlabel='Hypothetical 2026 month',
            title='Assumed seasonal demand and physical overflow')
    ax2 = ax1.twinx()
    ax2.plot(monthly.service_month, monthly.mean_overflow_l_day / 1000,
             color='#c04b2e', marker='s', label='Overflow')
    ax2.set_ylabel('Mean overflow thousand L/day')
    save_chart(fig, '07_monthly_pattern.png')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(bins.overflow_days, bins=25, color='#c04b2e', edgecolor='white')
    ax.set(xlabel='Days with positive physical overflow per bin', ylabel='Hypothetical bins',
           title='Simulated overflow-day burden')
    save_chart(fig, '08_overflow_bins.png')

    fig, ax = plt.subplots(figsize=(7, 6))
    scatter = ax.scatter(bins.longitude, bins.latitude, c=bins.overflow_days,
                         cmap='YlOrRd', s=18, alpha=.8, linewidths=0)
    fig.colorbar(scatter, ax=ax, label='Simulated overflow days in 2026')
    ax.set(xlabel='Longitude (real OSM road node)', ylabel='Latitude (real OSM road node)',
           title='Hypothetical bin risk at mapped road-node coordinates')
    save_chart(fig, '09_geographic_variation.png')

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].hist(route.successful_stops, bins=np.arange(route.successful_stops.max() + 2) - .5,
                 color='#5e548e', edgecolor='white')
    axes[0].set(xlabel='Successful stops/vehicle-day', ylabel='Vehicle-days',
                title='Assumed fleet assignment')
    axes[1].scatter(route.successful_stops, route.distance_km_assumed, alpha=.13, s=8, color='#b5651d')
    axes[1].set(xlabel='Successful stops', ylabel='Assumed distance (km)',
                title='Formula proxy: 5 + 0.35 km/stop')
    save_chart(fig, '10_route_proxy.png')

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].scatter(bins.gross_capacity_pct_day, bins.overflow_days, s=13, alpha=.35, color='#3a86a8')
    axes[0].set(xlabel='Gross generated volume / capacity (%/day)',
                ylabel='Annual overflow days', title='Mechanical scenario association')
    image = axes[1].imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
    axes[1].set_xticks(range(len(corr_vars)), ['Gross rate', 'Overflow days', 'Collections', 'Observed fill'], rotation=45, ha='right')
    axes[1].set_yticks(range(len(corr_vars)), ['Gross rate', 'Overflow days', 'Collections', 'Observed fill'])
    fig.colorbar(image, ax=axes[1], fraction=.045, label='Spearman rho')
    axes[1].set_title('Bin-level rank correlation')
    save_chart(fig, '11_bin_associations.png')

    totals = {'readings': int(city.scheduled_readings.sum()), 'observed_fill_readings': int(fill_stats['observed_n']),
        'generated_kg_simulated': float(city.generated_kg_simulated.sum()),
        'generated_tonnes_simulated': float(city.generated_kg_simulated.sum() / 1000),
        'overflow_l_simulated': float(city.overflow_l_simulated.sum()),
        'overflow_slots': int(city.overflowing_slots.sum()),
        'overflow_slot_pct': float(100 * city.overflowing_slots.sum() / city.scheduled_slots.sum()),
        'successful_collections': int(city.successful_collections.sum()),
        'partial_collections': int(service.loc[service.collection_status == 'partial', 'attempts'].iloc[0]),
        'missed_attempts': int(city.missed_collections.sum()),
        'attempts': int(timing['attempts']),
        'early_successes_lt35_pct': int(timing['early_successes_lt35_pct']),
        'near_full_or_overflow_attempts': int(timing['near_full_or_overflow_attempts']),
        'median_pre_service_fill_pct_true': float(timing['median_pre_service_fill_pct_true']),
        'weekday_mean_kg_day': float(weekday.mean() * 1000),
        'weekend_mean_kg_day': float(weekend.mean() * 1000),
        'bin_gross_rate_overflow_spearman': rho,
        'bin_gross_rate_overflow_pearson': pearson,
        'route_low_stop_days_lt4': int((route.successful_stops < 4).sum()),
        'route_active_days': int(len(route)), 'distance_origin': 'assumption'}
    (TABLES / 'phase3_metrics.json').write_text(json.dumps(totals, indent=2) + '\n', encoding='utf-8')

    top_zone = zones.sort_values('mean_arrival_l_bin_day', ascending=False).iloc[0]
    high_month = monthly.sort_values('mean_generated_kg_day', ascending=False).iloc[0]
    report = f'''# Phase 3 exploratory analysis — hypothetical Chennai bin scenario

**Evidence boundary.** All bin, reading, collection and vehicle-day measures below are synthetic. GCC ward IDs and OSM road-node coordinates are real source context, but the bins at those coordinates are hypothetical. Generated mass uses an assumed 0.12 kg/L density. This report does not estimate current municipal waste, route savings or operational performance in Chennai.

## Scope and reconciliation

The existing 1,000-bin scenario contains {totals['readings']:,} scheduled two-hour slots in 2026. {totals['observed_fill_readings']:,} have an observed fill value; missing telemetry remains in the denominator of scheduled slots. Phase 3 SQL reconciles all {totals['readings']:,} fact rows through bin- and zone-day marts and all {totals['attempts']:,} collection attempts. Bounded Python data frames and DuckDB aggregates underpin the charts; the full fact was not loaded into Pandas.

## Exploratory findings

- **Fill and collection.** The observed fill median is {fill_stats['median_fill_pct']:.1f}% (IQR {fill_stats['q1_fill_pct']:.1f}–{fill_stats['q3_fill_pct']:.1f}%). Bins experienced a median {bins.successful_collections.median():.0f} successful services over the scenario year. The distribution reflects the generator's 72%/48-hour due rule and sensor noise; it is not evidence of actual early collection.
- **Generated volume.** The simulator generated {totals['generated_tonnes_simulated']:,.1f} tonnes equivalent over the year under the fixed density assumption. Ward {top_zone.zone_id} has the highest normalized mean ({top_zone.mean_arrival_l_bin_day:.1f} L/hypothetical bin-day), which is an assumed demand hot spot, not an official ward waste estimate.
- **Calendar shape.** Mean generated mass is {totals['weekday_mean_kg_day']/1000:.1f} t/weekday and {totals['weekend_mean_kg_day']/1000:.1f} t/weekend day. This difference is expected because a 1.12 weekend multiplier was coded into the simulator. {high_month.service_month.strftime('%B')} has the highest simulated mean daily mass ({high_month.mean_generated_kg_day/1000:.1f} t/day), reflecting the imposed cosine seasonality. The local-hour chart similarly displays imposed intraday factors.
- **Overflow and service timing.** {totals['overflow_slots']:,} scheduled bin-slots ({totals['overflow_slot_pct']:.2f}%) had positive latent physical overflow, totalling {totals['overflow_l_simulated']:,.0f} L. {totals['successful_collections']:,} collections succeeded (including {totals['partial_collections']:,} partial services), and {totals['missed_attempts']:,} due attempts were missed. The missed-attempt share is {100*totals['missed_attempts']/totals['attempts']:.2f}%. The latent-truth diagnostic found {totals['early_successes_lt35_pct']:,} successful services under 35% pre-service fill, but {totals['near_full_or_overflow_attempts']:,} attempts at ≥95% pre-service fill or positive overflow. Median latent pre-service fill is {totals['median_pre_service_fill_pct_true']:.1f}%. These thresholds are exploratory flags, not municipal standards; the high stress level calls for calibration before policy comparisons.
- **Geography and associations.** The bin-level Spearman association between gross generated volume/capacity and overflow days is {rho:.2f} (Pearson {pearson:.2f}). Both quantities depend on the same generator and capacity assumptions, so this is not a causal or transferable estimate. The coordinate plot shows hypothetical risk at real mapped road nodes; it does not identify installed bins.
- **Vehicle-day proxy.** {totals['route_low_stop_days_lt4']:,} of {totals['route_active_days']:,} active vehicle-days have fewer than four successful stops. Distance is exactly the assumed 5 + 0.35 km per successful stop, so stops per km and its scatter cannot diagnose real routing inefficiency. No truck travel, depot access or service time was measured.

## Descriptive-statistics and outlier interpretation

`14_outputs/tables/phase3_eda/descriptive_statistics.csv` records mean, median, useful integer modes, sample variance and standard deviation, quartiles/IQR, 5th/95th percentiles, skewness and Tukey outlier counts at explicit city-day, bin-year or vehicle-day grains. A Tukey outlier is a screening flag, not a defective record. Sensor fill is clipped at 0–100%, so skewness and near-boundary frequencies are partly measurement design. The file does not attach naive confidence intervals to 4.38M correlated readings; the statistical report uses weekly aggregates and autocorrelation-aware intervals for two defined contrasts.

## Figures and next decision

Figures `01`–`11` in `14_outputs/charts/phase3/` cover distributions, normalized geography, calendar patterns, overflow, service, vehicle proxies and correlation. Review the 11.46% overflow-slot rate, latent timing flags, capacity and daily-service assumptions before any optimization claim. A field-calibration dataset or a range of clearly labelled scenarios is needed to judge real business significance. Forecasting and routing are intentionally outside Phase 3.
'''
    REPORT.write_text(report, encoding='utf-8')
    return totals


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
