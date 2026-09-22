#!/usr/bin/env python3
"""Rebuild trade article charts from saved official customs aggregate tables."""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = [
    ("crude_oil", "原油及び粗油", "30301", 34, "KL"),
    ("lng", "液化天然ガス（LNG）", "3050103", 40, "MT"),
    ("lpg", "液化石油ガス（LPG）", "3050101", 42, "MT"),
]


def read_csv(path):
    return list(csv.reader((ROOT / path).read_text(encoding="cp932").splitlines()))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write_json(path, value):
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    world_path = "raw/trade/mof-products-import-annual.csv"
    region_path = "raw/trade-article/mof-middleeast-products-import-annual.csv"
    country_path = "raw/trade-article/mof-middleeast-countries-annual.csv"
    world_rows, region_rows, country_rows = map(read_csv, [world_path, region_path, country_path])
    assert "世界" in world_rows[0][0] and "中東" in region_rows[0][0]
    assert world_rows[3:7] == region_rows[3:7], "Product definitions/units differ"
    for _, _, code, col, unit in PRODUCTS:
        assert world_rows[4][col] == f"'{code}'"
        assert world_rows[5][col] == "数量"
        assert world_rows[6][col] == f"(単位：{unit})"
    world = {int(r[0]): r for r in world_rows[7:]}
    region = {int(r[0]): r for r in region_rows[7:]}
    countries = {int(r[0]): r for r in country_rows[4:]}
    assert sorted(world) == sorted(region) == list(range(1988, 2026))

    import_columns = [i for i, name in enumerate(country_rows[2]) if name.startswith("Imp-") and name != "Imp-Total"]
    observations = []
    for year in sorted(world):
        assert int(region[year][1]) == int(countries[year][2])
        assert sum(int(countries[year][i]) for i in import_columns) == int(countries[year][2])
        for product_id, label, code, col, unit in PRODUCTS:
            total, middleeast = int(world[year][col]), int(region[year][col])
            assert total > 0 and 0 <= middleeast <= total
            share = Decimal(middleeast) / Decimal(total) * 100
            observations.append({
                "year": year, "product_id": product_id, "product_label": label,
                "item_code": code, "world_quantity": total, "middleeast_quantity": middleeast,
                "quantity_unit": unit, "middleeast_share_pct": float(share),
                "period_type": "calendar_year", "status": "確々報値" if year == 2025 else "確定値",
                "world_source_id": "trade-world-products", "middleeast_source_id": "trade-middleeast-products",
            })
    lookup = {(o["product_id"], o["year"]): o for o in observations}
    years = list(range(2015, 2026))
    common_notes = [
        "日本の各品目の輸入数量に占める中東の割合。国内消費に占める輸入依存度ではありません。",
        "輸入相手の国・地域は原則として原産国による。積出港や輸送航路、材料をさかのぼる間接依存は示しません。",
        "中東の範囲は財務省の地域区分。2024年以前は確定値、2025年は確々報値（2026年9月22日取得版）。",
    ]
    chart_sources = ["trade-world-products", "trade-middleeast-products"]
    charts = [
        {
            "id": "crude-oil-middleeast-share",
            "title": "原油の輸入数量に占める中東の割合",
            "question": "原油の調達地域の偏りは、どの程度変わった？",
            "type": "line", "unit": "%", "period_type": "calendar_year", "period_label": "暦年",
            "periods": [str(year) for year in years],
            "series": [{"id": "crude-oil-middleeast", "label": "中東の割合", "values": [lookup[("crude_oil", year)]["middleeast_share_pct"] for year in years], "source_ids": chart_sources}],
            "notes": common_notes + ["原油及び粗油（概況品コード30301）の数量KLを使います。白書説明資料のUN Comtrade・HS2709・金額ベースの図を再現したものではありません。"],
            "derivation": "世界d61ca.csvと中東d62ca007.csvの概況品コード30301・数量（0始まり34列）を暦年で結合。中東の数量 ÷ 世界からの輸入数量 × 100。",
            "takeaway": "数量ベースの中東比率は2015年82.0%から2025年94.0%へ上昇。調達地域の偏りを示す数字で、供給停止の確率や政策の効果を直接示すものではありません。",
        },
        {
            "id": "fuels-middleeast-share-2025",
            "title": "2025年の中東比率は、燃料によって違う",
            "question": "「エネルギー」をひとまとめにせず、品目ごとに見ると？",
            "type": "bar", "unit": "%", "period_type": "category", "period_label": "2025暦年・品目別",
            "periods": [label for _, label, *_ in PRODUCTS],
            "series": [{"id": "middleeast-by-fuel", "label": "各品目の輸入数量に占める中東の割合", "values": [lookup[(product, 2025)]["middleeast_share_pct"] for product, *_ in PRODUCTS], "source_ids": chart_sources}],
            "notes": common_notes + ["原油はKL、LNG・LPGはMTの数量を、それぞれ同じ品目の世界計で割った比率です。異なる品目の数量や比率を合算しません。"],
            "derivation": "2025年の原油30301（列34・KL）、LNG3050103（列40・MT）、LPG3050101（列42・MT）で中東数量 ÷ 世界数量 × 100を個別に計算。列は0始まり。",
            "takeaway": "原油94.0%、LNG10.8%、LPG2.0%。低い中東比率だけでは、別の地域への集中や価格の波及、輸送上のリスクまで小さいとは判断できません。",
        },
    ]

    prior = {s["id"]: s for s in json.loads((ROOT / "research/trade-sources.json").read_text())}
    downloads = {s["local_path"]: s for s in json.loads((ROOT / "raw/trade-article/download-log.json").read_text())}
    def source(source_id, title, publisher, url, locator, kind, local_path, fetched):
        assert digest(local_path) == fetched["sha256"], f"Source changed: {local_path}"
        return {"id": source_id, "title": title, "publisher": publisher, "url": url, "locator": locator,
                "kind": kind, "local_path": local_path, "retrieved_at": fetched["retrieved_at"], "sha256": digest(local_path)}
    pdf = "raw/trade/meti-rieti-presentation-2026.pdf"
    pdf_url = "https://www.rieti.go.jp/jp/events/bbl/26072301_yoda.pdf"
    sources = [
        source("trade-2026-risk", "通商白書2026 解説資料：供給網リスクと新興国", "経済産業省 通商政策局（RIETI掲載）", pdf_url + "#page=18", "PDF物理p18・p21・p23（紙面17・20・22）。白書本文ではなく担当局の解説資料。", "official_explanation", pdf, prior["trade-meti-presentation-2026"]),
        source("trade-2026-strategy", "通商白書2026 解説資料：通商戦略と国内外の循環", "経済産業省 通商政策局（RIETI掲載）", pdf_url + "#page=55", "PDF物理p55・p57（紙面54・56）。目標・政策方針の説明であり、因果効果の推計ではない。", "official_explanation", pdf, prior["trade-meti-presentation-2026"]),
        source("trade-world-products", "貿易統計 世界・主要商品別輸入・年別CSV", "財務省 関税局・税関", prior["trade-mof-products-import-annual"]["download_url"], "1988–2025暦年。原油30301、LNG3050103、LPG3050101の数量列。CP932。", "original_statistics", world_path, prior["trade-mof-products-import-annual"]),
        source("trade-middleeast-products", "貿易統計 中東・主要商品別輸入・年別CSV", "財務省 関税局・税関", downloads[region_path]["url"], "1988–2025暦年。世界表と同一の概況品コード・数量単位を使用。CP932。", "original_statistics", region_path, downloads[region_path]),
        source("trade-middleeast-countries", "貿易統計 中東・国別輸出入・年別CSV", "財務省 関税局・税関", downloads[country_path]["url"], "地域内の国別輸入金額の合計と、主要商品別表の中東総額を1988–2025の38年で照合。国別原油数量の表ではない。", "original_statistics", country_path, downloads[country_path]),
        source("trade-statistics-definition", "貿易統計 よくある質問：相手国の定義", "財務省 関税局・税関", "https://www.customs.go.jp/toukei/sankou/howto/faq.htm", "「相手国はどのように決められていますか」：原則、輸入は原産国で計上。", "official_explanation", "raw/trade-article/customs-statistics-faq.html", downloads["raw/trade-article/customs-statistics-faq.html"]),
        source("trade-series-status", "貿易統計 輸出入額の推移・年別CSV公表案内", "財務省 関税局・税関", "https://www.customs.go.jp/toukei/suii/html/time.htm", "主要商品別：2024年以前は確定値、2025年は確々報値。地域・品目の原表へのリンク。", "official_explanation", "raw/trade-article/customs-annual-index.html", downloads["raw/trade-article/customs-annual-index.html"]),
    ]
    checks = {"years": [1988, 2025], "observations": len(observations), "region_country_total_match_years": 38,
              "all_quantities_within_world": True, "sample_2025": [lookup[(product, 2025)] for product, *_ in PRODUCTS]}
    write_json("processed/trade-article-data.json", {"retrieved_at": "2026-09-22", "observations": observations, "checks": checks})
    with (ROOT / "processed/trade-article-observations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(observations[0])); writer.writeheader(); writer.writerows(observations)
    article_path = ROOT / "content/trade.json"
    article = json.loads(article_path.read_text())
    article.update(charts=charts, sources=sources)
    source_ids = {s["id"] for s in sources}
    for section in article["sections"]:
        assert set(section["source_ids"]) <= source_ids
    for chart in charts:
        for series in chart["series"]:
            assert len(series["values"]) == len(chart["periods"])
            assert all(isinstance(v, (int, float)) for v in series["values"])
            assert set(series["source_ids"]) <= source_ids
    write_json("content/trade.json", article)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
