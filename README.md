# 経産省白書紹介サイトの調査・素材・操作試作

調査・構成改訂日：2026-09-22。政策の課題認識と対応の理由を伝え、根拠の統計を自分でも確かめられるサイトの構成試作です。資料収集・元データ・再生成処理を含みます。

- [企画・構成の提案](research/PROPOSAL.md)
- [政策の考え方を軸にしたサイト構成](research/SITE-STRUCTURE.md)
- [Cloudflare Workers向けの構成設計](research/ARCHITECTURE.md)
- [出典台帳 CSV](research/source-catalog.csv) / [JSON](research/source-catalog.json)
- [通商](research/trade.md) / [ものづくり・中小企業・小規模企業](research/industry-sme.md) / [エネルギー](research/energy.md)の調査記録
- [データ検証](verification/data-review.md) / [収集ファイルの検査](verification/inventory-checks.json)

## 操作試作を開く

このフォルダで次を実行して、ブラウザから `http://127.0.0.1:8765/` を開きます。

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory prototype
```

トップの全体像から、5冊の問題意識、エネルギーの解説、成果を確認する指標、データ比較へ進めます。白書別の要約は開閉でき、テーマのリンクからも開きます。分析画面では期間・系列・表示方法を変え、CSVと計算条件JSONを保存できます。操作対象は燃料輸入額と消費者物価指数。他の4テーマは白書要約までで、詳細記事は今後追加します。HTMLファイルを直接開くとJSONの読み込みが制限されるため、HTTPサーバーを使います。

## 保存済み原本から再生成する

Python 3で実行します。エネルギー・鉱工業のExcel読込には `openpyxl` が必要です。この環境では `/home/kazu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` に含まれています。

```bash
python3 scripts/trade_normalize.py
python3 scripts/energy_normalize.py
python3 scripts/industry_normalize.py
python3 scripts/build_demo_data.py
python3 scripts/assemble_catalog.py
```

原本再取得は出典台帳の `download_url` を使います。エネルギーには `scripts/energy_collect.py` もあります。外部取得にはネットワーク接続が必要です。取得済み版を再現したい場合は原本を上書きせず使用してください。

## 保存場所

| フォルダ | 内容 |
|---|---|
| `raw/` | 公式サイトから取得した資料・統計表・取得記録 |
| `processed/` | UTF-8 CSV/JSONに整形したデータ、定義、検査結果 |
| `assets/` | 公式資料の参照画像7枚。公開用の再利用許諾が揃った素材集ではありません |
| `prototype/` | 自作の図と、再集計したデータで動く試作 |
| `research/` | 企画、構成設計、分野別調査、出典台帳 |
| `scripts/` | 原本からの再生成・検査処理 |
| `verification/` | 独立データレビュー、ブラウザ操作で保存したCSV/JSON、検証記録 |

## Cloudflareへの公開準備

`wrangler.jsonc` は `prototype/` だけをWorkers Static Assetsとして配信する構成例です。`raw/` や権利未確認の参照画像は公開対象になりません。

Wranglerを導入し、Cloudflareアカウントで認証した後の公開コマンドは次です。**今回、このコマンドは実行していません。**

```bash
npx wrangler deploy
```

現時点の検証はローカルブラウザとJSON設定の構文確認までです。Wranglerビルド、本番デプロイ、カスタムドメイン、R2やD1との接続は未検証です。
