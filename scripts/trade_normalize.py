#!/usr/bin/env python3
"""Normalize downloaded MOF calendar-year CSVs without third-party dependencies."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw/trade"
OUT = ROOT / "processed"


def read_csv(name):
    return list(csv.reader((RAW / name).read_text(encoding="cp932").splitlines()))


def main():
    world_rows = read_csv("mof-world-annual.csv")
    product_rows = read_csv("mof-products-import-annual.csv")
    assert world_rows[2] == ["Years", "Exp-Total", "Imp-Total"]
    assert product_rows[3][32] == "鉱物性燃料"
    assert product_rows[4][32] == "'3'"
    assert product_rows[5][33] == "金額"
    assert product_rows[6][33] == "(千円)"
    world = {int(r[0]): (int(r[1]), int(r[2])) for r in world_rows[4:]}
    products = {int(r[0]): r for r in product_rows[7:]}
    assert sorted(world) == list(range(1979, 2026))
    assert sorted(products) == list(range(1988, 2026))
    for year, row in products.items():
        assert int(row[1]) == world[year][1], (year, "world/product import totals disagree")

    # An independently formatted official HTML table checks the original CSV totals.
    html = (RAW / "customs-year-total.html").read_text(encoding="cp932")
    checked = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
        if len(cells) >= 3 and cells[0].isdigit() and int(cells[0]) in world:
            year = int(cells[0])
            values = tuple(int(c.replace(",", "")) for c in cells[1:3])
            assert values == world[year], (year, "HTML/CSV totals disagree")
            checked.append(year)
    assert len(checked) >= 40

    long_rows, wide_rows = [], []
    def add(year, series_id, label, value, source_id, unit="thousand_jpy"):
        long_rows.append(dict(year=year, series_id=series_id, label=label,
                              value=value, unit=unit, period_type="calendar_year",
                              geography="JPN", partner="WORLD", source_id=source_id,
                              vintage="2026-09-22", status="確々報値" if year == 2025 else "確定値"))

    for year, (exports, imports) in world.items():
        add(year, "exports", "輸出額", exports, "trade-mof-world-annual")
        add(year, "imports", "輸入額", imports, "trade-mof-world-annual")
        add(year, "trade_balance", "貿易収支（通関ベース）", exports - imports, "trade-mof-world-annual")
        row = dict(year=year, exports_thousand_jpy=exports, imports_thousand_jpy=imports,
                   trade_balance_thousand_jpy=exports - imports,
                   mineral_fuels_imports_thousand_jpy="", mineral_fuels_share_pct="",
                   period_type="calendar_year", status="確々報値" if year == 2025 else "確定値")
        if year in products:
            p = products[year]
            for col, sid, label in [(33, "mineral_fuels_imports", "鉱物性燃料輸入額"),
                                     (35, "crude_oil_imports", "原油及び粗油輸入額"),
                                     (37, "petroleum_products_imports", "石油製品輸入額"),
                                     (41, "lng_imports", "液化天然ガス輸入額"),
                                     (43, "lpg_imports", "液化石油ガス輸入額"),
                                     (45, "coal_imports", "石炭輸入額")]:
                add(year, sid, label, int(p[col]), "trade-mof-products-import-annual")
            fuel = int(p[33])
            assert 0 < fuel <= imports
            row["mineral_fuels_imports_thousand_jpy"] = fuel
            row["mineral_fuels_share_pct"] = round(100 * fuel / imports, 8)
        wide_rows.append(row)

    OUT.mkdir(exist_ok=True)
    for name, rows in [("trade-annual-long.csv", long_rows), ("trade-annual-wide.csv", wide_rows)]:
        with (OUT / name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    (OUT / "trade-annual.json").write_text(json.dumps({
        "retrieved_at": "2026-09-22", "period_type": "calendar_year", "nominal_real": "nominal",
        "value_basis": "customs; exports FOB, imports CIF", "unit": "thousand_jpy",
        "trillion_yen_divisor": 1000000000, "data": wide_rows,
        "verification": {"overlap_product_world_years": len(products), "html_csv_years": len(checked),
                         "html_csv_range": [min(checked), max(checked)]},
        "notes": ["年次の暦年系列。年度系列との同一横軸接続は不可。",
                  "貿易収支は輸出額－輸入額の独自算出。国際収支ベースの貿易収支とは異なる。",
                  "2025年は確々報値、2024年以前は確定値。取得時点の公表表を固定。",
                  "品目には包含関係がある。鉱物性燃料と内訳品目を合算しない。",
                  "原本統計表の正規化であり、税関申告個票ではない。"]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"series_rows": len(long_rows), "annual_rows": len(wide_rows),
                      "product_world_match_years": len(products), "html_csv_match_years": len(checked),
                      "latest": wide_rows[-1]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
