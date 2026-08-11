# SEO Entity Extraction & Analysis Dashboard

[繁體中文](#繁體中文) | [English](#english)

> A cloud-deployed SEO research dashboard that turns a user-entered keyword into auditable, article-level Entity data: SERP retrieval, full-page content extraction, AI Entity extraction, global dynamic clustering, Supabase storage, and authenticated visualisation.

| Link | Details |
|---|---|
| Live dashboard | https://seo-analyzer-neon-beta.vercel.app/ |
| Repository | https://github.com/Brittany3112/SEO-analyzer |
| Demo email | `demo@example.com` |
| Demo password | `demo0808` |

---

## English

### Overview

**SEO Entity Extraction & Analysis Dashboard** is a full-stack prototype for analysing the Google SERP of any user-entered keyword. After a signed-in user submits a keyword, the Vercel serverless API retrieves up to ten Taiwanese Google organic results through Serper, fetches accessible article content, extracts verifiable Entities with OpenAI, groups all validated Entities globally into query-specific themes, stores the results in Supabase, and refreshes the dashboard.

The design deliberately distinguishes **SERP results returned**, **articles successfully analysed**, **article-level Entity rows**, and **unique Entities**. This prevents unavailable pages, empty content, or unverified AI suggestions from being presented as completed analysis.

### Core Features

| Area | Implementation |
|---|---|
| Keyword input | The signed-in user can submit any keyword directly from the deployed dashboard. |
| SERP retrieval | Serper.dev is called with `gl=tw`, `hl=zh-tw`, and `num=10` to request up to ten organic results. |
| Full-content-only policy | The API retrieves the source page itself; SERP snippets are **not** used as a fallback for blocked or inaccessible pages. |
| Entity validation | Every AI-proposed Entity is verified with `content.count(entity)` before it is persisted. |
| Two-stage AI workflow | Stage 1 extracts Entities per article without local categories. Stage 2 clusters the complete validated Entity set globally for the query. |
| Dynamic themes | The clustering step creates at most five query-specific primary themes. Any remaining or ambiguous item is assigned to `其他` (Other). |
| Cloud data layer | Article-level Entity records and session metadata are batch-inserted into Supabase PostgreSQL. |
| Authenticated dashboard | Supabase Auth gates dashboard access. The frontend reads results through the Supabase client; server-side credentials remain in Vercel environment variables. |
| Visualisation | Chart.js renders the number of unique Entities per theme; WordCloud2.js displays aggregated Entity frequency; the table shows article-aggregated Entity occurrence counts. |
| Debug logging | Vercel Logs record SERP count, each article's extraction length, candidate and validated Entity counts, failures, final totals, clustering themes, and batch insert status. |

### Architecture and Data Flow

```text
Authenticated user enters a keyword
        ↓
index.html sends POST /api { "keyword": "..." }
        ↓
Vercel Serverless Function: api/index.py
        ↓
Serper.dev: request up to 10 Taiwanese organic search results
        ↓
For each returned result: fetch source page → extract article/main/body text
        ↓
Stage 1: OpenAI Entity extraction per article (no per-article theme assignment)
        ↓
Python exact-text validation: content.count(entity) > 0
        ↓
Aggregate unique validated Entities across all successful articles
        ↓
Stage 2: OpenAI global dynamic clustering (≤ 5 themes + 其他)
        ↓
Batch insert seo_data + insert seo_metadata in Supabase
        ↓
Dashboard reloads and visualises the latest analysis
```

### Why a Two-Stage Entity Workflow?

Classifying Entities one article at a time can produce inconsistent labels: the same Entity may be assigned to different themes because each model call sees only one article. This version separates extraction from grouping.

| Stage | Input | Output | Purpose |
|---|---|---|---|
| Stage 1 — extraction | One article’s accessible body text | Candidate Entity list | Finds relevant, text-grounded Entities from each article. |
| Python validation | Candidate Entity list + the same source text | Validated Entity rows and occurrence counts | Removes unsupported AI suggestions and calculates deterministic counts. |
| Stage 2 — global clustering | All validated unique Entities from the current query | One shared Entity → theme mapping | Produces consistent, query-specific categories across all source articles. |

### What the Dashboard Measures

| Dashboard item | Definition |
|---|---|
| `抓取篇數` / Successful articles | The number of URLs that produced accessible content **and** at least one Entity passing exact-text validation. It is not simply the number returned by the SERP API. |
| `不重複 Entity 數` | The number of distinct Entity strings across all successful articles. This is stored in `seo_metadata.total_entities_extracted`. |
| Entity row | One validated Entity in one source article. The same Entity appearing in multiple articles produces multiple rows in `seo_data`. |
| Entity occurrence count | The number of times an Entity string occurs in its extracted source text, calculated with Python `content.count(entity)`. |
| Bar chart | Number of unique Entities belonging to each theme. |
| Table total | Sum of Entity occurrence counts within that theme. |
| Average extracted text | Average number of extracted **characters** per successful article. The existing database column is named `avg_words_per_article` for historical reasons. |

### Project Structure

```text
SEO-analyzer/
├── api/
│   └── index.py                 # Vercel serverless API: SERP, extraction, validation, clustering, DB writes
├── index.html                   # Login, keyword input, Supabase reads, charts, word cloud, table
├── requirements.txt             # Production dependencies for Vercel
├── requirements-local.txt       # Optional local-development dependency list
├── main.py                      # Earlier local prototype; not used by the deployed dashboard workflow
└── README.md
```

### Supabase Schema

| Table | Key columns | Purpose |
|---|---|---|
| `seo_data` | `id`, `title`, `url`, `entity`, `count`, `theme` | One validated Entity record for one successfully analysed article. |
| `seo_metadata` | `id`, `query`, `total_articles`, `avg_words_per_article`, `total_entities_extracted`, `max_chars_limit` | Summary metadata for the latest analysis session. |

### Required Environment Variables

Set the following values in **Vercel → Project → Settings → Environment Variables**. Never commit them to GitHub.

```env
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional: defaults to gpt-5.6-sol if omitted
OPENAI_MODEL=gpt-5.6-sol
```

> `SUPABASE_SERVICE_ROLE_KEY` is used only by the Vercel serverless function to write analysis data. It must **never** be exposed in `index.html` or any browser-side JavaScript. The frontend uses a Supabase anonymous key together with Supabase Auth and Row Level Security.

### Deployment

1. Create a Supabase project, configure authentication, create the two tables above, and apply appropriate Row Level Security policies for authenticated dashboard reads.
2. Push the project to GitHub.
3. Import the GitHub repository in Vercel.
4. Add the required environment variables in Vercel.
5. Confirm that `requirements.txt` contains the runtime dependencies used by `api/index.py`.
6. Push to the `main` branch. Vercel will deploy automatically.
7. Visit the live dashboard, sign in, submit a keyword, wait for the analysis to finish, and refresh the dashboard when prompted.

```bash
git add api/index.py index.html requirements.txt README.md
git commit -m "docs: update deployed SEO analyzer README"
git push origin main
```

### Debugging an Analysis Run

Open **Vercel → Project → Logs** after submitting a keyword. The API prints a trace similar to the following:

```text
=== Start analysis: 4G吃到飽 ===
SERP returned 8 organic results; processing up to 10.
[3] Failed: https://example.com | HTTPError: 403 Client Error: Forbidden
First stage complete: 7 successful articles, 270 entity rows, 248 unique entities.
Global clustering themes: [...]
Batch inserted 270 entity rows into seo_data.
=== Analysis finished successfully ===
```

This makes it possible to distinguish the following situations without guessing:

| Log pattern | Interpretation |
|---|---|
| `SERP returned N organic results` | The search API returned `N` organic items. `num=10` requests a maximum, not a guaranteed count. |
| `Failed ... HTTPError: 403` | The source site blocked the HTTP request; the article is not analysed and no SERP snippet is substituted. |
| `Skipped: no extractable article content` | The page returned no usable body text. |
| `Skipped: no candidate entity passed exact-text validation` | The model proposed no Entity that could be verified in the extracted content. |
| `Success: N entities passed exact-text validation` | The article contributed data and is included in `抓取篇數`. |
| `POST /api ... 200` | The complete serverless request ended successfully. |

### Current Limitations and Next Improvements

This is an interview prototype and intentionally makes data-quality trade-offs explicit.

| Limitation | Current behaviour | Possible next step |
|---|---|---|
| Fewer than ten results | Serper may return fewer than ten organic results, and inaccessible pages are excluded. | Display both “SERP results returned” and “successfully analysed articles” in the dashboard. |
| Site blocking and client-side rendering | A page may return 403 or expose very little text to a simple HTTP request. | Add a browser-rendering fallback or an approved content-extraction service, subject to robots.txt and site policies. |
| Content length | Each page is limited to the first 2,000 extracted characters to control time and API cost. | Add configurable limits, chunking, or asynchronous jobs for deeper analysis. |
| Entity normalisation | Strings such as `遠傳` and `遠傳電信` remain separate Entities. | Add an optional canonicalisation/synonym layer after validation. |
| String matching | `content.count(entity)` is deterministic but may count a short string inside a larger expression. | Add boundary-aware matching rules for selected languages and entity types. |
| Word-cloud geometry | Word placement is affected by layout and string length, not only frequency. | Provide a ranked top-Entity list beside the word cloud. |
| Serverless runtime | Multi-article AI analysis can be slow and may be constrained by the selected hosting-plan execution limit. | Move long jobs to an asynchronous queue/background worker and poll for status. |

### Security Notes

The repository must not contain API keys, Supabase service-role credentials, or database passwords. The service-role key belongs only in Vercel environment variables. The demo account is intended solely for viewing the project dashboard.

### License

This project was developed as an educational technical assessment and portfolio prototype.

---

## 繁體中文

### 專案概述

**SEO Entity Extraction & Analysis Dashboard** 是一個可部署在雲端的 SEO SERP 分析原型。登入後，使用者可在儀表板直接輸入任意關鍵字；Vercel 後端會透過 Serper 取得台灣 Google 搜尋結果中的自然搜尋項目，抓取可存取網頁的正文、以 AI 提取 Entity、用程式驗證 Entity 是否真的存在於原文，再針對整個 query 的 Entity 集合進行全局動態分群，最後將結果寫入 Supabase 並呈現在受登入保護的儀表板中。

本專案刻意區分 **SERP API 回傳篇數**、**成功分析文章數**、**文章層級 Entity 資料列數** 與 **不重複 Entity 數**。因此，網站 403、抓不到正文或無法通過原文驗證的資料，不會被誤列為已完成分析。

### 核心功能

| 功能 | 說明 |
|---|---|
| 即時輸入關鍵字 | 已登入使用者可直接在 Vercel 儀表板輸入 keyword 並觸發分析。 |
| SERP 抓取 | 透過 Serper.dev，使用 `gl=tw`、`hl=zh-tw` 與 `num=10` 請求最多 10 筆自然搜尋結果。 |
| 僅使用全文內容 | 後端自行抓取來源頁面正文；若網站 403 或正文無法取得，**不使用 SERP snippet 代替文章內容**。 |
| Entity 原文驗證 | AI 提出每個 Entity 後，程式以 `content.count(entity)` 驗證 Entity 的確存在於該篇擷取文字內，才寫入資料庫。 |
| 兩階段 AI 流程 | 第一階段逐篇提取 Entity、暫不分類；第二階段彙整整個 query 的已驗證 Entity 後，再全局分群。 |
| 動態分群 | 每次 query 最多產生 5 個語意相關的主題；不適合主要主題或超出上限者會歸入「其他」，總類別數最多 6 個。 |
| Supabase 資料層 | 完成分群後，以 batch insert 將文章層級 Entity 資料寫入 `seo_data`，並將摘要寫入 `seo_metadata`。 |
| 登入保護 | 以 Supabase Auth 限制儀表板存取；前端透過 Supabase 匿名 key 與 RLS 讀取資料，敏感的後端金鑰只存在 Vercel。 |
| 儀表板視覺化 | Chart.js 顯示各主題的**不重複 Entity 數**；文字雲顯示 Entity 加總詞頻；表格顯示 Entity 及其文章內出現次數。 |
| 可追蹤除錯紀錄 | Vercel Logs 會記錄 SERP 回傳篇數、每篇正文長度、AI 候選數、驗證後數量、失敗原因、最終統計、分群與批次寫入狀態。 |

### 系統架構與資料流程

```text
已登入使用者輸入關鍵字
        ↓
index.html 將 { "keyword": "..." } POST 至 /api
        ↓
Vercel Serverless Function：api/index.py
        ↓
Serper.dev：請求最多 10 筆台灣 Google 自然搜尋結果
        ↓
逐篇抓取來源網頁，擷取 article / main / body 文字
        ↓
第一階段：逐篇以 AI 提取 Entity（暫不分類）
        ↓
Python 原文驗證：content.count(entity) > 0
        ↓
彙整所有成功文章的已驗證 Entity
        ↓
第二階段：全局動態分群（最多 5 個主題 + 其他）
        ↓
批次寫入 Supabase 的 seo_data，摘要寫入 seo_metadata
        ↓
儀表板重新讀取資料並更新圖表、文字雲與表格
```

### 為什麼要使用兩階段流程？

如果讓 AI 在每一篇文章中同時「提取並分類」，同一個 Entity 可能因文章脈絡不同而被分入不同類別。這版將「找出 Entity」和「為全部 Entity 建立共同分類」分開處理，讓同一個 query 的主題更一致。

| 階段 | 輸入 | 輸出 | 用意 |
|---|---|---|---|
| 第一階段：Entity 提取 | 單篇可存取文章的正文 | 候選 Entity 清單 | 從每篇文章找出與 query 相關、可辨識的實體。 |
| Python 驗證與計數 | 候選 Entity 清單 + 同一篇原文 | 通過驗證的 Entity 與次數 | 移除模型臆測，並以程式確定 Entity 的原文出現次數。 |
| 第二階段：全局分群 | 此次 query 的所有不重複、已驗證 Entity | 共同的 Entity → 主題對應 | 產生在全部文章中一致、且依 query 動態生成的分類。 |

### 儀表板數字如何定義？

| 儀表板項目 | 定義 |
|---|---|
| `抓取篇數` | 同時滿足「成功取得正文」與「至少一個 Entity 通過原文驗證」的 URL 數量；**不是**單純的 SERP 回傳筆數。 |
| `不重複 Entity 數` | 所有成功文章中，不重複的 Entity 字串數量；寫入 `seo_metadata.total_entities_extracted`。 |
| Entity 資料列 | 一個 Entity 在一篇來源文章中的驗證結果。同一 Entity 出現在多篇文章時，會有多筆 `seo_data`。 |
| Entity 出現次數 | Entity 字串於該篇已擷取原文內的次數，以 Python `content.count(entity)` 計算。 |
| 長條圖 | 每個主題包含多少個不重複 Entity。 |
| 表格右欄 | 該主題下所有 Entity 出現次數的加總。 |
| 每篇平均字數 | 實際是平均擷取的**字元數**。資料庫欄位仍沿用早期名稱 `avg_words_per_article`。 |

### 專案結構

```text
SEO-analyzer/
├── api/
│   └── index.py                 # Vercel API：SERP、抓取、Entity 驗證、分群、資料寫入
├── index.html                   # 登入、關鍵字輸入、Supabase 查詢、圖表、文字雲與表格
├── requirements.txt             # Vercel production dependencies
├── requirements-local.txt       # 選用的本機開發依賴
├── main.py                      # 早期本機原型；不參與目前 Vercel 即時分析流程
└── README.md
```

### Supabase 資料表

| 資料表 | 主要欄位 | 用途 |
|---|---|---|
| `seo_data` | `id`, `title`, `url`, `entity`, `count`, `theme` | 每篇成功分析文章的 Entity 資料。 |
| `seo_metadata` | `id`, `query`, `total_articles`, `avg_words_per_article`, `total_entities_extracted`, `max_chars_limit` | 最新一次分析的 query 與摘要統計。 |

### Vercel 環境變數

請在 **Vercel → Project → Settings → Environment Variables** 設定以下變數，且絕對不要提交至 GitHub。

```env
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# 選填；未設定時預設使用 gpt-5.6-sol
OPENAI_MODEL=gpt-5.6-sol
```

> `SUPABASE_SERVICE_ROLE_KEY` 只供 Vercel 後端寫入資料使用，不能寫進 `index.html` 或任何瀏覽器端程式。前端使用的是 Supabase anonymous key，並搭配 Supabase Auth 與 RLS。

### 部署步驟

1. 建立 Supabase 專案，建立上述兩張表，設定 Supabase Auth，並為已登入使用者設定必要的 RLS 讀取權限。
2. 將專案推送到 GitHub。
3. 在 Vercel 匯入該 GitHub repository。
4. 在 Vercel 加入所有必要環境變數。
5. 確認 `requirements.txt` 包含 `api/index.py` 所使用的 production dependencies。
6. 推送到 `main` branch 後，Vercel 會自動部署。
7. 開啟線上儀表板、登入、輸入 keyword，完成後依畫面提示重新整理即可看到新結果。

```bash
git add api/index.py index.html requirements.txt README.md
git commit -m "docs: update deployed SEO analyzer README"
git push origin main
```

### 如何看 Vercel Logs 除錯？

送出 query 後，到 **Vercel → Project → Logs** 查看。你會看到類似：

```text
=== Start analysis: 4G吃到飽 ===
SERP returned 8 organic results; processing up to 10.
[3] Failed: https://example.com | HTTPError: 403 Client Error: Forbidden
First stage complete: 7 successful articles, 270 entity rows, 248 unique entities.
Global clustering themes: [...]
Batch inserted 270 entity rows into seo_data.
=== Analysis finished successfully ===
```

| Log 訊息 | 代表意義 |
|---|---|
| `SERP returned N organic results` | SERP API 本次回傳 N 筆自然搜尋項目。`num=10` 是最多 10 筆的請求，不保證每次一定回傳 10 筆。 |
| `Failed ... HTTPError: 403` | 來源網站拒絕 HTTP 存取；系統會略過，且不會使用 snippet 假裝成全文。 |
| `Skipped: no extractable article content` | 頁面沒有可用的正文文字。 |
| `Skipped: no candidate entity passed exact-text validation` | AI 雖可能有候選詞，但沒有任何一個能在原文中通過驗證。 |
| `Success: N entities passed exact-text validation` | 該文章成功產生可驗證資料，會被計入「抓取篇數」。 |
| `POST /api ... 200` | 整個後端請求成功完成。 |

### 已知限制與下一步優化

| 限制 | 目前行為 | 可行的下一步 |
|---|---|---|
| 回傳少於 10 筆 | Serper 可能回傳少於 10 筆自然搜尋結果，且無法存取的頁面不會計入成功文章數。 | 前端同時顯示「SERP 回傳篇數」與「成功分析篇數」。 |
| 403 與 JavaScript 動態內容 | 部分網站拒絕 HTTP 抓取，或靜態 HTML 僅提供少量文字。 | 在遵守網站政策下，評估瀏覽器渲染或經核准的內容擷取服務。 |
| 每篇內容長度 | 為控制時間與 API 成本，每篇目前最多分析 2,000 字元。 | 提供可設定長度、文本切塊，或改成背景非同步任務。 |
| Entity 正規化 | `遠傳` 與 `遠傳電信` 等近義或上下位詞目前仍是不同 Entity。 | 加入可選的 canonicalisation / 同義詞對照層。 |
| `.count()` 字串計數 | 可重現、可驗證，但短字串可能出現在較長詞彙內。 | 針對不同語言與 Entity 類型加入邊界判斷。 |
| 文字雲視覺布局 | 字詞長度與排版也會影響大小和位置，不只取決於詞頻。 | 另外顯示可排序的 Top Entity 清單。 |
| Serverless 執行時間 | 多篇抓取與多次 AI 呼叫可能耗時，並受到託管方案限制。 | 將長任務移至 queue / background worker，再由前端輪詢進度。 |

### 安全提醒

Repository 不應包含 OpenAI、Serper、Supabase service-role 等 API key，也不應提交資料庫密碼。Service role key 僅能存在於 Vercel 環境變數。README 中的 demo 帳號只用於查看此作品的儀表板。

### 授權

本專案為教育、技術測驗與作品集展示用途。

---

**Last updated:** 2026-08-11
