"""Rebuild the comparison sample from saved primary statistical tables."""
import csv
import hashlib
import io
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    cpi_file = ROOT / "raw/context/cpi-monthly-2020base.csv"
    rows = list(csv.reader(io.StringIO(cpi_file.read_bytes().decode("cp932"))))
    headers, codes = rows[0], rows[2]
    wanted = {"cpi_all": "総合", "cpi_energy": "エネルギー", "cpi_ex_rent": "持家の帰属家賃を除く総合"}
    indices = {key: headers.index(label) for key, label in wanted.items()}
    observations = defaultdict(list)
    monthly = []
    for row in rows[6:]:
        period = row[0]
        if len(period) != 6 or not period.isdigit():
            raise ValueError(f"Unexpected CPI period: {period}")
        year, month = int(period[:4]), int(period[4:])
        if not 1 <= month <= 12:
            raise ValueError(period)
        for key, col in indices.items():
            value = Decimal(row[col])
            observations[(key, year)].append((month, value))
            monthly.append({"series_id": key, "period": f"{year}-{month:02d}", "value": str(value), "source_column_code": codes[col]})

    annual = {}
    incomplete = []
    for (key, year), values in observations.items():
        if sorted(month for month, _ in values) != list(range(1, 13)):
            incomplete.append({"series_id": key, "year": year, "months": len(values)})
            continue
        mean = sum(value for _, value in values) / Decimal(12)
        annual.setdefault(key, {})[year] = float(mean)
    for key in wanted:
        if abs(annual[key][2020] - 100) > 0.001:
            raise ValueError(f"CPI base check failed: {key}")

    trade = json.loads((ROOT / "processed/trade-annual.json").read_text())
    if trade["period_type"] != "calendar_year" or trade["unit"] != "thousand_jpy":
        raise ValueError("Unsupported trade definitions")
    trade_sources = json.loads((ROOT / "research/trade-sources.json").read_text())
    trade_source = next(s for s in trade_sources if s["id"] == "trade-mof-products-import-annual")
    trade_total_source = next(s for s in trade_sources if s["id"] == "trade-mof-world-annual")
    downloads = json.loads((ROOT / "raw/context/download-log.json").read_text())
    cpi_source = next(s for s in downloads if s["local_path"] == "raw/context/cpi-monthly-2020base.csv")

    series = []
    for key, label in wanted.items():
        series.append({
            "id": key, "label": "消費者物価・" + label, "publisher": "総務省統計局", "unit": "2020年=100", "period_type": "calendar_year", "aggregation": "各年1〜12月の月次指数の単純平均（丸め前）", "source_id": "stat-cpi-2020-monthly", "item_code": codes[indices[key]],
            "data": [{"year": year, "value": value} for year, value in sorted(annual[key].items())],
        })
    for key, label, field, source_id in [
        ("fuel_imports", "鉱物性燃料の輸入額", "mineral_fuels_imports_thousand_jpy", trade_source["id"]),
        ("exports", "日本の輸出額", "exports_thousand_jpy", trade_total_source["id"]),
        ("imports", "日本の輸入額", "imports_thousand_jpy", trade_total_source["id"]),
    ]:
        values = []
        for observation in trade["data"]:
            value = observation.get(field)
            if value in (None, ""):
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"Non-numeric trade observation: {field} {observation['year']}")
            values.append({"year": observation["year"], "value": value})
        series.append({"id": key, "label": label, "publisher": "財務省・税関", "unit": "千円", "period_type": "calendar_year", "aggregation": "公式暦年計を使用", "source_id": source_id, "item_code": "3" if key == "fuel_imports" else None, "source_column": "概況品コード3・金額（0始まり33列）" if key == "fuel_imports" else ("Exp-Total" if key == "exports" else "Imp-Total"), "data": values, "notes": "名目金額。輸入CIF・輸出FOB。2025年は確々報値。"})

    sources = [
        {"id": "stat-cpi-2020-monthly", "title": "2020年基準 消費者物価指数 全国 月次（小数第3位）", "publisher": "総務省統計局", "url": "https://www.stat.go.jp/data/cpi/1.htm", "download_url": cpi_source["url"], "sha256": cpi_source["sha256"], "retrieved_at": cpi_source["retrieved_at"], "local_path": cpi_source["local_path"], "notes": "2020年基準を固定。2026年は1〜8月しかなく、年平均の比較から除外。2025年基準への更新とは区別。"},
        *[{k: s.get(k) for k in ["id", "title", "publisher", "url", "download_url", "sha256", "retrieved_at", "local_path", "notes"]} for s in [trade_source, trade_total_source]],
    ]
    payload = {"schema_version": 1, "retrieved_at": "2026-09-22", "comparison_period": [2020, 2025], "period_type": "calendar_year", "series": series, "sources": sources, "incomplete_years_excluded": incomplete, "method": {"index": "100 * value / base_year_value", "yoy": "100 * (value / previous_calendar_year_value - 1)", "missing": "null; no interpolation; no zero filling", "note": "指数化しても系列の意味は同じにならない。価格、為替、数量、品目構成、補助政策などの影響を切り分けた因果分析ではない。"}}
    write_json(ROOT / "processed/comparison-data.json", payload)
    write_json(ROOT / "prototype/data.json", payload)
    with (ROOT / "processed/cpi-monthly-selected.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(monthly[0])); writer.writeheader(); writer.writerows(monthly)
    with (ROOT / "processed/comparison-observations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f); writer.writerow(["series_id", "year", "value", "unit", "period_type", "source_id"])
        for s in series:
            writer.writerows([s["id"], row["year"], row["value"], s["unit"], s["period_type"], s["source_id"]] for row in s["data"])
    report = {"cpi_base_2020": {key: annual[key][2020] for key in wanted}, "cpi_complete_calendar_years": sorted(annual["cpi_all"]), "incomplete_years_excluded": incomplete, "cpi_months": len(monthly) // len(wanted), "original_cpi_sha256": hashlib.sha256(cpi_file.read_bytes()).hexdigest(), "sample_2025": {s["id"]: next(x["value"] for x in s["data"] if x["year"] == 2025) for s in series}, "two_publishers": sorted({s["publisher"] for s in series}), "comparison_years": list(range(2020, 2026))}
    write_json(ROOT / "verification/data-checks.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
