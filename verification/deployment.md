# Cloudflare Workersへの公開

公開日：2026-09-23（日本時間）。ユーザーのコミット・デプロイ依頼に基づく。

- 公開URL：https://meti-whitepaper-prototype.kazumasa.workers.dev/
- Worker：`meti-whitepaper-prototype`
- 配信元コミット：`d7e72a9` — 白書5テーマの記事と再分析できるグラフを追加
- Cloudflare Version ID：`d8a784b0-597f-49f0-b9fc-4fa8b793c485`
- Wrangler：4.136.1。既存OAuth認証を使用し、新しいWorkerとして公開。
- 配信対象：`prototype/` の26ファイル、541,045 bytes。ローカルハッシュは `deployment.json`。
- Durable Objects・D1・R2のbindingなし。原資料PDF・Excelや認証情報は配信対象ディレクトリに含まない。

## 公開前

`verify_articles.py`：5記事、260リンク、CSV・静的表の152観測を確認。両JavaScriptの構文検査、Wrangler `deploy --dry-run` 成功。原本は取得時の改行・空白を維持し、編集したコード・資料はCRLF対応のGit差分検査を通した。原資料の取得版ハッシュを変えないため、原本を整形し直していない。

## 公開後のブラウザ確認

公開URLでトップと5記事へ移動し、全10図の描画を確認。CloudflareのHTML正規化により記事URLは `/themes/energy` 等に転送される。相対リンク、CSS・JavaScript、JSON読込はこのURLでも動作した。

- トップ比較：開始年を2022へ変更。2025年の輸入額65.7、家庭エネルギー価格101.1（2022=100）。
- 小規模事業：7本の棒、系列の非表示・再表示を確認。
- ものづくり：業種比較を2021開始・指数化へ変更。2021=100の表示を確認。
- 賃金8点、通商の折れ線11点・棒3本、エネルギー75点を確認。
- 操作時のブラウザ警告・JavaScriptエラーなし。

PythonによるHTTPS全ファイル比較は403（Cloudflare 1010）で完了できなかった。通常のブラウザでは上記ページと操作を確認できている。設定ファイルの非公開パスのブラウザ検査はクライアント側で遮断され、HTTP 404の直接確認は未了。ファイルの公開範囲はローカル配信ディレクトリとWranglerの26件のアップロード一覧で確認した。

CSVリンクの操作は実施したが、アプリ内ブラウザからOSへの保存完了は未確認。CSVの内容照合は前の独立検証記録を参照。大規模負荷・費用・全スクリーンリーダーの検証は行っていない。
