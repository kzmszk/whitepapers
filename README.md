# 経済の見取り図：白書の解説と公開データ分析

調査・構成改訂日：2026-09-22。政策の課題認識と対応の理由を伝え、根拠の統計を自分でも確かめられるサイトです。資料収集・元データ・再生成処理を含みます。

- [企画・構成の提案](research/PROPOSAL.md)
- [政策の考え方を軸にしたサイト構成](research/SITE-STRUCTURE.md)
- [Cloudflare Workers向けの構成設計](research/ARCHITECTURE.md)
- [記事ごとの根拠・集計記録](research/articles/README.md) / [記事の出典台帳](research/article-source-catalog.json)
- [初期収集の出典台帳 CSV](research/source-catalog.csv) / [JSON](research/source-catalog.json)
- [通商](research/trade.md) / [ものづくり・中小企業・小規模企業](research/industry-sme.md) / [エネルギー](research/energy.md)の調査記録
- [データ検証](verification/data-review.md) / [収集ファイルの検査](verification/inventory-checks.json)

## 操作試作を開く

このフォルダで次を実行して、ブラウザから `http://127.0.0.1:8765/` を開きます。

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory prototype
```

トップの全体像と5冊の要約から、全5テーマの詳細記事へ進めます。各記事は課題・対応・暮らしとの関係・成果の確かめ方を説明し、政策の筋道を図解しています。

| 記事 | 実データのグラフ |
|---|---|
| [エネルギー](http://127.0.0.1:8765/themes/energy.html) | 自給率、エネルギー起源CO₂、部門別消費量 |
| [賃上げ](http://127.0.0.1:8765/themes/wages.html) | 名目・実質賃金の公表前年比 |
| [ものづくり](http://127.0.0.1:8765/themes/industry.html) | 生産と出荷、4業種の生産指数 |
| [供給網](http://127.0.0.1:8765/themes/trade.html) | 原油の中東依存の推移、燃料3品目の中東比率 |
| [地域の事業](http://127.0.0.1:8765/themes/small-business.html) | 法人企業の従業者規模構成、売上に対する費用・利益 |

記事に10点の操作グラフ、トップに財務省の輸入額と総務省CPIを重ねる比較があります。系列選択、時系列の期間変更、正の水準値の指数化、表・CSV・計算条件JSONを利用できます。記事本文と元の数値表は静的HTMLに含まれ、JavaScriptがなくても読めます。トップの比較にはHTTPサーバーが必要です。

## 保存済み原本から再生成する

Python 3で実行します。エネルギー・鉱工業のExcel読込には `openpyxl` が必要です。この環境では `/home/kazu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` に含まれています。

```bash
python3 scripts/trade_normalize.py
python3 scripts/energy_normalize.py
python3 scripts/industry_normalize.py
python3 scripts/build_demo_data.py
python3 scripts/assemble_catalog.py
python3 scripts/build_energy_data.py
python3 scripts/build_wages_data.py
python3 scripts/build_industry_data.py
python3 scripts/build_trade_data.py
python3 scripts/build_small_business_data.py
python3 scripts/build_articles.py
python3 scripts/verify_articles.py
```

原本再取得は出典台帳の `download_url` を使います。エネルギーには `scripts/energy_collect.py` もあります。外部取得にはネットワーク接続が必要です。取得済み版を再現したい場合は原本を上書きせず使用してください。

## 保存場所

| フォルダ | 内容 |
|---|---|
| `raw/` | 公式サイトから取得した資料・統計表・取得記録 |
| `processed/` | UTF-8 CSV/JSONに整形したデータ、定義、検査結果 |
| `assets/` | 公式資料の参照画像7枚。公開用の再利用許諾が揃った素材集ではありません |
| `content/` | 5記事の本文、説明の種別、参照資料、グラフ定義 |
| `prototype/` | 静的な記事HTML、自作図、操作グラフ、JSON・CSV |
| `research/` | 企画、構成設計、分野別調査、出典台帳 |
| `scripts/` | 原本からの再生成・検査処理 |
| `verification/` | 独立データレビュー、ブラウザ操作で保存したCSV/JSON、検証記録 |

## Cloudflareへの公開

Durable Objectsへのリクエストは発生しません。D1・R2・外部APIへのブラウザ接続もありません。

`wrangler.jsonc` は `prototype/` だけをWorkers Static Assetsとして配信する構成例です。`raw/` や権利未確認の参照画像は公開対象になりません。

2026-09-23に [Cloudflare Workersへ公開](https://meti-whitepaper-prototype.kazumasa.workers.dev/) しました。配信元コミットは `d7e72a9`、Wrangler 4.136.1を使用。検証記録は [deployment.md](verification/deployment.md)。

認証済みアカウントから再公開するコマンドは次です。

```bash
npx wrangler@4.136.1 deploy
```

Wranglerの事前検査・デプロイ、公開環境のトップと5記事、グラフ操作を確認済みです。カスタムドメイン、R2・D1接続は使用していません。

## 確認できた範囲

5テーマの記事と指標は執筆・実装済みです。白書全文・全図表の原データを網羅的に取得したという意味ではありません。本文未取得の部分は公式概要・担当官の説明資料を明示し、非公開の企業個票は未取得として扱います。エネルギー白書は2025年版を使用し、2026年版は刊行未確認です。自給率はPDFの公表値を抽出したもので、IEA原表から再計算した値ではありません。
