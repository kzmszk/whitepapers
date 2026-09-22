"""Combine collection manifests and verify every listed local artifact."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = {
    "worldbank-gdp-real.json": ("worldbank-gdp-real", "日本の実質GDP（constant LCU）API応答", "World Bank", "補助候補。試作には未使用。白書の特定図との対応は未確認。"),
    "worldbank-gdp-metadata.json": ("worldbank-gdp-metadata", "実質GDP指標の定義・データ源", "World Bank", "補助候補の定義情報。"),
    "mhlw-wage-index.html": ("mhlw-wage-page", "毎月勤労統計2025年12月確報 掲載ページ", "厚生労働省", "2026-02-25公表の確報ページ。賃金指数の出典。"),
    "wages-2025-final.xlsx": ("mhlw-wage-indices", "毎月勤労統計 時系列表第1表 賃金指数", "厚生労働省", "2022〜2025年の年平均等。2024年ベンチマーク更新に伴い、公表前年比は隣接する指数の単純比と異なる。"),
    "wages-2025-final.pdf": ("mhlw-wage-release", "毎月勤労統計2025年12月確報 概況・利用上の注意", "厚生労働省", "計算上の注意を原PDFで確認。"),
    "cpi-annual.html": ("stat-cpi-annual-page", "消費者物価指数 2025年平均結果", "総務省統計局", "2020年基準の公表年平均を確認するページ。"),
    "cpi-results.html": ("stat-cpi-results", "消費者物価指数 結果一覧", "総務省統計局", "2020年基準と2025年基準の公開先を区別。"),
    "cpi-monthly-2020base.csv": ("stat-cpi-2020-monthly", "消費者物価指数 2020年基準 全国月次・小数第3位", "総務省統計局", "2020年1月〜2026年8月、786列。試作では3系列を抽出し、12か月そろう2020〜2025年を再集計。"),
    "meti-terms.html": ("meti-terms", "経済産業省 利用規約", "経済産業省", "公式検索内容を確認。直接取得は403。"),
}


def main():
    context = []
    for log in json.loads((ROOT / "raw/context/download-log.json").read_text()):
        name = Path(log["local_path"]).name
        identifier, title, publisher, note = CONTEXT[name]
        success = log["availability"] == "downloaded"
        item = {**log, "id": identifier, "title": title, "publisher": publisher, "edition": "取得日2026-09-22の保存版", "download_url": log["url"], "format": Path(name).suffix[1:], "notes": note, "whitepaper_ref": "横断分析の補助統計。白書掲載時の版と同一と確認したものではない。"}
        item["local_path"] = log["local_path"] if success else None
        item["rights_url"] = "https://data.worldbank.org/summary-terms-of-use" if publisher == "World Bank" else ("https://www.mhlw.go.jp/chosakuken/index.html" if publisher == "厚生労働省" else "https://www.stat.go.jp/info/riyou.html" if publisher == "総務省統計局" else "https://www.meti.go.jp/main/rules.html")
        item["rights_notes"] = "出典・加工内容を明記。第三者素材の条件は別途確認。World Bankはデータセット固有条件も確認。"
        context.append(item)
    (ROOT / "research/context-sources.json").write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n")
    entries = []
    for file in sorted((ROOT / "research").glob("*-sources.json")):
        entries.extend(json.loads(file.read_text()))
    assert len({e["id"] for e in entries}) == len(entries), "Duplicate source IDs"
    verified = []
    for entry in entries:
        rel = entry.get("local_path")
        if not rel:
            continue
        path = ROOT / rel
        assert path.is_file(), f"Missing file: {rel}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert entry.get("sha256") == digest, f"Checksum mismatch: {rel}"
        verified.append(rel)
    (ROOT / "research/source-catalog.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    fields = ["id", "title", "publisher", "edition", "format", "availability", "url", "download_url", "local_path", "sha256", "retrieved_at", "rights_url", "rights_notes", "whitepaper_ref", "notes"]
    with (ROOT / "research/source-catalog.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); writer.writeheader()
        for entry in entries:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in entry.items()})
    originals = sorted({p for p in verified if p.startswith("raw/")})
    formats = Counter(Path(p).suffix.lower() for p in originals)
    summary = {"catalog_entries": len(entries), "verified_unique_local_artifacts": len(set(verified)), "original_files": len(originals), "original_formats": dict(formats), "original_bytes": sum((ROOT/p).stat().st_size for p in originals), "reference_images": len({p for p in verified if p.startswith("assets/")}), "missing_or_discovered_only": sum(not e.get("local_path") for e in entries), "all_listed_local_sha256_match": True}
    (ROOT / "verification/inventory-checks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
