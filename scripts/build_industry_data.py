"""Build manufacturing charts directly from the archived annual IIP workbook."""
import json,hashlib,math
from pathlib import Path
import openpyxl
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'content/industry.json').read_text())
source=next(s for s in a['sources'] if s['id']=='industry-iip'); path=R/source['local_path']
assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
w=openpyxl.load_workbook(path,read_only=True,data_only=True)
def extract(sheet_name,codes):
 rows=list(w[sheet_name].values); assert '2020＝100.0' in rows[0][0]
 cols=[(i,str(p)[:4]) for i,p in enumerate(rows[2]) if isinstance(p,str) and p.endswith('CY')]
 assert [p for i,p in cols]==list(map(str,range(2018,2026)))
 series=[]
 for code,label in codes:
  row=next(row for row in rows[3:] if row[0]==code)
  values=[row[i] for i,p in cols]; assert all(isinstance(v,(int,float)) and math.isfinite(v) for v in values)
  assert values[2]==100
  series.append({'id':f'{sheet_name}-{code}','label':label,'values':values,'source_ids':['industry-iip']})
 return series
production=extract('生産計',[(1100000000,'製造工業・生産')]);shipments=extract('出荷計',[(1100000000,'製造工業・出荷')])
industries=extract('生産計',[(1103000000,'生産用機械工業'),(1105000000,'電子部品・デバイス工業'),(1107000000,'輸送機械工業'),(1114000000,'食料品・たばこ工業')])
base={'type':'line','unit':'2020年=100','period_type':'calendar_year','period_label':'暦年（1〜12月）','periods':list(map(str,range(2018,2026)))}
notes=['原指数の暦年値。年度値・季節調整済指数と区別。白書刊行後の2026年9月14日公表版。','数量の動きを表す指数で、名目売上・利益・生産性を表す数字ではない。','2020年は感染症の影響を受けた年。基準年を変えると見え方が変わるので、前後の年も確認する。']
a['charts']=[dict(base,id='production-shipments',title='作る量と出荷する量は、どう変わった？',question='製造工業全体の数量の変化を確認する。',series=production+shipments,notes=notes,derivation='生産計・出荷計シート、業種コード1100000000（製造工業）、2018CY〜2025CYを抽出。単位変換なし。',takeaway=f"製造工業の2025年生産指数は{production[0]['values'][-1]:.1f}。2020年を100とした数量の動きであり、業績や賃金の変化は別の統計で確認する。"),dict(base,id='industry-comparison',title='同じ製造業でも、動きは違う？',question='業種を選んで、回復や変化の違いを比べる。',series=industries,notes=notes+['各業種を同じ基準で指数化した比較。指数の単純平均や合計で製造業全体にはならない。'],derivation='生産計シートの1103000000、1105000000、1107000000、1114000000の2018CY〜2025CYを抽出。',takeaway='2025年は生産用機械118.3、電子部品・デバイス106.4、輸送機械107.2、食料品・たばこ97.1。業種ごとの需要や供給条件を調べる入口になる。')]
w.close()
(R/'content/industry.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
print('Industry: 2 charts; 6 series × 8 years; source SHA and 2020=100 verified.')
