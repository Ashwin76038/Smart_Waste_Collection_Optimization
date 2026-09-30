"""Observed-only 20-hour pre-service fill forecast; fixed chronological holdout."""
from phase4_common import ROOT,CFG,FC,REPORT,dump
import duckdb,numpy as np,pandas as pd,joblib
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FEATURES=['current_fill_pct','fill06','fill04','ma7_04','seasonal7_04','ewm7_04','recent_growth_pct','history_growth_pct','hours_since_collection','sensor_age_hours','capacity_l']+[f'target_dow_{i}' for i in range(7)]
BASELINES=['persistence','seasonal_naive7','moving_average7','exponential_smoothing7']

def dataset():
    c=duckdb.connect(str(ROOT/'03_data/processed/waste.duckdb'),read_only=True)
    d=c.execute('''WITH r AS (
      SELECT *, EXTRACT(HOUR FROM timestamp_utc+INTERVAL '5 hours 30 minutes') AS local_hour
      FROM fact_bin_readings)
      SELECT bin_id,CAST(service_date_local AS DATE) AS issue_date,
        ARG_MAX(fill_level_pct,timestamp_utc) FILTER (WHERE local_hour<=8 AND sensor_status='ok') AS current_fill_pct,
        MAX(timestamp_utc) FILTER (WHERE local_hour<=8 AND sensor_status='ok' AND fill_level_pct IS NOT NULL) AS last_sensor_utc,
        MAX(fill_level_pct) FILTER (WHERE local_hour=4 AND sensor_status='ok') AS fill04,
        MAX(fill_level_pct) FILTER (WHERE local_hour=6 AND sensor_status='ok') AS fill06,
        MAX(timestamp_utc) FILTER (WHERE local_hour<=8 AND collection_status IN ('collected','partial')) AS last_service_utc
      FROM r GROUP BY bin_id,issue_date ORDER BY bin_id,issue_date''').df()
    bins=c.execute('SELECT bin_id,zone_id,capacity_l FROM dim_bin').df();c.close()
    d=d.merge(bins,on='bin_id',validate='many_to_one').sort_values(['bin_id','issue_date'])
    d['issue_date']=pd.to_datetime(d.issue_date)
    d['issue_time_utc']=d.issue_date+pd.Timedelta(hours=2,minutes=30)
    d['target_time_utc']=d.issue_date+pd.Timedelta(hours=22,minutes=30)
    d['target_date']=d.issue_date+pd.Timedelta(days=1)
    g=d.groupby('bin_id',sort=False)
    d['target_fill_pct']=g.fill04.shift(-1)
    d['ma7_04']=g.fill04.transform(lambda s:s.rolling(7,min_periods=3).mean())
    d['ewm7_04']=g.fill04.transform(lambda s:s.ewm(span=7,adjust=False,min_periods=3).mean())
    d['seasonal7_04']=g.fill04.shift(6) # tomorrow's weekday, seven days earlier
    overnight=(d.fill04-g.current_fill_pct.shift(1)).clip(0,100)
    d['history_growth_pct']=overnight.groupby(d.bin_id).transform(lambda s:s.rolling(7,min_periods=3).mean())
    d['recent_growth_pct']=((d.current_fill_pct-d.fill06)/2).clip(0,50)
    d['last_service_utc']=d.groupby('bin_id').last_service_utc.ffill()
    d['hours_since_collection']=(d.issue_time_utc-d.last_service_utc).dt.total_seconds()/3600
    d['sensor_age_hours']=(d.issue_time_utc-d.last_sensor_utc).dt.total_seconds()/3600
    for i in range(7):d[f'target_dow_{i}']=(d.target_date.dt.dayofweek==i).astype(int)
    d['bin_holdout']=(d.bin_id%5==0)
    # Seven days of history before scored/training examples.
    d=d[d.issue_date>=pd.Timestamp('2026-01-08')].copy()
    d['split']=np.select([d.target_date<=pd.Timestamp('2026-06-30'),d.target_date<=pd.Timestamp('2026-08-31')],['train','validation'],default='test')
    d['data_origin']='synthetic'
    assert (d.last_sensor_utc.dropna()<=d.loc[d.last_sensor_utc.notna(),'issue_time_utc']).all()
    return d

def simple_predict(d,name):
    column={'persistence':'current_fill_pct','seasonal_naive7':'seasonal7_04','moving_average7':'ma7_04','exponential_smoothing7':'ewm7_04'}[name]
    # All fallback values available at issue; no future target imputation.
    return d[column].fillna(d.ma7_04).fillna(d.current_fill_pct).fillna(50).clip(0,100).to_numpy()

def metric(y,p):
    e=np.asarray(p)-np.asarray(y)
    return {'n':len(e),'mae_pct_points':float(np.mean(abs(e))),'rmse_pct_points':float(np.sqrt(np.mean(e*e))),
      'wape_pct':float(100*np.sum(abs(e))/np.sum(y)),
      'near_full_recall':float(np.sum((p>=95)&(y>=95))/max(1,np.sum(y>=95)))}

def run():
    d=dataset();valid=d.target_fill_pct.notna()&(d.target_date<=pd.Timestamp('2026-12-31'))
    train=d[valid&(d.split=='train')&~d.bin_holdout]
    val=d[valid&(d.split=='validation')&~d.bin_holdout]
    candidate=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=10))
    candidate.fit(train[FEATURES],train.target_fill_pct)
    val_preds={name:simple_predict(val,name) for name in BASELINES}
    val_preds['ridge']=candidate.predict(val[FEATURES]).clip(0,100)
    vm={name:metric(val.target_fill_pct.to_numpy(),p) for name,p in val_preds.items()}
    best_simple=min(BASELINES,key=lambda m:vm[m]['mae_pct_points'])
    selected='ridge' if vm['ridge']['mae_pct_points']<=.98*vm[best_simple]['mae_pct_points'] else best_simple
    calibration=abs(val.target_fill_pct.to_numpy()-val_preds[selected])
    widths={str(q):float(np.quantile(calibration,q,method='higher')) for q in [.8,.9,.95]}
    final_train=d[valid&(d.target_date<=pd.Timestamp('2026-08-31'))&~d.bin_holdout]
    final_model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=10))
    final_model.fit(final_train[FEATURES],final_train.target_fill_pct)
    joblib.dump(final_model,FC/'ridge_pipeline.joblib')
    rows=[];preds=[]
    for name in BASELINES+['ridge']:
        rows.append({'split':'validation','group':'known_bins','model':name,**vm[name]})
        for label,holdout in [('known_bins',False),('unseen_bins',True)]:
            test=d[valid&(d.split=='test')&(d.bin_holdout==holdout)]
            p=final_model.predict(test[FEATURES]).clip(0,100) if name=='ridge' else simple_predict(test,name)
            rows.append({'split':'test','group':label,'model':name,**metric(test.target_fill_pct.to_numpy(),p)})
            if name==selected:
                out=test[['bin_id','issue_time_utc','target_time_utc','target_fill_pct','data_origin']].copy()
                out['prediction_pct']=p;out['group']=label;out['model']=name
                out['lower90_pct']=(p-widths['0.9']).clip(0,100);out['upper90_pct']=(p+widths['0.9']).clip(0,100)
                preds.append(out)
    evaluation=pd.DataFrame(rows);evaluation.to_csv(FC/'forecast_evaluation.csv',index=False)
    predictions=pd.concat(preds);predictions.to_parquet(FC/'test_predictions.parquet',index=False)
    dispatch=d[d.issue_date==pd.Timestamp(CFG['issue_date_local'])].copy()
    dispatch['prediction_pct']=final_model.predict(dispatch[FEATURES]).clip(0,100) if selected=='ridge' else simple_predict(dispatch,selected)
    for q in [.8,.9,.95]:dispatch[f'upper{int(q*100)}_pct']=(dispatch.prediction_pct+widths[str(q)]).clip(0,100)
    dispatch['model']=selected
    # Do not export future labels into dispatcher feature table.
    dispatch=dispatch.drop(columns=['target_fill_pct','split'])
    dispatch.to_parquet(FC/'dispatch_forecasts.parquet',index=False)
    dispatch.to_csv(FC/'dispatch_forecasts.csv',index=False)
    card={'target':'observed fill at next-day 04:00 IST; 20 hours after 08:00 IST issue, before next scheduled service',
      'training_source':'fact_bin_readings observed-only; dim_bin capacity only; no simulation_truth or generator demand_factor',
      'features':FEATURES,'train_target_end':'2026-06-30','validation_target_start':'2026-07-01','validation_target_end':'2026-08-31',
      'refit_target_end':'2026-08-31','test_target_start':'2026-09-01','test_target_end':'2026-12-31',
      'bin_holdout':f"bin_id % 5 == 0; {d.loc[d.bin_holdout,'bin_id'].nunique()} bins never fitted or used for model selection; not contiguous spatial holdout",
      'selected_model':selected,'selection_rule':'ridge only if validation MAE is at least 2% better than the best simple baseline',
      'best_simple':best_simple,'empirical_interval_halfwidth_pct':widths,
      'test_interval_coverage90':float(((predictions.target_fill_pct>=predictions.lower90_pct)&(predictions.target_fill_pct<=predictions.upper90_pct)).mean()),
      'training_examples':len(train),'refit_examples':len(final_train),'validation_examples':len(val),'test_examples':len(predictions),
      'mape':'not reported: near-zero fills make percentage error unstable',
      'limitations':['One synthetic year; metrics do not establish real IoT performance.','Empirical interval from validation residuals; repeated-bin dependence prevents formal distribution-free coverage claim.','Baseline collection policy fixed; changed future interventions invalidate a direct reuse of baseline fill forecasts.','No calibrated overflow probability; priority uses forecast upper bound as a risk flag.']}
    dump(FC/'model_card.json',card)
    fig,ax=plt.subplots(figsize=(9,4.5))
    chart=evaluation[(evaluation.split=='test')&(evaluation.group=='known_bins')]
    ax.bar(chart.model,chart.mae_pct_points,color=['#788899' if m!=selected else '#087f8c' for m in chart.model])
    ax.set(ylabel='MAE (fill percentage points)',title='Synthetic 20-hour fill forecast: untouched Sep–Dec test')
    ax.tick_params(axis='x',rotation=18);fig.tight_layout()
    fig.savefig(FC/'forecast_test_mae.png',dpi=150);plt.close(fig)
    dump(FC/'feature_contract.json',{'n_dispatch':len(dispatch),'latest_model_training_target':'2026-08-31','dispatch_issue_local':CFG['issue_date_local']+' 08:00','feature_source_max_rule':'last_sensor_utc <= issue_time_utc','future_label_in_dispatch':False})
    print(evaluation.to_string(index=False));print('selected',selected,'interval coverage',card['test_interval_coverage90'])
if __name__=='__main__':run()
