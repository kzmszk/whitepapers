# 記事と図表の受け渡し

各担当は `content/<id>.json` を所有する。idは wages / small-business / industry / trade / energy。UTF-8、日本語、プレーンテキスト（HTMLを埋め込まない）。サイト生成と共通UIは親担当が所有する。

```json
{
  "id": "industry",
  "title": "人手が減るなかで、どう作り続ける？",
  "subtitle": "短い補足",
  "lead": "白書の課題認識と対応の筋道を150字程度で説明",
  "whitepaper_label": "ものづくり白書2026",
  "edition_note": "所管・確認した版、本文/概要/説明資料の区別",
  "sections": [
    {"heading":"何を課題と捉えている？", "kind":"policy", "paragraphs":["本文"], "source_ids":["source-id"]}
  ],
  "flow": [{"title":"課題", "text":"短い説明"}, {"title":"対応", "text":"短い説明"}, {"title":"目指す姿", "text":"目標であり実績と区別"}],
  "charts": [
    {"id":"production", "title":"図のタイトル", "question":"この図で何を確かめる？", "type":"line", "unit":"2020年=100", "period_type":"calendar_year", "period_label":"暦年", "periods":["2020","2021"], "series":[{"id":"manufacturing","label":"製造工業","values":[100,104],"source_ids":["source-id"]}], "notes":["単位・対象の注記"], "derivation":"原表のどの列/行をどう加工したか", "takeaway":"データから読めること。因果効果とは区別"}
  ],
  "outcomes":[{"title":"成果を確かめる指標", "text":"確認方法と限界"}],
  "questions":["さらに調べる問い"],
  "sources":[{"id":"source-id","title":"資料名","publisher":"公表者","url":"https://official...","locator":"第何章/表名/PDF物理ページ等","kind":"whitepaper|official_summary|official_explanation|original_statistics","local_path":"raw/...（取得時のみ、未取得ならnull）","retrieved_at":"ISO日時またはYYYY-MM-DD","sha256":"取得ファイルのSHA256、未取得ならnull"}]
}
```

sectionsは課題、対応の理由、具体策、暮らし・仕事との関係、両立すべき点/限界を含む5〜7項目。kindはpolicy（白書の説明）かeditorial（当サイトの整理）。主要な主張のsource_idsを必ず持つ。記事は全体で1000〜1800字程度を目安にする。flowは原文を読んだ担当の要約図で、政策効果の証明ではない。

chartsは1〜3件の実データ。typeはlineかbar。period_typeはcalendar_year / fiscal_year / survey_year / category、年のperiodsは西暦文字列。全seriesのvalues長はperiodsと一致し、数値またはnull。各図は単位と期間種別を一つにそろえる。親項目と内訳の重複合算はしない。系列ごとのsource_ids必須。

原データの整理・集計は `scripts/build_<id>_data.py` 等で再実行可能にし、公開用データと原表を照合する。既存ファイルは上書きせず、新規資料はテーマごとのrawサブフォルダへ置く。公開集計表から取り出した値を個票と呼ばない。欠測をゼロにしない。白書の主張とデータの観察、サイトの解釈を区別する。

`research/articles/<id>.md` に確認資料・主要数値の照合・残る制約を簡潔に記録する。原本取得できない箇所は出典と取得状況を明記し、取得できたと表現しない。ブラウザ・prototype・共通台帳・READMEは親担当が編集する。Cloudflare/Durable Objects/デプロイには一切アクセスしない。
