"""Build energy article charts and cross-check carbon balances against published totals."""
import csv, hashlib, json, math, re
from pathlib import Path
import openpyxl
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'content/energy.json').read_text())
years=list(range(2010,2025))
sources=json.loads((R/'research/energy-sources.json').read_text())
raw_sources={s['id']:s for s in sources}
a['sources']=[s for s in a['sources'] if not s['id'].startswith('energy-balance-')]
co2=[]; checks=[]
text=(R/'raw/energy/energy-supply-demand-2024-summary.txt').read_text()
publine=next(l for l in text.splitlines() if l.startswith('エネルギー起源CO2排出量    '))
pub=[float(v.replace(',','')) for v in re.findall(r'\d[\d,]*',publine.split('量')[1])][:16][1:]
assert len(pub)==15
for year,published in zip(years,pub):
 s=raw_sources[f'energy-balance-{year}']; path=R/s['local_path']
 digest=hashlib.sha256(path.read_bytes()).hexdigest(); assert digest==s['sha256']
 book=openpyxl.load_workbook(path,data_only=True,read_only=True)
 sheet=next(v for v in book if '炭素' in v.title); rows=list(sheet.values)
 cols={v:i for i,v in enumerate(rows[0])}; rowmap={v[0]:v for v in rows if isinstance(v[0],str)}
 assert str(rows[0][0]).strip()==f'{year}FY'
 assert rows[13][cols['$1401']]=='10^3 tC'
 total=(rowmap['#19'][cols['$1401']]-rowmap['#08'][cols['$1401']])*44/12/1000
 assert abs(total-published)<=0.5,(year,total,published)
 co2.append(total); checks.append({'fiscal_year':year,'computed_MtCO2':total,'published_rounded_MtCO2':published})
 book.close()
 a['sources'].append({'id':s['id'],'title':s['title'],'publisher':s['publisher'],'url':s['download_url'],'locator':'2026-04-14改訂。炭素単位表#19・#08の$1401、エネルギー単位表の最終消費','kind':'original_statistics','local_path':s['local_path'],'sha256':digest,'retrieved_at':s['retrieved_at']})
selfrows=list(csv.DictReader((R/'processed/energy-self-sufficiency-published.csv').open()))
selfvalues=[float(next(r['value'] for r in selfrows if int(r['year'])==year)) for year in years]
assert selfvalues[-1]==16.3
records=json.loads((R/'processed/energy-annual.json').read_text())
bykey={(r['series'],r['year']):r for r in records}
ids=[f'energy-balance-{year}' for year in years]
a['charts']=[
 {'id':'self-sufficiency','title':'エネルギー自給率は、どこまで戻った？','question':'国内で確保できるエネルギーの比率を、同じ定義で見る。','type':'line','unit':'%','period_type':'fiscal_year','period_label':'年度（4月〜翌3月）','periods':list(map(str,years)),'series':[{'id':'self-sufficiency-iea','label':'エネルギー自給率（IEAベース）','values':selfvalues,'source_ids':['energy-stat-summary']}],'notes':['2026年4月14日公表版の小数1桁の掲載値。PDF表から抽出したもので、原表からの自給率再計算ではない。','高位発熱量の国内産出÷一次供給とIEAベース自給率は定義が異なる。混ぜて比較しない。','IEAの定義では原子力を国内産出に含む。原子力燃料を国内で採掘しているという意味ではない。'],'derivation':'需給実績確報概要PDF7頁の「エネルギー自給率(IEAベース)」2010〜2024年度の掲載値を抽出。','takeaway':'2024年度は16.3%。調達の安定性を考える入口になるが、備蓄・輸入先・送電網などのリスクをこの値だけで評価できない。'},
 {'id':'emissions','title':'エネルギー起源のCO₂は、どう変わった？','question':'統計の炭素収支から排出量を再計算する。','type':'line','unit':'百万t-CO₂','period_type':'fiscal_year','period_label':'年度（4月〜翌3月）','periods':list(map(str,years)),'series':[{'id':'energy-co2','label':'エネルギー起源CO₂排出量','values':co2,'source_ids':ids}],'notes':['エネルギー起源CO₂。非エネルギー起源CO₂、他の温室効果ガス、森林等の吸収は含めない。','排出量の減少には活動量と燃料・電源構成の変化等が関わる。特定の政策の効果を示す比較ではない。','2023年度から標準発熱量・炭素排出係数の改訂がある。'],'derivation':'各年度の炭素単位表で、エネルギー利用の最終消費(#19/$1401)からエネルギー転換(#08/$1401、負値)を差し引き、千tC×44/12÷1000で百万t-CO₂に換算。15年度を概要PDF8頁の丸め値と±0.5以内で照合。','takeaway':f'2013年度から2024年度の減少は{(1-co2[-1]/co2[3])*100:.1f}%。2024年度は約{co2[-1]:.1f}百万t-CO₂。原表の丸め前の値から計算している。'},
 {'id':'consumption','title':'どこでエネルギーを使っている？','question':'企業・家庭・交通で、消費の動きは同じか。','type':'line','unit':'PJ','period_type':'fiscal_year','period_label':'年度（4月〜翌3月）','periods':list(map(str,years)),'series':[{'id':key,'label':label,'values':[bykey[(key,y)]['value'] for y in years],'source_ids':ids} for key,label in [('final_consumption_industry_business','企業・事業所他'),('final_consumption_households','家庭'),('final_consumption_transport','運輸')]],'notes':['PJはエネルギー量の単位。最終消費であり発電量ではない。非エネルギー利用を含む。','消費減には省エネ以外に天候・生産活動・人口・移動なども影響する。'],'derivation':'各年度エネルギー単位表の#20企業・事業所他、#33家庭、#34運輸の$1400（TJ）を1000で割りPJへ。3部門合計と#19最終消費の一致を各年で検査。','takeaway':'2024年度の最終消費は、企業・事業所他6,844.4 PJ、家庭1,697.2 PJ、運輸2,738.9 PJ。人数や生産量が違うので、部門間の効率の順位を示す数字ではない。'}]
for y in years:
 parts=sum(bykey[(key,y)]['value'] for key in ['final_consumption_industry_business','final_consumption_households','final_consumption_transport'])
 assert math.isclose(parts,bykey[('final_consumption_total',y)]['value'],rel_tol=1e-8)
(R/'content/energy.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'processed/energy-article-checks.json').write_text(json.dumps({'carbon_balance_checks':checks,'self_sufficiency_2024':selfvalues[-1],'co2_formula':'(#19/$1401 - #08/$1401) * 44/12 / 1000','sector_sums_checked':len(years)},ensure_ascii=False,indent=2)+'\n')
print('Energy: 3 charts; 15 carbon totals match published rounded values; 15 sector sums checked.')
