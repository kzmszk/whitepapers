"""Rebuild small-business charts from published SME survey aggregate tables."""
import csv
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
EMPLOYEES = ROOT / "raw/small-business/employees-by-size-2025.xlsx"
COSTS = ROOT / "raw/small-business/sales-costs-by-size-2025.xlsx"


def main():
    employees = openpyxl.load_workbook(EMPLOYEES, read_only=True, data_only=True).active
    costs = openpyxl.load_workbook(COSTS, read_only=True, data_only=True).active
    assert employees["I7"].value == "母集団企業数"
    assert employees["L6"].value == "合計_法人企業_計"
    assert costs["M6"].value == "合計_法人企業_5人以下"
    labels = ["5人以下", "6〜20人", "21〜50人", "51人以上"]
    cells = ["M7", "N7", "O7", "P7"]
    counts = [employees[cell].value for cell in cells]
    total = employees["L7"].value
    assert sum(counts) == total == 1701437
    assert counts == [1134765, 366437, 121673, 78562]
    shares = [round(value / total * 100, 2) for value in counts]
    for cell in ["L7", *cells]:
        assert employees[cell].value == costs[cell].value
    amounts = [costs[cell].value for cell in ["M10", "M18", "M27"]]
    sales = costs["M9"].value
    assert [costs[cell].value for cell in ["I10", "I18", "I27"]] == ["売上原価", "販売費及び一般管理費", "営業利益"]
    assert abs(sum(amounts) - sales) < 0.002
    proportions = [round(value / sales * 100, 2) for value in amounts]
    notes = ["2025年中小企業実態基本調査・確報。調査対象の中小法人企業。個人企業を含まない。",
             "従業者規模は法定の『小規模企業』区分と一致しない。5人以下を小規模企業全体と読み替えない。",
             "標本を母集団へ拡大推計した公表集計。個票でも全企業の悉皆調査でもない。"]
    charts = [
        {"id": "corporations-by-size", "title": "調査対象の中小法人企業の約3分の2は、従業者5人以下",
         "question": "小さな組織で経営する法人は、どのくらいある？", "type": "bar",
         "unit": "企業数の構成比（%）", "period_type": "category", "period_label": "2025年調査・従業者規模別",
         "periods": labels,
         "series": [{"id": "corporation-share", "label": "中小法人企業の構成比", "values": shares,
                     "source_ids": ["small-business-employees"]}],
         "notes": notes + ["母集団企業数は2023年次フレームに基づく推計。従業者数は2025年6月1日現在。"],
         "derivation": "原表『会社全体の従業者数(1)産業別・従業者規模別表』M7:P7を法人企業計L7で除し100倍。企業数4区分の合計がL7と一致することを確認。",
         "takeaway": "法人企業170万1,437社のうち、従業者5人以下は113万4,765社、66.69%。多くの法人が小さな組織で経営している。"},
        {"id": "small-corporation-costs", "title": "売上100円に対し、営業利益は約3円",
         "question": "売上から営業の費用を引くと、利益はどれほど残る？", "type": "bar",
         "unit": "売上高に対する割合（%）", "period_type": "category", "period_label": "2024年度決算・法人企業の従業者5人以下",
         "periods": ["売上原価", "販売費・一般管理費", "営業利益"],
         "series": [{"id": "sales-composition", "label": "売上高に対する割合", "values": proportions,
                     "source_ids": ["small-business-sales-costs"]}],
         "notes": notes + ["各社の比率の単純平均ではなく、公表された金額総額同士の比。対象企業の業種構成の影響を受ける。",
                           "営業利益は利息などの営業外損益や税金を差し引く前。売上原価と販管費の双方に人件費が含まれ、営業利益すべてが賃上げ原資になるわけではない。",
                           "各企業の最近決算期1年間。消費税込み・税抜きの回答が混在する。"],
         "derivation": "原表『売上高及び営業費用(1)産業別・従業者規模別表』M10(売上原価)、M18(販管費)、M27(営業利益)をM9(売上高)で除し100倍。3項目の和を売上高と照合。単位は原表の百万円から比率へ換算。",
         "takeaway": "この集計では売上原価69.13%、販管費27.87%、営業利益3.00%。売上だけでなく、費用と残る利益を把握する必要がある。原価管理の因果効果を示す図ではない。"}
    ]
    (ROOT / "processed/small-business-charts.json").write_text(json.dumps(charts, ensure_ascii=False, indent=2) + "\n")
    rows = [{"chart_id": charts[0]["id"], "category": label, "raw_numerator": count,
             "raw_denominator": total, "value": share, "unit": "percent", "source_cell": cell,
             "source_id": "small-business-employees"} for label, count, share, cell in zip(labels, counts, shares, cells)]
    rows += [{"chart_id": charts[1]["id"], "category": label, "raw_numerator": amount,
              "raw_denominator": sales, "value": proportion, "unit": "percent", "source_cell": cell,
              "source_id": "small-business-sales-costs"} for label, amount, proportion, cell in
             zip(charts[1]["periods"], amounts, proportions, ["M10", "M18", "M27"])]
    with (ROOT / "processed/small-business-observations.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    checks = {"source_hashes": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [EMPLOYEES, COSTS]},
              "corporations_total": total, "size_counts_sum": sum(counts), "counts_agree_between_two_tables": True,
              "sales_million_yen": sales, "costs_and_profit_sum_million_yen": sum(amounts),
              "cost_identity_error_million_yen": abs(sum(amounts) - sales), "observations": rows}
    (ROOT / "processed/small-business-checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
    article = ROOT / "content/small-business.json"
    if article.exists():
        content = json.loads(article.read_text()); content["charts"] = charts
        article.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"charts": len(charts), "observations": len(rows), "size_shares": shares, "cost_shares": proportions}))


if __name__ == "__main__":
    main()
