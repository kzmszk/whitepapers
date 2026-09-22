"""Check generated pages and CSVs as a static-site consumer, without network access."""
import csv
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'prototype'
NAMES = ['energy', 'wages', 'industry', 'trade', 'small-business']


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = []
        self.table_cells = 0
        self.feed(path.read_text())

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, attrs['id']
            self.ids.add(attrs['id'])
        if tag in ['a', 'link', 'script']:
            url = attrs.get('href') or attrs.get('src')
            if url:
                self.links.append(url)
        if tag == 'td':
            self.table_cells += 1


pages = {path.resolve(): Page(path) for path in SITE.rglob('*.html')}
link_count = 0
for path, page in pages.items():
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        if target.is_dir():
            target /= 'index.html'
        assert target.is_relative_to(SITE), (path, link)
        assert target.is_file(), (path, link)
        if url.fragment:
            assert unquote(url.fragment) in pages[target].ids, (path, link)
        link_count += 1

observations = 0
for name in NAMES:
    article = json.loads((ROOT / 'content' / f'{name}.json').read_text())
    exported = json.loads((SITE / 'data' / f'{name}.json').read_text())
    assert exported == article
    count = 0
    for chart in article['charts']:
        with (SITE / 'data' / f"{name}-{chart['id']}.csv").open(encoding='utf-8-sig') as file:
            rows = list(csv.DictReader(file))
        expected = [(p, s, s['values'][i]) for i, p in enumerate(chart['periods']) for s in chart['series']]
        assert len(rows) == len(expected)
        for row, (period, series, value) in zip(rows, expected):
            assert row['period'] == period and row['series_id'] == series['id']
            assert row['period_type'] == chart['period_type'] and row['unit'] == chart['unit']
            assert (None if row['value'] == '' else float(row['value'])) == value
            assert row['source_urls'].startswith('https://') and row['source_sha256']
        count += len(rows)
    assert pages[(SITE / 'themes' / f'{name}.html').resolve()].table_cells == count
    observations += count

config = json.loads((ROOT / 'wrangler.jsonc').read_text())
assert config['assets']['directory'] == './prototype'
assert not any(key in config for key in ['durable_objects', 'd1_databases', 'r2_buckets'])
report = {'articles': len(NAMES), 'html_pages': len(pages), 'local_links_checked': link_count,
          'exported_observations_matched': observations, 'static_html_table_observations': observations,
          'cloudflare_bindings': []}
(ROOT / 'verification/article-static-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report))
