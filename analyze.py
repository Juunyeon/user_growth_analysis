"""从 MySQL 导出表清理并计算指标；pandas/numpy + 标准库 SVG，无需绘图库。"""
from pathlib import Path
import calendar, hashlib, html, json, math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
START=pd.Timestamp('2017-06-01'); END=pd.Timestamp('2018-06-01')

def save(df,name,index=False):
    df.to_csv(ROOT/'data'/f'{name}.csv',index=index,encoding='utf-8-sig',float_format='%.8f')

def ratio(a,b):
    return a/b.replace(0,np.nan) if isinstance(b,pd.Series) else a/b if b else np.nan

def svg_chart(df,columns,title,name,percent=False):
    """折线图；缺失值断线，不把不成熟指标画成零。"""
    w,h=1100,430; left,top,right,bottom=85,65,40,85
    pw,ph=w-left-right,h-top-bottom
    values=df[columns].to_numpy(dtype=float)
    maximum=np.nanmax(values) if np.isfinite(values).any() else 1
    maximum=max(maximum*1.1,0.01)
    colors=['#2563eb','#0d9488','#e58b17','#9333ea']
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           '<rect width="100%" height="100%" fill="#fff"/>',
           '<style>text{font-family:"Microsoft YaHei",Arial,sans-serif;fill:#334155;font-size:12px}</style>',
           f'<text x="{left}" y="30" style="font-size:20px;font-weight:bold">{html.escape(title)}</text>']
    for t in range(5):
        val=maximum*t/4;y=top+ph*(1-t/4)
        label=f'{val:.1%}' if percent else f'{val:,.2f}' if maximum<10 else f'{val:,.0f}'
        parts += [f'<line x1="{left}" y1="{y}" x2="{w-right}" y2="{y}" stroke="#e2e8f0"/>',f'<text x="{left-12}" y="{y+4}" text-anchor="end">{label}</text>']
    n=len(df)
    for k,col in enumerate(columns):
        segments=[]; current=[]
        for i,v in enumerate(df[col]):
            if pd.isna(v):
                if current: segments.append(current);current=[]
            else: current.append(f'{left+pw*i/max(n-1,1):.1f},{top+ph*(1-v/maximum):.1f}')
        if current:segments.append(current)
        for seg in segments:parts.append(f'<polyline points="{" ".join(seg)}" stroke="{colors[k]}" fill="none" stroke-width="2.5"/>')
        parts.append(f'<text x="{left+k*220}" y="{h-10}" style="fill:{colors[k]}">{html.escape(col)}</text>')
    for i in sorted(set(np.linspace(0,max(n-1,0),min(n,9)).astype(int))):
        label=str(df.index[i])[:10]
        parts.append(f'<text x="{left+pw*i/max(n-1,1)}" y="{h-bottom+25}" text-anchor="middle">{html.escape(label)}</text>')
    parts.append('</svg>');(ROOT/'figures'/f'{name}.svg').write_text('\n'.join(parts),encoding='utf-8')

def heatmap(matrix,title,name,percent=True):
    cellw,cellh=70,29; w=170+len(matrix.columns)*cellw;h=105+len(matrix)*cellh
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">', '<rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:"Microsoft YaHei",Arial,sans-serif;font-size:12px;fill:#334155}</style>',f'<text x="15" y="27" style="font-size:18px">{html.escape(title)}</text>']
    for j,col in enumerate(matrix.columns):parts.append(f'<text x="{150+j*cellw}" y="60" text-anchor="middle">{html.escape(str(col))}</text>')
    for i,(idx,row) in enumerate(matrix.iterrows()):
        y=73+i*cellh;parts.append(f'<text x="12" y="{y+19}">{str(idx)[:10]}</text>')
        for j,v in enumerate(row):
            x=116+j*cellw
            color='#f1f5f9' if pd.isna(v) else f'rgb({int(240-160*min(v,1))},{int(249-100*min(v,1))},255)'
            label='—' if pd.isna(v) else f'{v:.1%}' if percent else f'{v:.2f}'
            parts += [f'<rect x="{x}" y="{y}" width="{cellw-2}" height="{cellh-2}" fill="{color}"/>',f'<text x="{x+cellw/2}" y="{y+19}" text-anchor="middle">{label}</text>']
    parts.append('</svg>');(ROOT/'figures'/f'{name}.svg').write_text('\n'.join(parts),encoding='utf-8')

def bar_chart(df,columns,title,name):
    w,h=1100,430;left,top,pw,ph=85,65,970,275
    colors=['#2563eb','#0d9488'];n=len(df);group=pw/n;bar=group*.7/len(columns)
    maximum=max(float(np.nanmax(df[columns].to_numpy(dtype=float)))*1.16,0.01)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:"Microsoft YaHei",Arial,sans-serif;font-size:12px;fill:#334155}</style>',f'<text x="{left}" y="30" style="font-size:20px;font-weight:bold">{html.escape(title)}</text>']
    for t in range(5):
        y=top+ph*(1-t/4);val=maximum*t/4
        parts += [f'<line x1="{left}" y1="{y}" x2="{left+pw}" y2="{y}" stroke="#e2e8f0"/>',f'<text x="{left-12}" y="{y+4}" text-anchor="end">{val:.2f}</text>']
    for i,(idx,row) in enumerate(df.iterrows()):
        x=left+group*(i+.15)
        parts.append(f'<text x="{left+group*(i+.5)}" y="365" text-anchor="middle">{idx}</text>')
        for j,col in enumerate(columns):
            val=row[col];xx=x+j*bar
            if pd.isna(val):parts.append(f'<text x="{xx+bar/2}" y="330" text-anchor="middle">NA</text>');continue
            height=val/maximum*ph;yy=top+ph-height
            parts += [f'<rect x="{xx}" y="{yy}" width="{bar-3}" height="{height}" fill="{colors[j]}"/>',f'<text x="{xx+bar/2}" y="{yy-6}" text-anchor="middle">{val:.2f}</text>']
    for j,col in enumerate(columns):parts.append(f'<text x="{left+j*230}" y="400" style="fill:{colors[j]}">{html.escape(col)}</text>')
    parts.append('<text x="700" y="400">NA：无费用记录，非零成本</text></svg>')
    (ROOT/'figures'/f'{name}.svg').write_text('\n'.join(parts),encoding='utf-8')

def main():
    d=ROOT/'data/mysql_extract'
    v=pd.read_csv(d/'visits.csv',dtype={'uid':'string'},parse_dates=['start_ts','end_ts'])
    o=pd.read_csv(d/'orders.csv',dtype={'uid':'string'},parse_dates=['buy_ts'])
    c=pd.read_csv(d/'costs.csv',parse_dates=['dt'])
    su=pd.read_csv(d/'user_acquisition.csv',dtype={'uid':'string'},parse_dates=['first_visit','last_visit','first_purchase'])
    audit={'raw_rows':{'visits':len(v),'orders':len(o),'costs':len(c)},'nulls':{},'duplicates':{}}
    for key,df in [('visits',v),('orders',o),('costs',c)]:
        audit['nulls'][key]=df.isna().sum().to_dict()
        cols=[x for x in df.columns if x!='row_id']
        audit['duplicates'][key]=int(df.duplicated(cols).sum())
        df.drop_duplicates(cols,inplace=True)
    assert not v[['uid','start_ts','source_id']].isna().any().any()
    assert not o[['uid','buy_ts','revenue']].isna().any().any()
    assert not c[['source_id','dt','costs']].isna().any().any()
    assert (o.revenue>=0).all() and (c.costs>=0).all()
    assert not c.duplicated(['source_id','dt']).any(), '重复费用键需要人工核实'
    audit['invalid_duration_rows']=int((v.end_ts<v.start_ts).sum())
    save(v[v.end_ts<v.start_ts],'invalid_session_duration')
    v['duration_seconds']=(v.end_ts-v.start_ts).dt.total_seconds().where(v.end_ts>=v.start_ts)
    audit['orders_outside_window']=int((~o.buy_ts.between(START,END,inclusive='left')).sum())
    audit['revenue_outside_window']=float(o.loc[~o.buy_ts.between(START,END,inclusive='left'),'revenue'].sum())
    outside_orders=o.loc[~o.buy_ts.between(START,END,inclusive='left')].copy()
    outside_orders['exclusion_reason']='outside_analysis_window'
    v=v[v.start_ts.between(START,END,inclusive='left')].copy()
    o=o[o.buy_ts.between(START,END,inclusive='left')].copy()
    c=c[c.dt.between(START,END,inclusive='left')].copy()
    v.sort_values(['uid','start_ts','source_id','device','row_id'],inplace=True)
    ties=v.groupby(['uid','start_ts']).source_id.nunique()
    audit['same_time_multichannel_user_timestamp_groups']=int((ties>1).sum())
    u=v.drop_duplicates('uid').set_index('uid')[['start_ts','source_id','device']].rename(columns={'start_ts':'first_visit','source_id':'first_source','device':'first_device'})
    u['first_date']=u.first_visit.dt.normalize();u['cohort_month']=u.first_visit.dt.to_period('M').astype(str)
    o=o.merge(u[['first_visit','first_source','cohort_month']],left_on='uid',right_index=True,how='left',validate='many_to_one')
    audit['unmatched_orders']=int(o.first_visit.isna().sum())
    audit['orders_before_first_visit']=int((o.buy_ts<o.first_visit).sum())
    audit['revenue_before_first_visit']=float(o.loc[o.buy_ts<o.first_visit,'revenue'].sum())
    excluded=o[o.first_visit.isna() | (o.buy_ts<o.first_visit)].copy()
    excluded['exclusion_reason']=np.where(excluded.first_visit.isna(),'no_visit_match','before_first_visit')
    save(pd.concat([outside_orders,excluded],ignore_index=True),'excluded_orders')
    o=o[o.first_visit.notna() & (o.buy_ts>=o.first_visit)].copy()
    u=u.join(o.groupby('uid').agg(first_purchase=('buy_ts','min'),orders=('row_id','size'),revenue=('revenue','sum')))
    u[['orders','revenue']]=u[['orders','revenue']].fillna(0);u['converted']=u.first_purchase.notna()
    u['purchase_delay_hours']=(u.first_purchase-u.first_visit).dt.total_seconds()/3600
    # 与 MySQL 独立聚合校验，阻止一对多关联导致收入膨胀。
    su=su.set_index('uid').reindex(u.index)
    checks={'mysql_python_user_count':len(su)==len(u) and su.first_visit.notna().all(),
      'mysql_python_first_visit':u.first_visit.equals(su.first_visit),
      'mysql_python_first_source':bool((u.first_source==su.first_source).all()),
      'mysql_python_order_counts':bool((u.orders==su.order_count).all()),
      'mysql_python_revenue':bool(np.allclose(u.revenue,su.revenue)),
      'mysql_python_first_purchase':bool(((u.first_purchase==su.first_purchase)|(u.first_purchase.isna()&su.first_purchase.isna())).all())}
    assert all(checks.values()),checks
    days=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    ud=v.assign(date=v.start_ts.dt.normalize())[['uid','date']].drop_duplicates()
    ud=ud.merge(u[['first_date','cohort_month']],left_on='uid',right_index=True,validate='many_to_one')
    ud['age_day']=(ud.date-ud.first_date).dt.days
    daily=pd.DataFrame(index=days);daily.index.name='date'
    daily['new_users']=u.groupby('first_date').size().reindex(days,fill_value=0)
    daily['dau']=ud.groupby('date').uid.nunique().reindex(days,fill_value=0)
    daily['wau']=[ud.loc[ud.date.between(t-pd.Timedelta(days=6),t),'uid'].nunique() for t in days]
    daily['mau']=[ud.loc[ud.date.between(t-pd.Timedelta(days=29),t),'uid'].nunique() for t in days]
    daily['dau_mau']=daily.dau/daily.mau;daily['wau_mau']=daily.wau/daily.mau
    daily['new_users_7d_mean']=daily.new_users.rolling(7,min_periods=7).mean()
    daily['wau_full_window']=daily.index>=START+pd.Timedelta(days=6)
    daily['mau_full_window']=daily.index>=START+pd.Timedelta(days=29)
    daily['dau_mau_full_window']=daily.dau_mau.where(daily.mau_full_window)
    daily['wau_mau_full_window']=daily.wau_mau.where(daily.mau_full_window)
    save(daily,'daily_growth_activity',True)
    suspect_days=daily.index[daily.dau<10]
    audit['low_traffic_days_below_10_dau']=[str(x.date()) for x in suspect_days]
    audit['missing_cost_dates_by_observed_channel']={str(int(s)): [str(x.date()) for x in days.difference(pd.DatetimeIndex(g.dt))] for s,g in c.groupby('source_id')}
    ud['month']=ud.date.dt.to_period('M').astype(str)
    monthly=daily.groupby(daily.index.to_period('M').astype(str)).agg(new_users=('new_users','sum'),avg_dau=('dau','mean'))
    monthly.index.name='month';monthly['calendar_mau']=ud.groupby('month').uid.nunique()
    monthly['new_users_mom']=monthly.new_users.pct_change()
    monthly['calendar_stickiness']=monthly.avg_dau/monthly.calendar_mau
    save(monthly,'monthly_growth_activity',True)
    retention=[]
    return_counts=ud.groupby(['first_date','age_day']).uid.nunique()
    for cohort,group in u.groupby('first_date'):
        row={'cohort_date':cohort,'cohort_users':len(group)}
        for n in [1,7,30]:
            mature=cohort+pd.Timedelta(days=n)<END
            returned=return_counts.get((cohort,n),0) if mature else np.nan
            row[f'd{n}_eligible']=len(group) if mature else 0
            row[f'd{n}_returned']=returned;row[f'd{n}_retention']=returned/len(group)
        retention.append(row)
    ret=pd.DataFrame(retention);save(ret,'retention_daily_cohort')
    sensitivity=[]
    for n in [1,7,30]:
        eligible=(ret[f'd{n}_eligible']>0)&~ret.cohort_date.isin(suspect_days)&~(ret.cohort_date+pd.Timedelta(days=n)).isin(suspect_days)
        denominator=int(ret.loc[eligible,f'd{n}_eligible'].sum())
        numerator=int(ret.loc[eligible,f'd{n}_returned'].sum())
        sensitivity.append({'horizon_days':n,'eligible_excluding_flagged_dates':denominator,'returned_excluding_flagged_dates':numerator,'retention_excluding_flagged_dates':ratio(numerator,denominator)})
    save(pd.DataFrame(sensitivity),'retention_sensitivity')
    retm=ret.assign(month=ret.cohort_date.dt.to_period('M').astype(str))
    retm=retm.groupby('month').sum(numeric_only=True)
    for n in [1,7,30]: retm[f'd{n}_retention']=ratio(retm[f'd{n}_returned'],retm[f'd{n}_eligible'])
    save(retm,'retention_monthly_summary',True)
    cohorts=sorted(u.cohort_month.unique()); matrix=pd.DataFrame(index=cohorts,columns=range(len(cohorts)),dtype=float)
    active_month_counts=ud[['uid','cohort_month','month']].drop_duplicates().groupby(['cohort_month','month']).size()
    for cohort in cohorts:
        base=pd.Period(cohort,'M'); size=int((u.cohort_month==cohort).sum())
        for age in range(len(cohorts)):
            month=base+age
            if month.end_time<END:
                matrix.loc[cohort,age]=active_month_counts.get((cohort,str(month)),0)/size
    matrix.index.name='cohort_month';matrix.columns=[f'M{x}' for x in matrix.columns]
    save(matrix,'cohort_monthly_visit_retention',True)
    # 生命周期为月末快照；当前30天/之前30天窗口，四类互斥且覆盖所有已知用户。
    states=[];previous=None;transitions=[]
    for period in pd.period_range(START,END-pd.Timedelta(days=1),freq='M'):
        stop=period.end_time.normalize()+pd.Timedelta(days=1);begin=stop-pd.Timedelta(days=30)
        known=u[u.first_visit<stop]
        current=set(v.loc[v.start_ts.between(begin,stop,inclusive='left'),'uid'])
        prior=set(v.loc[v.start_ts.between(begin-pd.Timedelta(days=30),begin,inclusive='left'),'uid'])
        status=pd.Series('dormant',index=known.index,name='state')
        active=status.index.isin(current);new=known.first_visit>=begin
        status.loc[active & new]='new'
        status.loc[active & ~new & status.index.isin(prior)]='continuing'
        status.loc[active & ~new & ~status.index.isin(prior)]='returned'
        counts=status.value_counts().reindex(['new','continuing','dormant','returned'],fill_value=0)
        row={'month':str(period),'known_users':len(known),'current_window_start':str(begin.date()),'prior_window_complete':begin-pd.Timedelta(days=30)>=START,**counts.to_dict()}
        assert counts.sum()==len(known);states.append(row)
        if previous is not None:
            joined=previous.to_frame('from').join(status.rename('to'),how='inner')
            for (a,b),n in joined.groupby(['from','to']).size().items():transitions.append({'month':str(period),'from':a,'to':b,'users':n})
        previous=status
    life=pd.DataFrame(states).set_index('month');save(life,'lifecycle_monthly',True);save(pd.DataFrame(transitions),'lifecycle_transitions')
    conversion=[]
    for cohort,g in u.groupby('cohort_month'):
        row={'cohort_month':cohort,'users':len(g),'observed_buyers':int(g.converted.sum()),'observed_conversion':float(g.converted.mean())}
        for horizon in [1,7,30]:
            eligible=g.first_visit+pd.Timedelta(days=horizon)<=END
            buyers=eligible & g.converted & (g.first_purchase<g.first_visit+pd.Timedelta(days=horizon))
            row[f'eligible_{horizon}d']=int(eligible.sum());row[f'buyers_{horizon}d']=int(buyers.sum());row[f'conversion_{horizon}d']=ratio(int(buyers.sum()),int(eligible.sum()))
        conversion.append(row)
    conv=pd.DataFrame(conversion);save(conv,'conversion_cohort')
    channel=u.groupby('first_source').agg(new_users=('first_visit','size'),buyers=('converted','sum'),orders=('orders','sum'),revenue=('revenue','sum'))
    channel.index.name='source_id';channel=channel.join(c.groupby('source_id').costs.sum().rename('costs'),how='outer')
    channel['visiting_users_any_touch']=v.groupby('source_id').uid.nunique()
    channel['conversion']=channel.buyers/channel.new_users
    channel['cac_visitor']=ratio(channel.costs,channel.new_users);channel['cac_buyer']=ratio(channel.costs,channel.buyers)
    channel['observed_ltv_per_visitor']=channel.revenue/channel.new_users
    channel['observed_ltv_per_buyer']=channel.revenue/channel.buyers
    channel['roas']=ratio(channel.revenue,channel.costs)
    channel['marketing_surplus_rate']=channel.roas-1
    save(channel,'channel_performance',True)
    # 固定30日收入LTV：按完整成熟的首访月份计算，避免新老cohort观察期不同。
    o['age_seconds']=(o.buy_ts-o.first_visit).dt.total_seconds()
    rev30=o[o.age_seconds<30*86400].groupby('uid').revenue.sum()
    u['revenue_30d']=u.index.to_series().map(rev30).fillna(0).where(u.first_visit+pd.Timedelta(days=30)<=END)
    u['purchased_30d']=(u.first_purchase<u.first_visit+pd.Timedelta(days=30)) & u.converted
    c['month']=c.dt.dt.to_period('M').astype(str)
    cm=c.groupby(['source_id','month']).costs.sum()
    ltv=[]
    for (cohort,source),g in u.groupby(['cohort_month','first_source']):
        mature=(pd.Period(cohort,'M')+1).start_time+pd.Timedelta(days=30)<=END
        cost=cm.get((source,cohort),np.nan)
        rev=g.revenue_30d.sum() if mature else np.nan
        buyers=int(g.purchased_30d.sum()) if mature else np.nan
        ltv.append({'cohort_month':cohort,'source_id':source,'users':len(g),'fully_mature_30d':mature,'buyers_30d':buyers,'cohort_month_costs':cost,'revenue_30d':rev,'ltv_30d_per_visitor':rev/len(g),'cac_visitor':cost/len(g),'roas_30d':rev/cost if pd.notna(cost) and cost>0 else np.nan})
    ltv=pd.DataFrame(ltv);save(ltv,'ltv_cac_30d_cohort_channel')
    save(u.reset_index(),'users_clean');save(ud,'user_activity_days');save(o,'orders_clean');save(c,'costs_clean')
    save(v,'visits_clean')
    checks.update({'daily_new_users_sum':int(daily.new_users.sum())==len(u),'dau_le_wau_le_mau':bool(((daily.dau<=daily.wau)&(daily.wau<=daily.mau)).all()),'channel_revenue_reconciles':bool(np.isclose(channel.revenue.sum(),o.revenue.sum())),'channel_cost_reconciles':bool(np.isclose(channel.costs.sum(),c.costs.sum())),'cohort_m0_is_one':bool((matrix.M0==1).all()),'retention_bounds':bool(all(ret[f'd{n}_retention'].dropna().between(0,1).all() for n in [1,7,30]))})
    assert all(checks.values()),checks
    audit['checks']={k:bool(val) for k,val in checks.items()}
    audit['source_csv_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.glob('*.csv')}
    (ROOT/'reports/data_quality.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=int),encoding='utf-8')
    metrics={'users':len(u),'visits':len(v),'orders':len(o),'buyers':int(u.converted.sum()),'conversion':float(u.converted.mean()),'revenue':round(float(o.revenue.sum()),2),'costs':round(float(c.costs.sum()),2),'roas':float(o.revenue.sum()/c.costs.sum()),'cac_visitor':float(c.costs.sum()/len(u)),'cac_buyer':float(c.costs.sum()/u.converted.sum()),'observed_ltv_per_visitor':float(o.revenue.sum()/len(u)),'observed_ltv_per_buyer':float(o.revenue.sum()/u.converted.sum()),'avg_dau':float(daily.dau.mean()),'avg_wau_full_window':float(daily.loc[daily.wau_full_window,'wau'].mean()),'avg_mau_full_window':float(daily.loc[daily.mau_full_window,'mau'].mean()),'mean_dau_mau_full_window':float(daily.dau_mau_full_window.mean()),'median_purchase_delay_hours':float(u.purchase_delay_hours.median())}
    for n in [1,7,30]:
        metrics[f'd{n}_eligible']=int(ret[f'd{n}_eligible'].sum());metrics[f'd{n}_returned']=int(ret[f'd{n}_returned'].sum());metrics[f'd{n}_retention']=float(ret[f'd{n}_returned'].sum()/ret[f'd{n}_eligible'].sum())
    (ROOT/'reports/metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf-8')
    svg_chart(daily,['new_users','new_users_7d_mean'],'每日新增访客与7日均线','01_daily_new_users')
    svg_chart(monthly,['new_users','calendar_mau'],'月新增访客与自然月活跃用户','02_monthly_growth')
    svg_chart(daily,['dau','wau','mau'],'日活与滚动7日、30日活跃用户（起始窗口不完整）','03_activity')
    svg_chart(daily,['dau_mau_full_window','wau_mau_full_window'],'完整30日窗口用户黏性','04_stickiness',True)
    retention_plot=retm[[f'd{n}_retention' for n in [1,7,30]]].copy()
    for n in [1,7,30]:retention_plot[f'd{n}_retention']=retention_plot[f'd{n}_retention'].where(retm[f'd{n}_eligible']==retm.cohort_users)
    retention_plot.columns=['D1','D7','D30']
    heatmap(retention_plot,'整月成熟首访用户：回访留存','05_retention')
    heatmap(matrix,'月度同期群访问留存（空白为未观察）','06_cohort')
    svg_chart(life,['new','continuing','dormant','returned'],'月末生命周期：滚动30日状态','07_lifecycle')
    conv_plot=conv.set_index('cohort_month').copy()
    full_month=[(pd.Period(x,'M')+1).start_time+pd.Timedelta(days=30)<=END for x in conv_plot.index]
    conv_plot.loc[~np.array(full_month),['conversion_1d','conversion_7d','conversion_30d']]=np.nan
    svg_chart(conv_plot,['conversion_1d','conversion_7d','conversion_30d'],'整月成熟首访用户：固定窗口购买转化','08_conversion',True)
    bar_chart(channel,['cac_visitor','cac_buyer'],'首次触点归因：渠道获客成本','09_channel_cac')
    bar_chart(channel,['roas'],'首次触点归因：观察期渠道ROAS','10_channel_roas')
    write_report(metrics,audit,monthly,channel,ltv,conv)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    return {'metrics':metrics,'daily':daily,'monthly':monthly,'retention':ret,'cohort':matrix,'lifecycle':life,'conversion':conv,'channel':channel,'ltv30':ltv,'audit':audit}

def write_report(m,a,monthly,channel,ltv,conv):
    lines=['# 用户增长分析报告（待本人核验）','',f'分析期：{START.date()} 至 {(END-pd.Timedelta(days=1)).date()}。来源：本机 MySQL 实际导入及关联，Python 计算。金额单位沿用数据原值，币种未经原始说明核实。', '',
      f'覆盖 {m["users"]:,} 名访客、{m["visits"]:,} 次访问、{m["orders"]:,} 条期内有效订单；购买用户 {m["buyers"]:,} 人，观察期转化率 {m["conversion"]:.2%}。',
      f'收入 {m["revenue"]:,.2f}，营销费用 {m["costs"]:,.2f}，收入/营销费（ROAS）{m["roas"]:.3f}。每访客获客成本 {m["cac_visitor"]:.2f}，每购买用户获客成本 {m["cac_buyer"]:.2f}。',
      f'日均 DAU {m["avg_dau"]:,.0f}；完整窗口平均 WAU {m["avg_wau_full_window"]:,.0f}、MAU {m["avg_mau_full_window"]:,.0f}；完整窗口日均 DAU/MAU {m["mean_dau_mau_full_window"]:.2%}。',
      f'严格第 N 个自然日回访留存：次日 {m["d1_retention"]:.2%}，第7日 {m["d7_retention"]:.2%}，第30日 {m["d30_retention"]:.2%}。不同天数分别采用已成熟的分母，不代表“7天内任意一天回访”。',
      f'已购买用户首访至首购时长中位数 {m["median_purchase_delay_hours"]:.2f} 小时；仅针对成功购买者，不能用于描述所有访客。','',
      '## 增长与渠道发现','',f'新增访客最高月份为 {monthly.new_users.idxmax()}，{monthly.new_users.max():,} 人。这是描述性结果，单年数据不能判断季节性或活动因果。', '',
      '|渠道|首访用户|首购用户|转化率|费用|首购CAC|ROAS|','|---|---:|---:|---:|---:|---:|---:|']
    for idx,r in channel.iterrows():
        fmt=lambda x: '缺少费用' if pd.isna(x) else f'{x:,.2f}'
        lines.append(f'|{idx}|{r.new_users:,.0f}|{r.buyers:,.0f}|{r.conversion:.2%}|{fmt(r.costs)}|{fmt(r.cac_buyer)}|{fmt(r.roas)}|')
    mature=ltv[ltv.fully_mature_30d].groupby('source_id').agg(revenue_30d=('revenue_30d','sum'),users=('users','sum'),costs=('cohort_month_costs',lambda x:x.sum(min_count=1)))
    mature['roas_30d']=mature.revenue_30d/mature.costs
    save(mature,'channel_30d_mature_cohorts',True)
    lines += ['', '固定30日观察窗口（整月成熟首访cohort汇总，2017-06 至 2018-04）：', '', '|渠道|成熟cohort用户数|30日每访客LTV|同cohort月费用|30日ROAS|', '|---|---:|---:|---:|---:|']
    for idx,r in mature.iterrows():
        fmt=lambda x:'缺少费用' if pd.isna(x) else f'{x:,.3f}'
        lines.append(f'|{idx}|{r.users:,.0f}|{r.revenue_30d/r.users:.3f}|{fmt(r.costs)}|{fmt(r.roas_30d)}|')
    r3=channel.loc[3]
    lines += ['',f'渠道3消耗 {r3.costs/m["costs"]:.1%} 的营销费用，贡献 {r3.revenue/m["revenue"]:.1%} 的归因收入，观察期ROAS仅 {r3.roas:.3f}。建议优先审查该渠道的人群与投放结构，并用小规模预算实验验证；这不是渠道投放造成亏损的因果证明。', f'新增用户从2017-11的 {monthly.loc["2017-11","new_users"]:,} 人降至2018-05的 {monthly.loc["2018-05","new_users"]:,} 人，变化 {monthly.loc["2018-05","new_users"]/monthly.loc["2017-11","new_users"]-1:.1%}；应联合费用和渠道构成排查，不能直接归因为留存下降。']
    lines += ['', '## 可验证的优化方向','',
      '渠道优先级需同时看固定30日ROAS、转化率与规模，先小额实验验证增量效果，不能仅凭累计收入决定预算。没有费用记录的渠道不能视为免费渠道。',
      '将首访未购买者与已购买者分别研究；可围绕首日购买路径提出实验，但本数据没有页面、加购、曝光信息，不能直接定位漏斗流失步骤。',
      '生命周期的沉默用户规模是历史用户存量；回流率和触达实验需结合可触达性、实验组与对照组，本数据不能证明营销带来回流。','',
      '## 数据质量与分析边界','',
      f'原始完全重复行：{a["duplicates"]}；访问结束早于开始：{a["invalid_duration_rows"]} 条，保留合法开始时间计算活跃，仅将时长置空。',
      f'窗口外订单 {a["orders_outside_window"]} 条，收入 {a["revenue_outside_window"]:.2f}；无访问匹配订单 {a["unmatched_orders"]} 条；早于首访订单 {a["orders_before_first_visit"]} 条，均记录并排除。',
      f'同一用户同时间多渠道组 {a["same_time_multichannel_user_timestamp_groups"]} 个，以渠道ID、设备、原始行号确定性排序；这不是可识别的真实先后关系。',
      '用户ID按字符串处理；订单无订单ID，原始行只作为记录标识。无重复行不代表不存在业务重复订单。',
      f'异常低流量日期（DAU<10）为 {a["low_traffic_days_below_10_dau"]}。其中2018-03-31仅1名访客，2018-04-01无访问记录，可能是采集缺口，也可能是实际业务异常，不能据此定论。主结果按已记录事件计算；retention_sensitivity.csv排除首访日或回访目标日落在异常日期的cohort，提供敏感性对照，不替代主口径。',
      '费用存在部分渠道日期缺行，详见data_quality.json；无法判断是零投放还是漏记，费用总额仅代表已记录金额。渠道成本效率需在补齐业务说明后再用于预算决策。',
      '首次访问仅指观察期内首次出现，存在左截断；数据未提供时区，保留源时间，不自行换算。首月新用户可能含历史老用户。',
      '渠道以观察期首次访问归因；跨渠道访问用户的收入只计入一个首访渠道。任意触点用户规模允许跨渠道重复，不能求和解释为总用户。',
      'LTV为已观察收入LTV，不是预测终身价值；固定30日cohort表只对整月均成熟的cohort展示30日收入。营销费按首访渠道和月份对齐，是描述性效率口径，不是用户级真实广告归因。',
      'ROAS=收入/营销费；marketing_surplus_rate=(收入-营销费)/营销费只代表营销费用差额率。缺少毛利、退款、履约等成本，不计算利润ROI。',
      '月末生命周期使用两个相邻30日窗口：新访客=当前窗口首访；持续活跃=两个窗口均访问且非新；回流=当前访问、前窗口未访问且首访更早；沉默=已知用户当前窗口无访问。四类互斥且覆盖已知用户。前窗口不足的月份有标记。',
      '完整流程及口径见 README.md、reports/metric_dictionary.md；质量断言和SQL/Python逐用户核对结果见 data_quality.json。Excel展示及完整Word项目报告已完成，详见项目README。']
    (ROOT/'reports/analysis_report.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
