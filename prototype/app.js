let dataset;
const colors = {fuel_imports:'#335acb',cpi_energy:'#007e70',cpi_all:'#aa6705'};
const labels = {fuel_imports:'鉱物性燃料の輸入額',cpi_energy:'家庭のエネルギー価格',cpi_all:'物価全体'};
const byId = id => document.getElementById(id);
const selected = () => [...document.querySelectorAll('input[name="series"]:checked')].map(input => input.value);
const number = value => value === null ? '欠測' : value.toLocaleString('ja-JP',{minimumFractionDigits:1,maximumFractionDigits:1});

function revealWhitepaper(hash = location.hash) {
  const target = document.getElementById(hash.slice(1));
  if (target?.matches('details.whitepaper')) target.open = true;
}
window.addEventListener('hashchange', () => revealWhitepaper());
document.querySelectorAll('a[href^="#paper-"]').forEach(link => {
  link.addEventListener('click', () => revealWhitepaper(link.hash));
});
revealWhitepaper();

function model() {
  const start=Number(byId('start').value),end=Number(byId('end').value),mode=byId('mode').value;
  const series=selected().map(id=>dataset.series.find(s=>s.id===id));
  const rows=[];
  for(let year=start;year<=end;year++) {
    const values=series.map(s=>{
      const current=s.data.find(r=>r.year===year)?.value;
      const denominator=s.data.find(r=>r.year===(mode==='index'?start:year-1))?.value;
      return current===undefined || denominator===undefined || denominator===0 ? null : mode==='index'?100*current/denominator:100*(current/denominator-1);
    });
    rows.push({year,values});
  }
  return {start,end,mode,series,rows,unit:mode==='index'?`${start}年=100`:'前年比（%）'};
}

function render() {
  const m=model();
  byId('chart-title').textContent=m.series.length?m.series.map(s=>labels[s.id]).join('と、'):'データを選んで比べる';
  byId('chart-subtitle').textContent=`${m.start}〜${m.end}年 / 暦年 / ${m.unit}`;
  byId('download-csv').disabled=m.series.length===0;
  byId('download-recipe').disabled=m.series.length===0;
  byId('legend').replaceChildren();
  m.series.forEach(s=>{const span=document.createElement('span'),line=document.createElement('i');line.style.background=colors[s.id];span.append(line,document.createTextNode(labels[s.id]));byId('legend').append(span)});
  const values=m.rows.flatMap(r=>r.values.filter(v=>v!==null));
  if(!values.length) {
    byId('chart').innerHTML='<div class="empty">比べたいデータを、選択欄から選んでください。</div>';
    byId('insight').textContent='1つの系列を詳しく見たり、複数の系列を重ねたりできます。';
  } else {
    const w=Math.max(290,byId('chart').clientWidth),h=320,p={left:45,right:20,top:22,bottom:42};
    const min=m.mode==='index'?0:Math.floor(Math.min(...values,0)/10)*10;
    const max=Math.max(min+10,Math.ceil(Math.max(...values,0)/(m.mode==='index'?50:10))*(m.mode==='index'?50:10));
    const x=year=>m.end===m.start?(w+p.left-p.right)/2:p.left+(year-m.start)/(m.end-m.start)*(w-p.left-p.right);
    const y=value=>h-p.bottom-(value-min)/(max-min)*(h-p.top-p.bottom);
    let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="plot-title plot-desc"><title id="plot-title">${m.start}〜${m.end}年の比較</title><desc id="plot-desc">${m.series.map(s=>labels[s.id]).join('、')}。${m.unit}。数値は下の「グラフの数値を表で読む」から確認できます。</desc>`;
    for(let i=0;i<=5;i++){const v=min+(max-min)*i/5;svg+=`<line x1="${p.left}" x2="${w-p.right}" y1="${y(v)}" y2="${y(v)}" stroke="#dfe7ec"/><text x="${p.left-12}" y="${y(v)+5}" text-anchor="end" fill="#506879" font-size="14">${Math.round(v)}</text>`;}
    if(m.mode==='index'&&max>=100)svg+=`<line x1="${p.left}" x2="${w-p.right}" y1="${y(100)}" y2="${y(100)}" stroke="#8ea3b2" stroke-dasharray="4 5"/>`;
    for(const row of m.rows)svg+=`<text x="${x(row.year)}" y="${h-12}" text-anchor="middle" fill="#506879" font-size="14">${row.year}</text>`;
    m.series.forEach((s,i)=>{
      let path='',connected=false;
      for(const row of m.rows){const v=row.values[i];if(v===null){connected=false;continue}path+=`${connected?'L':'M'}${x(row.year)} ${y(v)} `;connected=true;}
      svg+=`<path d="${path}" fill="none" stroke="${colors[s.id]}" stroke-width="3" stroke-linejoin="round"${s.id==='cpi_all'?' stroke-dasharray="7 5"':''}/>`;
      for(const row of m.rows)if(row.values[i]!==null)svg+=`<circle cx="${x(row.year)}" cy="${y(row.values[i])}" r="4" fill="white" stroke="${colors[s.id]}" stroke-width="2"><title>${row.year}年 ${labels[s.id]}：${number(row.values[i])}</title></circle>`;
    });
    byId('chart').innerHTML=svg+'</svg>';
    const last=m.rows.at(-1);
    byId('insight').textContent=`${m.end}年は、${m.series.map((s,i)=>`${labels[s.id]}が${number(last.values[i])}${m.mode==='yoy'&&last.values[i]!==null?'%':''}`).join('、')}。${m.mode==='index'?`${m.start}年を100とした、それぞれの変化です。`:'それぞれの前年からの変化です。'}`;
  }
  renderTable(m);
}

function renderTable(m){
  const table=byId('data-table');table.replaceChildren();
  const caption=document.createElement('caption');caption.textContent=m.unit;table.append(caption);
  const head=document.createElement('thead'),tr=document.createElement('tr');
  ['暦年',...m.series.map(s=>labels[s.id])].forEach(text=>{const th=document.createElement('th');th.scope='col';th.textContent=text;tr.append(th)});head.append(tr);table.append(head);
  const body=document.createElement('tbody');
  m.rows.forEach(row=>{const tr=document.createElement('tr');[`${row.year}年`,...row.values.map(number)].forEach((text,i)=>{const td=document.createElement(i?'td':'th');if(!i)td.scope='row';td.textContent=text;tr.append(td)});body.append(tr)});table.append(body);
}

function saveFile(name,text,type){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function recipe(){const m=model();return {schema_version:1,created_from:'meti-whitepaper-comparison-prototype',dataset_snapshot:dataset.retrieved_at,period_type:'calendar_year',start:m.start,end:m.end,series_ids:m.series.map(s=>s.id),series_definitions:m.series.map(({id,source_id,item_code,source_column,unit,aggregation})=>({id,source_id,item_code,source_column,unit,aggregation})),transformation:m.mode,base_year:m.mode==='index'?m.start:null,formula:dataset.method[m.mode],missing:dataset.method.missing,source_versions:dataset.sources.filter(s=>m.series.some(v=>v.source_id===s.id)),cpi_annual_aggregation:'Arithmetic mean of all 12 monthly indices; 2020 base; unrounded before display',display_precision:1}}

async function init(){
  try {
    const response=await fetch('data.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);dataset=await response.json();
    for(const id of ['start','end'])for(let year=2020;year<=2025;year++){const option=document.createElement('option');option.value=year;option.textContent=`${year}年`;byId(id).append(option)}
    byId('start').value='2020';byId('end').value='2025';
    document.querySelectorAll('input[name="series"],#mode').forEach(el=>el.addEventListener('change',render));
    byId('start').addEventListener('change',()=>{if(Number(byId('start').value)>Number(byId('end').value))byId('end').value=byId('start').value;render()});
    byId('end').addEventListener('change',()=>{if(Number(byId('end').value)<Number(byId('start').value))byId('start').value=byId('end').value;render()});
    byId('reset').addEventListener('click',()=>{byId('start').value='2020';byId('end').value='2025';byId('mode').value='index';document.querySelectorAll('input[name="series"]').forEach(el=>el.checked=el.value!=='cpi_all');render()});
    byId('download-recipe').addEventListener('click',()=>saveFile('comparison-recipe.json',JSON.stringify(recipe(),null,2),'application/json;charset=utf-8'));
    byId('download-csv').addEventListener('click',()=>{
      const m=model(),rows=[['calendar_year','series_id','label','transformed_value','display_value','display_unit','original_value','original_unit','source_url','source_sha256','retrieved_at','transformation','base_year']];
      for(const row of m.rows)m.series.forEach((s,i)=>{const source=dataset.sources.find(v=>v.id===s.source_id);rows.push([row.year,s.id,labels[s.id],row.values[i]??'',row.values[i]===null?'':row.values[i].toFixed(1),m.unit,s.data.find(v=>v.year===row.year)?.value??'',s.unit,source.download_url||source.url,source.sha256,source.retrieved_at,m.mode,m.mode==='index'?m.start:''])});
      const escape=value=>'"'+String(value).replaceAll('"','""')+'"';saveFile('comparison.csv','\ufeff'+rows.map(row=>row.map(escape).join(',')).join('\r\n'),'text/csv;charset=utf-8');
    });
    const explanations={ 'stat-cpi-2020-monthly':'全国の「総合」「エネルギー」を使用。毎月の指数から、12か月そろった年の平均を独自に計算。家計の支出額そのものではありません。', 'trade-mof-products-import-annual':'「鉱物性燃料」の輸入金額（千円）を使用。輸入価格そのものではなく、輸入量や為替なども含んだ金額です。'};
    dataset.sources.filter(s=>s.id in explanations).forEach(source=>{const article=document.createElement('article');article.className='source-row';const main=document.createElement('div'),h=document.createElement('h3'),p=document.createElement('p');h.textContent=source.title;p.textContent=source.publisher;main.append(h,p);for(const [label,url] of [['公式の掲載ページ ↗',source.url],['原データを開く ↗',source.download_url]]){if(!url)continue;const a=document.createElement('a');a.textContent=label;a.href=url;main.append(a)}const detail=document.createElement('p');detail.textContent=explanations[source.id];article.append(main,detail);byId('source-list').append(article)});
    render();
    window.addEventListener('resize',render);
  } catch(error){byId('chart').innerHTML='<p class="error">データを読み込めませんでした。ローカルHTTPサーバーから開いてください。</p>';byId('chart-subtitle').textContent='データ未読込';byId('download-csv').disabled=true;byId('download-recipe').disabled=true;console.error(error)}
}
init();
