"""Create editable PBIP/PBIR from the verified Phase 5 exports. Desktop saves PBIX.

No analysis, source data or model export is modified. Run from project root.
"""
from pathlib import Path
import json, re, csv, uuid, shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '12_powerbi' / 'desktop_project'
REPORT = OUT / 'Smart_Waste.Report'
MODEL = OUT / 'Smart_Waste.SemanticModel'
DATA = ROOT / '12_powerbi' / 'phase5_model'
BASE = 'https://developer.microsoft.com/json-schemas/fabric/'

def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')

def sid(s): return uuid.uuid5(uuid.NAMESPACE_URL, 'smart-waste/'+s).hex[:20]
def schema(s): return BASE+s+'/schema.json'

save(OUT/'Smart_Waste_Chennai_Coimbatore.pbip', {'$schema':schema('pbip/pbipProperties/1.0.0'),'version':'1.0','artifacts':[{'report':{'path':REPORT.name}}],'settings':{'enableAutoRecovery':True}})
save(REPORT/'definition.pbir', {'$schema':schema('item/report/definitionProperties/2.0.0'),'version':'4.0','datasetReference':{'byPath':{'path':'../'+MODEL.name}}})
save(MODEL/'definition.pbism', {'$schema':schema('item/semanticModel/definitionProperties/1.0.0'),'version':'1.0','settings':{}})

intcols=set('calendar_year month_number year_month_sort weekday_sunday_zero capacity_l vehicles_available bins scheduled_readings received_readings overflow_slots successful_collections missed_collections mean_fill_band_sort overflow_day_count successful_attempt_count early_success_count late_risk_attempt_count priority_rank tier required_bins bins_serviced full_capacity_l_required vehicle n'.split())
boolcols=set('weekend base_scenario required forecast_trigger network_accessible in_routing_pilot baseline_complete'.split())
floatcols=set('latitude longitude map_latitude map_longitude trigger_pct demand_multiplier fuel_price_multiplier fill_sum_pct max_observed_fill_pct generated_l overflow_l collected_kg pre_service_fill_pct baseline_overflow_l optimized_overflow_l overflow_l_avoided_modelled current_fill_pct prediction_pct upper90_pct mae_pct_points rmse_pct_points wape_pct near_full_recall baseline_km optimized_km km_saved distance_reduction_pct travel_hours_saved vehicle_hours_saved fuel_l_saved_assumed fuel_cost_inr_saved_historical_proxy tailpipe_co2_kg_saved_proxy distance_km travel_minutes load_l route_minutes load_kg_assumed volume_utilization_pct payload_utilization_pct'.split())
tables=[]
for file in sorted(DATA.glob('*.csv')):
    if not file.name.startswith(('dim_','fact_')): continue
    name=file.stem
    with file.open(encoding='utf-8-sig',newline='') as fh: columns=next(csv.reader(fh))
    cs=[]; mts=[]
    for c in columns:
        typ,mt='string','type text'
        if c in intcols: typ,mt='int64','Int64.Type'
        elif c in boolcols: typ,mt='boolean','type logical'
        elif c in floatcols: typ,mt='double','type number'
        elif c.endswith('_date'): typ,mt='dateTime','type date'
        elif c=='attempted_at_utc': typ,mt='dateTime','type datetime'
        obj={'name':c,'dataType':typ,'sourceColumn':c,'summarizeBy':'none'}
        if typ=='double': obj['formatString']='#,0.00'
        elif typ=='int64': obj['formatString']='#,0'
        elif typ=='dateTime': obj['formatString']='yyyy-MM-dd'
        if c in ('latitude','longitude'): obj['dataCategory']=c.title()
        if c=='mean_fill_band':obj['sortByColumn']='mean_fill_band_sort'
        if c=='month_name':obj['sortByColumn']='month_number'
        if c.endswith('_key') and c!='bin_key' or c in ('source_id','mean_fill_band_sort'):obj['isHidden']=True
        if name=='dim_date' and c=='service_date':obj['isKey']=True
        cs.append(obj); mts.append('{"'+c+'", '+mt+'}')
    expr=['let',f'    Source = Csv.Document(File.Contents("{file}"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Typed = Table.TransformColumnTypes(Headers, {'+', '.join(mts)+'}, "en-US")','in','    Typed']
    tab={'name':name,'columns':cs,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
    if name=='dim_date':tab['dataCategory']='Time'
    tables.append(tab)

text=(ROOT/'12_powerbi/PHASE5_MEASURES.dax').read_text(encoding='utf-8-sig')
text=re.sub(r'^//.*$', '',text,flags=re.M)
matches=list(re.finditer(r'^([^\n=]+) =\s*$', text,re.M))
measures=[]
for i,m in enumerate(matches):
    name=m.group(1).strip(); expr=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
    fmt='#,0.00'
    if name in ('Bin Count','Bin-Day Count','Overflow Bin-Days','Collection Attempts','Collections Completed','Bins Requiring Collection','High Priority Bins','Forecast-Triggered Bins','Access Review Bins','Pilot Bins Serviced'):fmt='#,0'
    measures.append({'name':name,'expression':expr.splitlines(),'formatString':fmt,'description':'Synthetic operational scenario. See PHASE5_MEASURES.dax for scope and denominator.','displayFolder':'Route pilot' if any(x in name for x in ('Route','Distance','Fuel','Travel','Pilot','Truck','Spill')) else 'Operations'})
extra={'Route Distance Km':'SUM ( fact_truck_route[distance_km] )','Generated Litres':'SUM ( fact_bin_day[generated_l] )'}
for n,e in extra.items():measures.append({'name':n,'expression':e,'formatString':'#,0.00'})
tables.append({'name':'KPI Measures','columns':[{'name':'_','dataType':'int64','sourceColumn':'_','isHidden':True}],'partitions':[{'name':'KPI Measures','mode':'import','source':{'type':'m','expression':'#table(type table [_ = Int64.Type], {{0}})'}}],'measures':measures})
links=[]
for parent,col,children in [('dim_city','city_id',['dim_bin','dim_zone','dim_scenario','fact_city_day','fact_forecast_score']),('dim_date','service_date',['fact_city_day','fact_bin_day','fact_zone_day','fact_collection_attempt']),('dim_bin','bin_key',['fact_bin_day','fact_collection_attempt','fact_dispatch_snapshot']),('dim_zone','zone_key',['fact_zone_day']),('dim_scenario','scenario_key',['fact_route_scenario','fact_truck_route','fact_counterfactual'])]:
    for child in children:links.append({'name':sid(parent+child),'fromTable':child,'fromColumn':col,'fromCardinality':'many','toTable':parent,'toColumn':col,'toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
save(MODEL/'model.bim',{'name':'Smart_Waste','compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':tables,'relationships':links,'annotations':[{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}})

definition=REPORT/'definition'
save(definition/'version.json',{'$schema':schema('item/report/definition/versionMetadata/1.0.0'),'version':'2.0.0'})
save(definition/'report.json',{'$schema':schema('item/report/definition/report/3.0.0'),'themeCollection':{'customTheme':{'name':'theme.json','reportVersionAtImport':{'visual':'1.8.101','report':'2.0.101','page':'1.3.101'},'type':'RegisteredResources'}},'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'theme.json','path':'theme.json','type':'CustomTheme'}]}],'settings':{'useStylableVisualContainerHeader':True,'allowChangeFilterTypes':True,'useEnhancedTooltips':True}})
(REPORT/'StaticResources/RegisteredResources').mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'12_powerbi/phase5_theme.json',REPORT/'StaticResources/RegisteredResources/theme.json')

def lit(v):
    x=('true' if v else 'false') if isinstance(v,bool) else str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':x}}}
def color(v): return {'solid':{'color':lit(v)}}
def prop(**kw):return [{'properties':kw}]
def field(table,col,measure=False):return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':col}}
def col(t,c):return (t,c,False)
def meas(m):return ('KPI Measures',m,True)
def projection(f):return {'field':field(*f),'queryRef':f[0]+'.'+f[1],'nativeQueryRef':f[1]}
titles=['Executive Overview','Waste & Bin Analysis','Geographic Intelligence','Route Optimization','Forecasting & Planning']
pages=[sid(t) for t in titles]
save(definition/'pages/pages.json',{'$schema':schema('item/report/definition/pagesMetadata/1.0.0'),'pageOrder':pages,'activePageName':pages[0]})
counts={}
def visual(page,kind,title,x,y,w,h,roles=None,objects=None,filters=None,sort=None):
    count=counts.get(page,0);counts[page]=count+1
    name=sid(page+str(count)+title)
    v={'visualType':kind,'visualContainerObjects':{'title':prop(show=lit(True),text=lit(title),fontFamily=lit('Segoe UI'),fontSize=lit(12),fontColor=color('#162B36')),'background':prop(show=lit(True),color=color('#FFFFFF'),transparency=lit(0)),'border':prop(show=lit(False))}}
    if objects:v['objects']=objects
    if roles:v['query']={'queryState':{role:{'projections':[projection(f) for f in fs]} for role,fs in roles.items()}}
    if sort and roles:v['query']['sortDefinition']={'sort':[{'field':field(*sort[0]),'direction':sort[1]}]}
    obj={'$schema':schema('item/report/definition/visualContainer/2.4.0'),'name':name,'position':{'x':x,'y':y,'z':count*1000,'width':w,'height':h,'tabOrder':count*1000},'visual':v}
    if filters:obj['filterConfig']={'filters':filters}
    save(definition/'pages'/page/'visuals'/name/'visual.json',obj)
    return obj
def txt(p,text,x,y,w,h,size=12,bg='#F7FAF9',fg='#162B36'):
    obj=visual(p,'textbox','',x,y,w,h,objects={'general':prop(paragraphs=[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':fg}}]}])})
    obj['visual']['visualContainerObjects']={'title':prop(show=lit(False)),'background':prop(show=lit(True),color=color(bg),transparency=lit(0))}
    save(definition/'pages'/p/'visuals'/obj['name']/'visual.json',obj)
def filteron(t,c,value):
    return {'name':sid(t+c+str(value)),'field':field(t,c),'type':'Categorical','filter':{'Version':2,'From':[{'Name':'s','Entity':t,'Type':0}],'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':c}}],'Values':[[{'Literal':{'Value':"'"+str(value)+"'"}}]]}}}]},'howCreated':'User'}
def slicer(p,t,c,title,x,w=220,single=False,value=None):
    objects={'data':prop(mode=lit('Dropdown')),'header':prop(show=lit(True),text=lit(title)),'selection':prop(singleSelect=lit(single),selectAllCheckboxEnabled=lit(not single))}
    if value:objects['general']=prop(filter={'filter':filteron(t,c,value)['filter']})
    obj=visual(p,'slicer',title,x,90,w,76,{'Values':[col(t,c)]},objects)
    obj['visual']['visualContainerObjects']['title']=prop(show=lit(False))
    obj['visual']['visualContainerObjects']['padding']=prop(top=lit(4),bottom=lit(4),left=lit(6),right=lit(6))
    save(definition/'pages'/p/'visuals'/obj['name']/'visual.json',obj)
    return obj
def cards(p,names,y=178):
    width=(1232-16*(len(names)-1))/len(names)
    for i,n in enumerate(names):visual(p,'card',n,24+i*(width+16),y,width,100,{'Values':[meas(n)]},{'labels':prop(fontSize=lit(25),color=color('#147D78'),labelDisplayUnits=lit(1)),'categoryLabels':prop(show=lit(False))})
def table(p,title,x,y,w,h,fs,sort=None):return visual(p,'tableEx',title,x,y,w,h,{'Values':fs},{'grid':prop(textSize=lit(10))},sort=sort)

for i,(p,title) in enumerate(zip(pages,titles)):
    pg={'$schema':schema('item/report/definition/page/2.0.0'),'name':p,'displayName':title,'displayOption':'FitToPage','width':1280,'height':800,'objects':{'background':prop(color=color('#F7FAF9'),transparency=lit(0))}}
    if i==4:pg['filterConfig']={'filters':[filteron('fact_forecast_score','split','test'),filteron('fact_forecast_score','evaluation_group','known_bins')]}
    save(definition/'pages'/p/'page.json',pg)
    txt(p,'SMART WASTE  /  '+title.upper(),24,12,1232,43,22,'#162B36','#FFFFFF')
    txt(p,'Tamil Nadu  |  Synthetic operations on real geography  |  Chennai & Coimbatore',24,57,1232,25,11)
    slicer(p,'dim_city','city_name','Study city',24,single=i>=2,value='Chennai' if i>=2 else None)
    if i<3:slicer(p,'dim_date','service_date','Historical date · 2026',260,270)
    if i==1:slicer(p,'dim_bin','ward_label','Ward',546,360)
    if i==3:slicer(p,'dim_scenario','scenario','Route scenario',260,370,True,'base_3_trucks')
    if i>=3:txt(p,'FROZEN PILOT · 23 SEP 2026, 08:00 IST\n'+('One city + one scenario. Alternatives must not be summed.' if i==3 else '20-hour fill horizon · test / known bins evaluation'),660,92,590,62,12)
    txt(p,'Synthetic operational demonstration. No real municipal performance, causal effects or annualized route savings claimed.',24,714,1232,27,10)
    for j,name in enumerate(titles):
        obj=visual(p,'actionButton','',24+j*249,750,236,38,objects={'text':prop(show=lit(True))+[{'selector':{'id':'default'},'properties':{'text':lit(str(j+1)+'  '+name),'fontSize':lit(10),'fontColor':color('#FFFFFF' if i==j else '#162B36')}}],'fill':prop(show=lit(True))+[{'selector':{'id':'default'},'properties':{'fillColor':color('#147D78' if i==j else '#E6EFED')}}]})
        obj['visual']['visualContainerObjects']['title']=prop(show=lit(False))
        obj['visual']['visualContainerObjects']['visualLink']=prop(show=lit(True),type=lit('PageNavigation'),navigationSection=lit(pages[j]),tooltip=lit('Open '+name))
        save(definition/'pages'/p/'visuals'/obj['name']/'visual.json',obj)

p=pages[0]
cards(p,['Bin Count','Total Waste Collected (t)','Average Bin Fill %','Overflow Slot %','Collections Completed'])
visual(p,'lineChart','How does generated volume change through the year?',24,294,760,268,{'Category':[col('dim_date','service_date')],'Y':[meas('Generated L per Bin-Day')],'Series':[col('dim_city','city_name')]},sort=(col('dim_date','service_date'),'Ascending'))
txt(p,'MANAGEMENT LENS\n\nCompare litres per bin-day, not city totals.\nOverflow is simulated physical spill.\nEarly service is a diagnostic, not waste.\nReview flagged wards before changing service.',802,294,454,268,15,'#E6EFED')
table(p,'Normalized city comparison · synthetic scenarios',24,578,1232,120,[col('dim_city','city_name')]+[meas(m) for m in ['Generated L per Bin-Day','Average Bin Fill %','Overflow Slot %','Collection Completion %','Early Collection % (simulated <35%)']])
p=pages[1]
visual(p,'clusteredBarChart','Which wards have the highest spill per bin-day?',24,178,710,272,{'Category':[col('dim_bin','ward_label')],'Y':[meas('Overflow L per Bin-Day')],'Tooltips':[meas(x) for x in ['Bin Generated L per Bin-Day','Overflow Bin-Days','Collections Completed']]},sort=(meas('Overflow L per Bin-Day'),'Descending'))
visual(p,'columnChart','Distribution of daily mean fill',750,178,506,272,{'Category':[col('fact_bin_day','mean_fill_band')],'Y':[meas('Bin-Day Count')]},sort=(col('fact_bin_day','mean_fill_band'),'Ascending'))
table(p,'Bin-level service and overflow audit',24,466,1232,232,[col('dim_bin','ward_label'),col('dim_bin','bin_key'),col('dim_bin','capacity_l')]+[meas(x) for x in ['Overflow Bin-Days','Generated Litres','Collections Completed']],sort=(meas('Overflow Bin-Days'),'Descending'))
p=pages[2]
mapobj=visual(p,'map','Where are recurring overflow hotspots?',24,178,730,370,{'Category':[col('dim_bin','bin_key')],'Y':[col('dim_bin','latitude')],'X':[col('dim_bin','longitude')],'Size':[meas('Overflow Bin-Days')],'Tooltips':[col('dim_bin','ward_label'),col('dim_bin','capacity_l'),meas('Overflow L per Bin-Day')]})
for role,c in [('Y','latitude'),('X','longitude')]:
    pj=mapobj['visual']['query']['queryState'][role]['projections'][0]
    pj['field']={'Aggregation':{'Expression':field('dim_bin',c),'Function':1}}
    pj['queryRef']='Avg(dim_bin.'+c+')'
save(definition/'pages'/p/'visuals'/mapobj['name']/'visual.json',mapobj)
table(p,'Ward risk and frozen dispatch priority',770,178,486,370,[col('dim_bin','ward_label')]+[meas(x) for x in ['Overflow L per Bin-Day','Bins Requiring Collection','Access Review Bins']],sort=(meas('Overflow L per Bin-Day'),'Descending'))
table(p,'Snapshot queue · 23 Sep 2026 · ignores historical date selection',24,564,1232,134,[col('dim_bin','bin_key'),col('dim_bin','ward_label'),col('fact_dispatch_snapshot','dispatch_status'),col('fact_dispatch_snapshot','priority_rank'),col('fact_dispatch_snapshot','reasons')],sort=(col('fact_dispatch_snapshot','priority_rank'),'Ascending'))
p=pages[3]
cards(p,['Pilot Bins Serviced','Baseline Route Km','Optimized Route Km','Distance Saved Km','Distance Reduction %'])
visual(p,'clusteredColumnChart','Matched fleet comparison · road kilometres',24,294,435,218,{'Category':[col('fact_truck_route','method')],'Y':[meas('Route Distance Km')]})
table(p,'Truck routes · reserved capacity, not measured payload',475,294,781,218,[col('fact_truck_route',x) for x in ['method','vehicle','bins','distance_km','volume_utilization_pct','route_minutes']])
cards(p,['Fuel Saved L (assumed)','Fuel Cost Saved INR (proxy)','Modeled Spill Avoided L (24h)'],528)
table(p,'Feasibility and exception reason',24,644,1232,54,[col('dim_scenario','status'),col('fact_route_scenario','reason')])
p=pages[4]
cards(p,['Bins Requiring Collection','Forecast-Triggered Bins','Access Review Bins'])
visual(p,'clusteredBarChart','Forecast MAE · lower is better · percentage points',24,294,540,230,{'Category':[col('fact_forecast_score','model')],'Y':[meas('Forecast MAE (pp)')],'Tooltips':[meas('Forecast Near-Full Recall %')]},sort=(meas('Forecast MAE (pp)'),'Ascending'))
txt(p,'OPERATIONAL GUARDRAILS\n\nForecasts miss some near-full bins; retain rules.\n90% prediction bands have undercoverage.\nReview network access before dispatch.\nQueue is a fixed simulation snapshot.',580,294,676,230,16,'#E6EFED')
table(p,'Collection queue · review tier, reason and access',24,540,1232,158,[col('dim_bin','bin_key'),col('dim_bin','ward_label')]+[col('fact_dispatch_snapshot',x) for x in ['current_fill_pct','prediction_pct','tier','reasons','network_accessible']],sort=(col('fact_dispatch_snapshot','tier'),'Ascending'))
save(OUT/'build_receipt.json',{'model_tables':len(tables),'csv_tables':14,'relationships':len(links),'measures':len(measures),'pages':dict(zip(titles,[counts[p] for p in pages])),'execution_status':'Authored project; Desktop refresh, rendering and PBIX save required.'})
print(json.dumps({'project':str(OUT),'tables':len(tables),'measures':len(measures),'visuals':sum(counts.values())}))

