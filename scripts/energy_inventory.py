#!/usr/bin/env python3
"""Complete the energy source inventory with acquired PDF, rendered pages, derivatives, and gaps."""
import datetime,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=ROOT/'research'/'energy-sources.json';sources=json.loads(p.read_text());items={s['id']:s for s in sources if not s['id'].startswith('energy-processed-')}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
rights='https://www.enecho.meti.go.jp/about/linksto_thissite/'
pdfurl='https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040391289&fileKind=2'
def add(id,title,url,path=None,fmt='html',edition='2025',availability='discovered_not_downloaded',notes='',ref='',rights_notes='資源エネルギー庁サイト利用規約は特記がなければPDL1.0。第三者の権利・独自利用条件を別途確認。',download_url=None):
    items[id]=dict(id=id,title=title,publisher='経済産業省・資源エネルギー庁',edition=edition,url=url,download_url=download_url if download_url is not None else url,local_path=path,format=fmt,retrieved_at=now,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest() if path else None,availability=availability,rights_url=rights,rights_notes=rights_notes,whitepaper_ref=ref,notes=notes)
add('energy-supply-demand-2024-summary','2024年度エネルギー需給実績（確報）概要',pdfurl,'raw/energy/energy-supply-demand-2024-summary.pdf','pdf','2024年度・2026-04-14公表','downloaded','e-Stat公式配布経由で取得。11ページ。白書2025後の統計改訂版。',ref='エネルギー動向2025年6月版第1章の更新検証に使う原統計')
for file,title,page in [('official-final-consumption-p02.png','最終エネルギー消費（公式PDF2頁）',2),('official-primary-supply-06.png','一次エネルギー国内供給（公式PDF6頁）',6),('official-primary-supply-07.png','効率・自給率・化石依存度（公式PDF7頁）',7)]:
    add('energy-graphic-page-'+str(page),title,pdfurl,'assets/energy/'+file,'png','2024年度・2026-04-14公表','derived_from_downloaded_pdf',f'原PDFの{page}頁全体をpdftoppmでPNG化（長辺1800px）。図表と注記を保持。出典:資源エネルギー庁「2024年度エネルギー需給実績（確報）概要」。Webへの掲載時は画像化したことを明示し、可能ならCSVから再描画する。',ref=f'原PDF {page}頁')
add('energy-supply-summary-text','公式PDFテキスト抽出',pdfurl,'raw/energy/energy-supply-demand-2024-summary.txt','txt','2024年度・2026-04-14公表','derived_from_downloaded_pdf','pdftotext -layout。OCRではない。画像の代替ではなく抽出確認用。')
add('energy-estat-summary-index','総合エネルギー統計 結果概要一覧','https://www.e-stat.go.jp/stat-search/files?cycle=7&layout=dataset&page=1&tclass1=000001024836&tclass2val=0&toukei=00551010&tstat=000001024835','raw/energy/estat-summary-index.html','html','2026-04-14公表','downloaded')
for file,title,fmt,note in [('energy-annual.csv','エネルギー年度統計 正規化データ','csv','35年度×20系列=700行。原ファイル、シート、セル、単位変換を各行に保持。'),('energy-annual.json','エネルギー年度統計 正規化JSON','json','CSVと同じ700行。'),('energy-self-sufficiency-published.csv','IEAベース自給率 公表値抽出','csv','2010〜2024年度15行。PDF7頁の公表丸め値から抽出。元Excelからの自給率再計算は未実施。'),('energy-validation.json','正規化検証結果と定義上の注意','json','表内年度、行コード、単位、構成要素の和を検証。')]:
    add('energy-processed-'+file.replace('.', '-'),title,pdfurl if 'self-sufficiency' in file else 'https://www.enecho.meti.go.jp/statistics/total_energy/results.html','processed/'+file,fmt,'2024年度・2026-04-14改訂','derived_from_downloaded_source',note)
for id,title,url,fmt,availability,note in [
 ('energy-whitepaper-index','エネルギー白書一覧','https://www.enecho.meti.go.jp/about/whitepaper/','html','search_index_read_http_403','2026-09-22調査で検索取得できた公式一覧は2025版を先頭掲載。2026版の刊行は確認できず。公式サイトへの直接HTTP取得は403で最新性に制限あり。'),
 ('energy-whitepaper-2025-full','エネルギー白書2025 全体版','https://www.enecho.meti.go.jp/about/whitepaper/2025/pdf/whitepaper2025_all.pdf','pdf','unavailable_http_403','公式掲載確認済。公開ファイルHTTP取得は403。ローカルPDF原本未取得。'),
 ('energy-whitepaper-2025-summary','エネルギー白書2025 概要','https://www.enecho.meti.go.jp/about/whitepaper/2025/pdf/whitepaper2025.pdf','pdf','discovered_not_downloaded','公式概要PDFの掲載・検索本文を確認。ローカル原本未取得。METI側同概要配布URLはHTTP403。'),
 ('energy-whitepaper-2025-gxchapter','エネルギー白書2025 第1部第2章','https://www.enecho.meti.go.jp/about/whitepaper/2025/pdf/1_2.pdf','pdf','search_index_read_not_downloaded','GX、産業政策、技術開発の章。原本未取得。'),
 ('energy-trends-202506','エネルギー動向2025年6月版 全体版','https://www.enecho.meti.go.jp/about/energytrends/202506/pdf/energytrends_all.pdf','pdf','discovered_not_downloaded','2025年から白書とは別掲載となった統計中心資料。原本未取得。'),
 ('energy-trends-demand','エネルギー動向 第1章第1節 エネルギー需給の概要','https://www.enecho.meti.go.jp/about/energytrends/202506/html/s-1-1.html','html','search_index_read_http_403','図11-1-1ほか図表Excelリンクを公式検索本文で確認。個別Excelの取得未了。図11-4-1の1989年度以前はIEA由来、1990年度以降は総合エネルギー統計。'),
 ('energy-total-series','総合エネルギー統計 時系列表・低位発熱量版IEA準拠表','https://www.enecho.meti.go.jp/statistics/total_energy/results.html','html','search_index_read_http_403','2026-04-14公表の時系列表211KBと低位発熱量版IEA準拠表362KBの存在を確認。直接配布ファイル未取得。今回保存はe-Stat年次表。'),
 ('energy-policy-s3e','白書2025 第2部はじめに 日本のエネルギー政策','https://www.enecho.meti.go.jp/about/whitepaper/2025/html/2-0-0.html','html','search_index_read_not_downloaded','S+3E、省エネ、再エネ・原子力、エネルギー安定供給と成長と脱炭素。'),
 ('energy-policy-fukushima','白書2025 第1部第1章 福島復興の進捗','https://www.enecho.meti.go.jp/about/whitepaper/2025/html/1-1-0.html','html','search_index_read_not_downloaded','福島復興、廃炉・被災者支援・新エネ社会構想。'),
 ('energy-policy-innovation','白書2025 第1部第2章第3節 次世代エネルギー革新技術','https://www.enecho.meti.go.jp/about/whitepaper/2025/html/1-2-3.html','html','search_index_read_not_downloaded','光電融合、ペロブスカイト、浮体式洋上風力、次世代地熱、次世代革新炉、水素等。'),
 ('energy-rights','資源エネルギー庁 サイト利用規約',rights,'html','search_index_read_not_downloaded','PDL1.0と第三者権利に関する規約を確認。'),
 ('energy-rights-thirdparty','資源エネルギー庁 法的事項','https://www.enecho.meti.go.jp/about/linksto_thissite/001/','html','search_index_read_not_downloaded','IEAや企業の出典がある図表・写真に政府共通ライセンスを一律適用しない。'),
]:add(id,title,url,fmt=fmt,availability=availability,notes=note)
for year in (1994,1995):
    items[f'energy-balance-{year}']['notes']=items[f'energy-balance-{year}']['notes'].split(' e-Stat')[0]+' e-Statの一覧名は簡易表だが実ファイルは詳細表（表内確認済）。名称不整合を保持し、正規化は明示的な行・列コードで処理。'
p.write_text(json.dumps(list(items.values()),ensure_ascii=False,indent=2)+'\n')
for item in items.values():
    if item['local_path']:
        assert hashlib.sha256((ROOT/item['local_path']).read_bytes()).hexdigest()==item['sha256']
print(f'Inventory: {len(items)} sources; {sum(bool(s["local_path"]) for s in items.values())} local files hashed')
