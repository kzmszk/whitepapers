#!/usr/bin/env python3
"""Fetch official e-Stat energy balance workbooks and record reproducible provenance."""
import concurrent.futures, datetime, hashlib, html, json, pathlib, re, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw' / 'energy'
RAW.mkdir(parents=True, exist_ok=True)
LIST_URL = 'https://www.e-stat.go.jp/stat-search/files?cycle=7&layout=dataset&page={page}&result_page=1&tclass1=000001024837&tclass2val=0&toukei=00551010&toukei_kind=9&tstat=000001024835'
SOURCES = []
def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()
def source(id, title, url, path, fmt, edition, notes=''):
    return dict(id=id,title=title,publisher='資源エネルギー庁（e-Stat掲載）',edition=edition,url=url,download_url=url,local_path=str(path.relative_to(ROOT)),format=fmt,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),availability='downloaded',rights_url='https://www.e-stat.go.jp/terms-of-use',rights_notes='e-Stat利用規約および提供元の利用条件に従う。出典・加工の明示が必要。',whitepaper_ref='エネルギー動向2025年6月版 第1章 国内エネルギー動向。2026年4月14日改訂系列は白書掲載時点と異なる。',notes=notes)
items=[]
for page in range(1,4):
    url=LIST_URL.format(page=page)
    data=get(url)
    path=RAW / f'estat-balance-index-{page}.html'
    path.write_bytes(data)
    SOURCES.append(source(f'energy-estat-index-{page}',f'総合エネルギー統計 e-Stat一覧 {page}',url,path,'html','2026-04-14更新系列'))
    text=data.decode('utf-8')
    for article in re.findall(r'<article\b.*?</article>',text,flags=re.S):
        m=re.search(r'(\d{4})年度簡易表',article)
        d=re.search(r'href="([^"]*file-download[^"]+)"',article)
        if m and d:
            year=int(m[1]);url='https://www.e-stat.go.jp'+html.unescape(d[1]);items.append((year,url))
assert len(items)==35 and {y for y,u in items}==set(range(1990,2025)), len(items)
def download(item):
    year,url=item;path=RAW/f'energy-balance-{year}-simple.xlsx'
    if not path.exists():
        data=get(url)
        if data[:2]!=b'PK': raise ValueError(f'Not XLSX: {url}')
        path.write_bytes(data)
    return source(f'energy-balance-{year}',f'総合エネルギー統計 {year}年度 簡易表',url,path,'xlsx',f'{year}年度・2026-04-14改訂','年度は4月〜翌年3月。エネルギー単位表は高位発熱量・TJ。低位発熱量のIEA準拠自給率と異なる。')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    SOURCES.extend(executor.map(download,items))
p=RAW/'energy-balance-2024.xlsx'
if p.exists():SOURCES.append(source('energy-balance-2024-full','総合エネルギー統計 2024年度 本表','https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040445051&fileKind=0',p,'xlsx','2024年度・2026-04-14改訂'))
manifest=ROOT/'research'/'energy-sources.json'
prior=json.loads(manifest.read_text()) if manifest.exists() else []
owned={s['id'] for s in SOURCES}
SOURCES.extend(s for s in prior if s['id'] not in owned)
manifest.write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2)+'\n')
print(f'Downloaded {len(items)} annual workbooks, FY1990–FY2024; {sum(p.stat().st_size for p in RAW.glob("*.xlsx")):,} bytes XLSX')
