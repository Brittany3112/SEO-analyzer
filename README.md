# SEO Data Analysis Dashboard - 4G Unlimited Plan

## English Version

### 📋 Project Overview

A comprehensive SEO data analysis tool that scrapes search results for "4G 吃到飽" (4G Unlimited Data Plan) queries, extracts entities using AI, classifies them by theme, and visualizes the results in an interactive dashboard.

### ✨ Features

- **Web Scraping**: Searches Google using Serper API and scrapes content from top results
- **AI Entity Extraction**: Uses OpenAI GPT-4o-mini to intelligently extract relevant entities from content
- **Automatic Classification**: Rule-based classification system categorizing entities into 6 themes:
  - 電信品牌 (Telecom Brands)
  - 手機與硬體 (Mobile Devices & Hardware)
  - 價格 (Pricing)
  - 合約 (Contracts & Plans)
  - 技術 (Technology & Specs)
  - 其他 (Other)
- **Cloud Database**: Data storage and management using Supabase PostgreSQL
- **Interactive Dashboard**: Web-based visualization with:
  - Summary statistics
  - Theme distribution bar chart
  - Detailed entity listing with occurrence counts
  - User authentication

### 🔧 Tech Stack

**Backend:**
- Python 3.x
- requests, BeautifulSoup4 (web scraping)
- OpenAI API (entity extraction)
- Supabase SDK (database)
- python-dotenv (environment management)

**Frontend:**
- HTML5
- Vanilla JavaScript
- Supabase JS SDK v2
- Chart.js (data visualization)

**Database:**
- Supabase PostgreSQL with Row-Level Security (RLS)
- Two main tables: `seo_metadata` and `seo_data`

### 📁 Project Structure

```
4G_AllYouCanEat/
├── main.py                      # Web scraper & entity extraction
├── upload_to_supabase.py        # Data uploader to Supabase
├── index.html                   # Interactive dashboard
├── results.json                 # Output data file
├── .env                         # Environment variables (not tracked)
└── README.md                    # This file
```

### 🚀 Quick Start

#### Prerequisites

- Python 3.8+
- Google Serper API key
- OpenAI API key
- Supabase project (URL & API key)

#### Installation

1. **Clone/Setup the project**
```bash
cd 4G_AllYouCanEat
pip install -r requirements.txt  # or install individually
```

2. **Configure environment variables** - Create `.env` file:
```env
SERPER_API_KEY=your_serper_key
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. **Run the scraper**
```bash
python main.py
# Enter keyword when prompted (default: "4G 吃到飽")
```

4. **Upload to Supabase**
```bash
python upload_to_supabase.py
```

5. **View the dashboard**
- Open `index.html` in a web browser
- Login with your Supabase credentials
- View statistics, charts, and entity details

### 📊 Data Pipeline

```
Google Search → Scrape Websites → Extract Entities (AI) 
→ Classify by Rules → JSON Output → Supabase Upload → Dashboard Visualization
```

### 🗂️ Database Schema

**seo_metadata** (Search session metadata)
- query: search keyword
- total_articles: number of pages scraped
- total_words: total characters extracted
- avg_words_per_article: average characters per page
- total_entities_extracted: number of entities found
- max_words_limit: character limit per page
- created_at: timestamp

**seo_data** (Individual entities)
- title: source article title
- url: source URL
- entity: entity name
- theme: category (電信品牌, 手機與硬體, 價格, 合約, 技術, 其他)
- count: occurrence count in content

### ⚙️ Configuration

Edit `main.py` to adjust:
- `MAX_WORDS_LIMIT = 6000` - Maximum characters extracted per page
- Search engine results limit in `get_serp_data()` - currently set to 10 results

### 🔐 Security Features

- Supabase Row-Level Security (RLS) for access control
- Environment variables for sensitive credentials
- User authentication required for dashboard access

### 🐛 Error Handling

- Validates entity names before classification
- Filters out empty/null entities
- Handles network timeouts gracefully
- Comprehensive console logging for debugging

### 📈 Future Enhancements

- Export data to CSV/Excel
- Advanced filtering and search
- Historical data comparison
- Custom theme templates
- Multi-language support

### 📝 License

This project is for educational and research purposes.

---

## 中文版本

### 📋 專案概述

一個綜合性的 SEO 資料分析工具，專門搜尋「4G 吃到飽」相關內容，使用 AI 智能提取實體，按主題分類，並在互動式儀表板中可視化呈現結果。

### ✨ 功能特色

- **網頁爬蟲**：使用 Serper API 搜尋並抓取 Google 搜尋結果內容
- **AI 實體提取**：使用 OpenAI GPT-4o-mini 智能從內容中提取相關實體
- **自動分類**：基於規則的分類系統，將實體分為 6 個主題：
  - 電信品牌
  - 手機與硬體
  - 價格
  - 合約
  - 技術
  - 其他
- **雲端資料庫**：使用 Supabase PostgreSQL 進行資料存儲和管理
- **互動式儀表板**：包含以下功能的網頁可視化：
  - 摘要統計數據
  - 主題分佈長條圖
  - 詳細實體清單（含出現次數）
  - 用戶身份驗證

### 🔧 技術堆棧

**後端：**
- Python 3.x
- requests、BeautifulSoup4（網頁爬蟲）
- OpenAI API（實體提取）
- Supabase SDK（資料庫）
- python-dotenv（環境變數管理）

**前端：**
- HTML5
- 原生 JavaScript
- Supabase JS SDK v2
- Chart.js（資料可視化）

**資料庫：**
- Supabase PostgreSQL（含列級安全性 RLS）
- 兩個主要表：`seo_metadata` 和 `seo_data`

### 📁 專案結構

```
4G_AllYouCanEat/
├── main.py                      # 網頁爬蟲 & 實體提取
├── upload_to_supabase.py        # 上傳資料到 Supabase
├── index.html                   # 互動式儀表板
├── results.json                 # 輸出資料檔
├── .env                         # 環境變數（不追蹤）
└── README.md                    # 本檔案
```

### 🚀 快速開始

#### 系統需求

- Python 3.8+
- Google Serper API 金鑰
- OpenAI API 金鑰
- Supabase 專案（URL 和 API 金鑰）

#### 安裝步驟

1. **設置專案**
```bash
cd 4G_AllYouCanEat
pip install -r requirements.txt  # 或逐個安裝套件
```

2. **配置環境變數** - 創建 `.env` 檔案：
```env
SERPER_API_KEY=你的_serper_金鑰
OPENAI_API_KEY=你的_openai_金鑰
SUPABASE_URL=你的_supabase_網址
SUPABASE_KEY=你的_supabase_金鑰
```

3. **執行爬蟲**
```bash
python main.py
# 出現提示時輸入關鍵字（預設值："4G 吃到飽"）
```

4. **上傳至 Supabase**
```bash
python upload_to_supabase.py
```

5. **查看儀表板**
- 在網頁瀏覽器中開啟 `index.html`
- 使用 Supabase 認證登入
- 查看統計資料、圖表和實體詳情

### 📊 資料流程

```
Google 搜尋 → 抓取網站 → 提取實體（AI）
→ 按規則分類 → JSON 輸出 → 上傳至 Supabase → 儀表板可視化
```

### 🗂️ 資料庫架構

**seo_metadata**（搜尋工作階段中繼資料）
- query：搜尋關鍵字
- total_articles：抓取的頁面數
- total_words：提取的總字數
- avg_words_per_article：每頁平均字數
- total_entities_extracted：找到的實體數量
- max_words_limit：每頁字數限制
- created_at：時間戳記

**seo_data**（個別實體）
- title：源文章標題
- url：源 URL
- entity：實體名稱
- theme：分類（電信品牌、手機與硬體、價格、合約、技術、其他）
- count：在內容中出現的次數

### ⚙️ 設置選項

編輯 `main.py` 以調整：
- `MAX_WORDS_LIMIT = 6000` - 每頁提取的最大字數
- `get_serp_data()` 中的搜尋結果限制 - 目前設為 10 筆結果

### 🔐 安全功能

- Supabase 列級安全性（RLS）進行存取控制
- 敏感認證使用環境變數儲存
- 儀表板存取需要用戶身份驗證

### 🐛 錯誤處理

- 分類前驗證實體名稱
- 過濾掉空值/null 實體
- 優雅處理網路逾時
- 提供詳細的主控台日誌用於除錯

### 📈 未來增強功能

- 匯出資料為 CSV/Excel
- 進階篩選和搜尋功能
- 歷史資料比較
- 自訂主題範本
- 多語言支援

### 📝 授權

本專案用於教育和研究目的。

---

**Last Updated:** 2026-08-09
