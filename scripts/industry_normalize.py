#!/usr/bin/env python3
"""Normalize the downloaded METI/e-Stat IIP workbook; never mix CY and FY."""

import csv
import hashlib
import json
import math
import re
from pathlib import Path

import openpyxl


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "raw/industry-sme/iip-industry-annual-quarterly-original-20260914.xlsx"
MONTHLY = ROOT / "raw/industry-sme/iip-industry-monthly-original-20260914.xlsx"
SOURCE_ID = "industry-iip-annual-20260914"
MEASURES = {"生産計": ("production", "生産"), "出荷計": ("shipments", "出荷")}


def normalize():
    workbook = openpyxl.load_workbook(SOURCE, data_only=True, read_only=True)
    records = []
    missing = []
    for sheet, (measure, label) in MEASURES.items():
        rows = list(workbook[sheet].values)
        assert "2020＝100.0" in rows[0][0], rows[0][0]
        columns = [(column, int(period[:4])) for column, period in enumerate(rows[2])
                   if isinstance(period, str) and re.fullmatch(r"\d{4}CY", period)]
        assert [year for _, year in columns] == list(range(2018, 2026))
        for row in rows[3:]:
            if not isinstance(row[0], (int, float)) or not row[1]:
                continue
            industry_code = str(int(row[0]))
            for column, year in columns:
                raw = row[column]
                if not isinstance(raw, (int, float)):
                    missing.append({"sheet": sheet, "industry_code": industry_code,
                                    "year": year, "raw_value": raw})
                    continue
                assert math.isfinite(raw)
                records.append({"year": year, "series_id": f"iip_{measure}_{industry_code}",
                                "label": f"{row[1]}・{label}", "value": float(raw),
                                "unit": "index_2020_100", "frequency": "calendar_year",
                                "geography": "Japan", "industry_code": industry_code,
                                "industry_name": row[1], "measure": measure,
                                "source_id": SOURCE_ID})

    output = ROOT / "processed"
    output.mkdir(exist_ok=True)
    with (output / "industry-annual-indices.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    series = []
    for measure, label in MEASURES.values():
        for code, industry in [("1000000000", "鉱工業"), ("1100000000", "製造工業")]:
            selected = [row for row in records if row["measure"] == measure and row["industry_code"] == code]
            assert len(selected) == 8
            series.append({"id": f"iip_{measure}_{code}", "label": f"{industry}・{label}",
                           "unit": "index_2020_100", "frequency": "calendar_year",
                           "geography": "Japan", "seasonal_adjustment": "unadjusted",
                           "source_id": SOURCE_ID,
                           "observations": [{"year": row["year"], "value": row["value"]} for row in selected]})

    monthly = openpyxl.load_workbook(MONTHLY, data_only=True, read_only=True)
    checks = []
    for sheet, (measure, _) in MEASURES.items():
        rows = list(monthly[sheet.removesuffix("計")].values)
        for code in [1000000000, 1100000000]:
            monthly_row = next(row for row in rows[3:] if row[0] == code)
            for year in range(2018, 2026):
                values = [monthly_row[column] for column, period in enumerate(rows[2])
                          if str(period).startswith(str(year)) and re.fullmatch(r"\d{6}", str(period))]
                assert len(values) == 12, (sheet, code, year, values)
                expected = next(row["value"] for row in records if row["measure"] == measure
                                and row["industry_code"] == str(code) and row["year"] == year)
                difference = abs(sum(values) / 12 - expected)
                assert difference <= 0.051, (sheet, code, year, difference)
                checks.append({"measure": measure, "industry_code": str(code), "year": year,
                               "annual_value": expected, "monthly_mean": round(sum(values) / 12, 6)})

    result = {"source_id": SOURCE_ID,
              "source_url": "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040172370&fileKind=0",
              "source_published_at": "2026-09-14",
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "notes": ["暦年の原指数。年度・四半期・季節調整済指数を混ぜていない。",
                        "生産は付加価値額ウエイトによる数量指数。名目付加価値額や売上金額ではない。",
                        "鉱工業には製造工業を含む。両者や業種階層を合算しない。",
                        "白書刊行後の2026年9月公表データ。白書掲載時点の値と異なる場合がある。"],
              "series": series}
    (output / "industry-annual-indices.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    report = {"annual_rows": len(records), "missing_rows": missing,
              "crosscheck": "32 annual values compared to 12-month arithmetic means; tolerance 0.051 index points",
              "checks": checks}
    (output / "industry-normalization-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"annual_rows": len(records), "missing_rows": len(missing),
                      "demo_series": len(series), "annual_monthly_checks": len(checks)}, ensure_ascii=False))


if __name__ == "__main__":
    normalize()
