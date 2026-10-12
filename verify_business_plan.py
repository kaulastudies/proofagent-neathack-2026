"""Recompute cfo.ai export assumptions; verifies arithmetic, never actual traction."""
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SCHEDULES = {
 'Conservative': [[10,15,20,20,25,30],[0,1,2,3,4,5],[0,0,0,0,1,1]],
 'Base': [[20,30,40,50,60,70],[0,3,6,12,18,24],[0,0,1,2,3,4]],
 'Growth': [[40,60,80,100,120,150],[0,6,12,24,36,48],[0,0,2,5,8,12]],
}
# Published exact or displayed-rounded figures, transcribed from the original PDF.
EXPECTED = {
 'Conservative': ('704','960.32','-256.32','1433','3003',26),
 'Base': ('3230','2046','1184','6779','1695.28',29),
 'Growth': ('7325','3813','3512','14961','1462.96',33),
}
BASE_NET = ['-617.60','-590.64','-423.24','-63.80','472.24','1184.00']

def calculate():
    report = {'basis':'Hypothetical cfo.ai assumptions; not supplier quotes or business actuals',
              'rounding':'round-half-up churn to whole accounts', 'scenarios':{}}
    for name, additions in SCHEDULES.items():
        active=[0,0,0]; cumulative=Decimal(0); peak=Decimal(0); revenue_sum=Decimal(0); months=[]
        for month in range(6):
            active=[n-int((Decimal(n)*rate).quantize(Decimal(1), rounding=ROUND_HALF_UP))+additions[i][month]
                    for i,(n,rate) in enumerate(zip(active,[Decimal('.1'),Decimal('.05'),Decimal('.05')]))]
            free,individual,team=active
            evaluations=free*10+individual*100+team*500
            revenue=Decimal(29*individual+149*team)
            delivery=Decimal(170)+Decimal('.068')*evaluations+Decimal('.2')*free+5*individual+20*team
            recurring=delivery+430; net=revenue-recurring
            cumulative+=net; peak=max(peak,-cumulative); revenue_sum+=revenue
            months.append({'month':month+1,'accounts':active.copy(),'revenue':str(revenue),
                'delivery_cost':str(delivery),'recurring_cost':str(recurring),'net_movement':str(net),
                'burn':str(max(Decimal(0),-net)),'cumulative_movement':str(cumulative)})
        mix=(Decimal('17.20')*individual+95*team)/Decimal(individual+team)
        breakeven=math.ceil((Decimal(600)+Decimal('.88')*free)/mix)
        observed=(revenue,recurring,net,revenue_sum,peak,breakeven)
        expected=tuple(Decimal(v) for v in EXPECTED[name][:-1])+(EXPECTED[name][-1],)
        if observed != expected:
            raise ValueError('PDF summary does not reconcile: '+name)
        if name=='Base' and [Decimal(m['net_movement']) for m in months]!=list(map(Decimal,BASE_NET)):
            raise ValueError('PDF base monthly movements do not reconcile')
        report['scenarios'][name]={'months':months,'six_month_revenue':str(revenue_sum),
            'peak_funding_deficit':str(peak),'month6_break_even_accounts':breakeven,
            'month6_gross_margin_percent':str((revenue-delivery)/revenue*100),
            'summary_matches_pdf':True}
    report['opening_cash']=None;report['runway']=None
    return report

if __name__=='__main__':
    target=Path('artifacts/cfo/arithmetic-verification.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(calculate(),indent=2)+'\n')
    print('All three scenario summaries and base monthly cash movements match the cfo.ai PDF.')
    print('Saved:',target)
