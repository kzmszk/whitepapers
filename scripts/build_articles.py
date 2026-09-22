"""Validate editorial data and generate static, readable article pages and exports."""
import csv,hashlib,html,json,math,re
from pathlib import Path
from urllib.parse import urlparse
R=Path(__file__).resolve().parents[1]; OUT=R/'prototype'; (OUT/'themes').mkdir(exist_ok=True);(OUT/'data').mkdir(exist_ok=True)
ORDER=['energy','wages','industry','trade','small-business']
NAMES={'energy':'エネルギー','wages':'賃上げ','industry':'ものづくり','trade':'供給網','small-business':'地域の事業'}
esc=lambda x:html.escape(str(x),quote=True)
def load(name):
 a=json.loads((R/'content'/f'{name}.json').read_text()); assert a['id']==name
 sources={s['id']:s for s in a['sources']}; assert len(sources)==len(a['sources'])
 for s in sources.values():
  assert urlparse(s['url']).scheme=='https'
  if s.get('local_path'):
   path=R/s['local_path']; assert path.is_file(),path
   assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256'],path
 for section in a['sections']:
  assert section['kind'] in ['policy','editorial']
  assert section['source_ids'] and set(section['source_ids'])<=sources.keys()
 chartids=[]
 for c in a['charts']:
  assert c['type'] in ['line','bar'] and c['period_type'] in ['calendar_year','fiscal_year','survey_year','category']
  assert re.fullmatch(r'[a-z0-9-]+',c['id']),c['id'];chartids.append(c['id'])
  assert c['periods'] and len(c['periods'])==len(set(c['periods']))
  for s in c['series']:
   assert len(s['values'])==len(c['periods'])
   assert all(v is None or (type(v) in [int,float] and math.isfinite(v)) for v in s['values'])
   assert s['source_ids'] and set(s['source_ids'])<=sources.keys()
  assert len({s['id'] for s in c['series']})==len(c['series'])
 assert len(chartids)==len(set(chartids))
 return a

def links(ids,sources):
 return ' '.join(f'<a href="#source-{esc(id)}">{esc(sources[id]["title"])} ↓</a>' for id in dict.fromkeys(ids))

def chart_html(article_id,c,sources):
 heads=''.join(f'<th scope="col">{esc(s["label"])}</th>' for s in c['series'])
 rows=''.join('<tr><th scope="row">'+esc(p)+'</th>'+''.join('<td>'+('欠測' if s['values'][i] is None else esc(f'{s["values"][i]:,.1f}'))+'</td>' for s in c['series'])+'</tr>' for i,p in enumerate(c['periods']))
 refs=list(dict.fromkeys(id for s in c['series'] for id in s['source_ids']))
 return f'''<section class="article-chart" id="chart-{esc(c['id'])}" data-chart="{esc(c['id'])}">
 <div class="chart-intro"><span class="label observation">公式統計から再集計</span><h3>{esc(c['title'])}</h3><p>{esc(c['question'])}</p></div>
 <div class="chart-controls"></div><div class="graph" aria-live="polite"><noscript>数値は下の表から確認できます。</noscript></div><div class="graph-legend"></div><p class="chart-unit">{esc(c['period_label'])} / {esc(c['unit'])}</p>
 <p class="chart-takeaway"><strong>収録データ全体から分かること：</strong> {esc(c['takeaway'])}</p><ul class="chart-notes">{''.join('<li>'+esc(t)+'</li>' for t in c['notes'])}</ul>
 <div class="chart-actions"><a href="../data/{esc(article_id)}-{esc(c['id'])}.csv" download>全データのCSV</a></div>
 <details class="chart-table"><summary>グラフの数値を表で読む</summary><div class="table-scroll"><table><caption>{esc(c['unit'])} / {esc(c['period_label'])}</caption><thead><tr><th scope="col">{esc(c['period_label'])}</th>{heads}</tr></thead><tbody>{rows}</tbody></table></div></details>
 <details class="chart-method"><summary>出典と計算方法</summary><p>{esc(c['derivation'])}</p><div class="chart-source-links">{links(refs,sources)}</div></details></section>'''

reports=[]
catalog=[]
for current_id in ORDER:
 a=load(current_id);sources={s['id']:s for s in a['sources']}
 catalog.extend({'article_id':current_id,**source} for source in a['sources'])
 payload=json.dumps(a,ensure_ascii=False,indent=2)+'\n';(OUT/'data'/f'{current_id}.json').write_text(payload)
 for c in a['charts']:
  with (OUT/'data'/f"{current_id}-{c['id']}.csv").open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(['article','chart','period_type','period','series_id','label','value','unit','source_urls','source_sha256','derivation'])
   for i,p in enumerate(c['periods']):
    for s in c['series']:
     refs=[sources[id] for id in s['source_ids']]
     w.writerow([current_id,c['id'],c['period_type'],p,s['id'],s['label'],s['values'][i],c['unit'],' | '.join(x['url'] for x in refs),' | '.join(x.get('sha256') or '' for x in refs),c['derivation']])
 nav=''.join(f'<a href="{id}.html"'+(' aria-current="page"' if id==current_id else '')+f'>{NAMES[id]}</a>' for id in ORDER)
 toc=''.join(f'<a href="#section-{i}">{i}. {esc(s["heading"])}</a>' for i,s in enumerate(a['sections'],1))
 sections=[]
 for i,s in enumerate(a['sections'],1):
  kind='白書の説明を要約' if s['kind']=='policy' else 'このサイトの整理'
  sections.append(f'<section class="prose-section" id="section-{i}"><span class="label {s["kind"]}">{kind}</span><h2><span class="chapter-number">{i:02}</span>{esc(s["heading"])}</h2>'+''.join('<p>'+esc(t)+'</p>' for t in s['paragraphs'])+'<div class="section-citations">根拠：'+links(s['source_ids'],sources)+'</div></section>')
 sourcehtml=[]
 for s in sources.values():
  status='原本を保存・ハッシュ照合済み' if s.get('local_path') else '原本のローカル保存なし。確認範囲は上記の参照箇所に記載'
  kind={'whitepaper':'白書本文','official_summary':'公式概要','official_explanation':'担当官の解説','original_statistics':'原統計'}[s['kind']]
  sourcehtml.append(f'<details class="article-source" id="source-{esc(s["id"])}"><summary>{esc(s["title"])}</summary><p>{esc(s["publisher"])} / {kind}</p><p>{esc(s["locator"])}</p><p>{status}。確認・取得日：{esc(s["retrieved_at"])}</p><a href="{esc(s["url"])}">公式の原文・原データを開く ↗</a>'+ (f'<p class="hash">SHA-256: {esc(s["sha256"])}</p>' if s.get('sha256') else '')+'</details>')
 allcharts=''.join(chart_html(current_id,c,sources) for c in a['charts'])
 flow=''.join(f'<div><small>{esc(f["title"])}</small><strong>{esc(f["text"])}</strong></div>' for f in a['flow'])
 outcomes=''.join(f'<article><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p></article>' for x in a['outcomes'])
 questions=''.join('<li>'+esc(q)+'</li>' for q in a['questions'])
 energyextra='<p class="related-lab"><a href="../#lab">燃料輸入額と家庭の価格を重ねて比較する ↗</a></p>' if current_id=='energy' else ''
 doc=f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(a['title'])}｜経済の見取り図</title><meta name="description" content="{esc(a['subtitle'])}"><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="../article.css"><script src="../article.js" defer></script></head>
<body class="article-page"><a class="skip" href="#article-body">本文へ移動</a><header class="site-header"><a class="brand" href="../">▥ <span>経済の見取り図</span></a><nav aria-label="メイン"><a href="../#overview">白書の考え方</a><a href="#charts">データで確かめる</a><a href="#article-sources">出典</a></nav><span class="badge">非公式</span></header><nav class="theme-nav" aria-label="テーマ">{nav}</nav>
<main><header class="article-hero"><p class="eyebrow">白書から暮らしへ / {esc(a['whitepaper_label'])}</p><h1>{esc(a['title'])}</h1><p class="article-subtitle">{esc(a['subtitle'])}</p><p class="article-lead">{esc(a['lead'])}</p><p class="edition-note">{esc(a['edition_note'])}</p></header>
<section class="article-map"><span class="label editorial">このサイトの整理 / 政策の筋道</span><div class="policy-flow">{flow}</div><p>対応が目指す方向を図にしたものです。達成済みの成果や因果効果を示すものではありません。</p></section>
<div class="article-layout"><aside class="article-toc"><strong>この記事を読む</strong>{toc}<a href="#charts">数字で確かめる</a><a href="#outcomes">成果をどう見る？</a><a href="#article-sources">原文・元データ</a></aside><div id="article-body">{''.join(sections)}</div></div>
<section id="charts" class="article-data-section"><p class="eyebrow">自分の目で確かめる</p><h2>指標を選び、動きを比べる。</h2><p>公式の公開統計を使った比較です。系列や期間を変え、表・CSV・計算条件を持ち帰れます。</p>{allcharts}{energyextra}</section>
<section id="outcomes" class="article-outcomes"><p class="eyebrow">成果をどう見る？</p><h2>一つの数字で、結論を急がない。</h2><div class="outcome-grid">{outcomes}</div><h3>さらに調べる問い</h3><ul>{questions}</ul></section>
<section id="article-sources" class="article-sources"><h2>原文と元データに戻る。</h2><p>白書の説明、統計の観察、このサイトの整理を区別しています。図の原数値・出典・計算式は<a href="../data/{current_id}.json" download>記事データJSON</a>にも保存しています。</p>{''.join(sourcehtml)}</section>
<nav class="theme-nav" aria-label="他のテーマを読む">{nav}</nav></main><footer><strong>経済の見取り図</strong><p>関係省庁が運営・監修する公式サイトではありません。<br>公式資料を読み解き、公開統計を再集計して作成しています。</p></footer><script type="application/json" id="article-data">{json.dumps(a,ensure_ascii=False).replace('<',chr(92)+'u003c')}</script></body></html>'''
 (OUT/'themes'/f'{current_id}.html').write_text(doc)
 reports.append({'id':current_id,'sections':len(a['sections']),'charts':len(a['charts']),'sources':len(a['sources']),'observations':sum(len(c['periods'])*len(c['series']) for c in a['charts'])})
(R/'verification/article-build.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
(R/'research/article-source-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
with (R/'research/article-source-catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(catalog[0]));w.writeheader();w.writerows(catalog)
print(json.dumps(reports,ensure_ascii=False))
