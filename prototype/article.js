const article = JSON.parse(document.getElementById('article-data').textContent);
const palette = ['#335acb', '#007e70', '#a26508', '#9a4384', '#4e7483'];
const number = value => value === null ? '欠測' : value.toLocaleString('ja-JP', {maximumFractionDigits: 1});
const escapeHtml = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const sourceMap = new Map(article.sources.map(source => [source.id, source]));

function showSource(hash = location.hash) {
  const target = document.getElementById(hash.slice(1));
  if (target?.matches('details.article-source')) target.open = true;
}
window.addEventListener('hashchange', () => showSource());
document.querySelectorAll('a[href^="#source-"]').forEach(link => link.addEventListener('click', () => showSource(link.hash)));
showSource();

function save(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const link = document.createElement('a'); link.href = url; link.download = name;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

function mountChart(chart) {
  const root = document.getElementById(`chart-${chart.id}`);
  const controls = root.querySelector('.chart-controls');
  const state = {start: 0, end: chart.periods.length - 1, indexed: false, selected: new Set(chart.series.map(series => series.id))};
  const fieldset = document.createElement('fieldset');
  const legend = document.createElement('legend'); legend.textContent = '表示する指標'; fieldset.append(legend);
  chart.series.forEach((series, index) => {
    const label = document.createElement('label');
    const input = document.createElement('input'); input.type = 'checkbox'; input.checked = true;
    const marker = document.createElement('i'); marker.style.background = palette[index % palette.length];
    label.append(input, marker, document.createTextNode(series.label)); fieldset.append(label);
    input.addEventListener('change', () => {input.checked ? state.selected.add(series.id) : state.selected.delete(series.id); render();});
  });
  controls.append(fieldset);
  if (chart.type === 'line') {
    const periods = document.createElement('div'); periods.className = 'period-selects';
    const selects = {};
    for (const [key, labelText] of [['start', '開始期'], ['end', '終了期']]) {
      const label = document.createElement('label'); label.append(document.createTextNode(labelText));
      const select = document.createElement('select');
      chart.periods.forEach((period, index) => {const option = document.createElement('option'); option.value = index; option.textContent = period; select.append(option);});
      select.value = state[key]; label.append(select); periods.append(label); selects[key] = select;
      select.addEventListener('change', () => {
        state[key] = Number(select.value);
        if (state.start > state.end) {const other = key === 'start' ? 'end' : 'start'; state[other] = state[key]; selects[other].value = state[other];}
        render();
      });
    }
    const canIndex = chart.series.every(series => series.values.every(value => value === null || value > 0));
    if (canIndex) {
      const label = document.createElement('label'); label.append(document.createTextNode('表示方法'));
      const select = document.createElement('select');
      for (const [value, text] of [['original', '元の値'], ['index', '開始期を100にする']]) {
        const option = document.createElement('option'); option.value = value; option.textContent = text; select.append(option);
      }
      label.append(select); periods.append(label);
      select.addEventListener('change', () => {state.indexed = select.value === 'index'; render();});
    }
    controls.append(periods);
  }
  const actions = root.querySelector('.chart-actions');
  const csvButton = document.createElement('button'); csvButton.type = 'button'; csvButton.textContent = '表示中のCSVを保存';
  const recipeButton = document.createElement('button'); recipeButton.type = 'button'; recipeButton.textContent = '計算条件を保存';
  actions.prepend(csvButton, recipeButton);
  function model() {
    const series = chart.series.filter(series => state.selected.has(series.id));
    const periods = chart.periods.slice(state.start, state.end + 1);
    const rows = periods.map((period, offset) => ({period, original: series.map(series => series.values[state.start + offset]), values: series.map(series => {
      const value = series.values[state.start + offset], base = series.values[state.start];
      return state.indexed ? (value === null || base === null || base === 0 ? null : value / base * 100) : value;
    })}));
    return {series, periods, rows, unit: state.indexed ? `${periods[0]}=100` : chart.unit};
  }
  function render() {
    const data = model();
    const graph = root.querySelector('.graph');
    const values = data.rows.flatMap(row => row.values.filter(value => value !== null));
    csvButton.disabled = recipeButton.disabled = data.series.length === 0;
    root.querySelector('.chart-unit').textContent = `${chart.period_label} / ${data.unit} / ${data.periods[0]}${data.periods.length > 1 ? `〜${data.periods.at(-1)}` : ''}`;
    if (!values.length) {
      graph.innerHTML = '<p class="empty">表示する指標を選んでください。欠測の期間には値を補いません。</p>';
    } else if (chart.type === 'bar') {
      const min = Math.min(0, ...values), max = Math.max(chart.unit.includes('%') ? 100 : 1, ...values), span = max - min;
      const x = value => (value - min) / span * 100;
      graph.innerHTML = data.rows.map(row => `<div class="bar-group"><h4>${escapeHtml(row.period)}</h4>${data.series.map((series, i) => {
        const value = row.values[i], color = palette[chart.series.indexOf(series) % palette.length];
        return `<div class="bar-series"><div class="bar-label"><span>${escapeHtml(series.label)}</span><strong>${number(value)} ${escapeHtml(data.unit.includes('%') ? '%' : data.unit)}</strong></div><div class="bar-track"><i class="bar-zero" style="left:${x(0)}%"></i>${value === null ? '' : `<i class="bar-fill" style="left:${Math.min(x(0), x(value))}%;width:${Math.abs(x(value)-x(0))}%;background:${color}"></i>`}</div></div>`;
      }).join('')}</div>`).join('') + `<p class="bar-scale">軸の範囲：${number(min)}〜${number(max)} ${escapeHtml(data.unit)}。すべて同じ尺度。</p>`;
    } else {
      const width = Math.max(290, graph.clientWidth), height = 300;
      const p = {left: 53, right: 20, top: 20, bottom: 42};
      const low = Math.min(0, ...values), high = Math.max(0, ...values);
      const rawStep = (high - low || 1) / 4;
      const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
      const step = [1, 2, 2.5, 5, 10].find(value => value * magnitude >= rawStep) * magnitude;
      const min = Math.floor(low / step) * step, max = Math.ceil(high / step) * step || step;
      const x = i => data.periods.length === 1 ? (width + p.left - p.right) / 2 : p.left + i / (data.periods.length - 1) * (width-p.left-p.right);
      const y = value => height-p.bottom-(value-min)/(max-min)*(height-p.top-p.bottom);
      let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(chart.title)}。${escapeHtml(data.unit)}。数値は下の表で確認できます。">`;
      for (let value=min; value<=max+step/100; value+=step) {
        svg += `<line x1="${p.left}" x2="${width-p.right}" y1="${y(value)}" y2="${y(value)}" stroke="${value===0?'#8ca3b3':'#dde6eb'}"/><text x="${p.left-8}" y="${y(value)+5}" text-anchor="end" fill="#506879" font-size="12">${number(value)}</text>`;
      }
      const every = Math.max(1, Math.ceil((data.periods.length-1)/(width < 500 ? 4 : 8)));
      data.periods.forEach((period, i) => {if (i%every===0 || i===data.periods.length-1) svg += `<text x="${x(i)}" y="${height-12}" text-anchor="middle" fill="#506879" font-size="12">${escapeHtml(period)}</text>`;});
      data.series.forEach((series, index) => {
        const color = palette[chart.series.indexOf(series) % palette.length];
        let path='', connected=false;
        data.rows.forEach((row, i) => {const value=row.values[index]; if(value===null){connected=false;return;} path+=`${connected?'L':'M'}${x(i)} ${y(value)} `;connected=true;});
        const dashed = chart.series.indexOf(series) % 2 ? 'stroke-dasharray="6 3"' : '';
        svg += `<path d="${path}" fill="none" stroke="${color}" stroke-width="2.5" ${dashed}/>`;
        data.rows.forEach((row, i) => {const value=row.values[index];if(value!==null) svg += `<circle cx="${x(i)}" cy="${y(value)}" r="3" fill="white" stroke="${color}" stroke-width="2"><title>${escapeHtml(row.period)} ${escapeHtml(series.label)}：${number(value)}</title></circle>`;});
      });
      graph.innerHTML = svg + '</svg>';
    }
    root.querySelector('.graph-legend').innerHTML = data.series.map(series => `<span><i style="background:${palette[chart.series.indexOf(series)%palette.length]}"></i>${escapeHtml(series.label)}</span>`).join('');
    const table = root.querySelector('table');
    table.innerHTML = `<caption>${escapeHtml(data.unit)} / ${escapeHtml(chart.period_label)}</caption><thead><tr><th scope="col">${escapeHtml(chart.period_label)}</th>${data.series.map(series=>`<th scope="col">${escapeHtml(series.label)}</th>`).join('')}</tr></thead><tbody>${data.rows.map(row=>`<tr><th scope="row">${escapeHtml(row.period)}</th>${row.values.map(value=>`<td>${number(value)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  }
  csvButton.addEventListener('click', () => {
    const data=model(), rows=[['article','chart','period_type','period','series','label','value','unit','original_value','original_unit','transformation','source_urls','source_sha256','derivation']];
    data.rows.forEach(row=>data.series.forEach((series,i)=>{const refs=series.source_ids.map(id=>sourceMap.get(id));rows.push([article.id,chart.id,chart.period_type,row.period,series.id,series.label,row.values[i]??'',data.unit,row.original[i]??'',chart.unit,state.indexed?'value/base*100':'original',refs.map(s=>s.url).join(' | '),refs.map(s=>s.sha256||'').join(' | '),chart.derivation]);}));
    const quote=value=>'"'+String(value).replaceAll('"','""')+'"';
    save(`${article.id}-${chart.id}-view.csv`,'\ufeff'+rows.map(row=>row.map(quote).join(',')).join('\r\n'),'text/csv;charset=utf-8');
  });
  recipeButton.addEventListener('click', () => {
    const data=model(), ids=new Set(data.series.flatMap(series=>series.source_ids));
    save(`${article.id}-${chart.id}-recipe.json`,JSON.stringify({schema_version:1,article:article.id,chart:chart.id,period_type:chart.period_type,periods:data.periods,series_ids:data.series.map(s=>s.id),transformation:state.indexed?'value/base*100':'original',base_period:state.indexed?data.periods[0]:null,unit:data.unit,missing:'null; no interpolation',derivation:chart.derivation,source_versions:article.sources.filter(s=>ids.has(s.id)),chart_snapshot:chart},null,2),'application/json;charset=utf-8');
  });
  render();
  let renderedWidth = root.querySelector('.graph').clientWidth;
  new ResizeObserver(entries => {
    const width = entries[0].contentRect.width;
    if (Math.abs(width - renderedWidth) < 1) return;
    renderedWidth = width;
    render();
  }).observe(root.querySelector('.graph'));
}
article.charts.forEach(mountChart);
