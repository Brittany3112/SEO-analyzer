# SEO Entity Extraction & Analysis Dashboard

**🌐 Live Dashboard:** https://seo-analyzer-neon-beta.vercel.app/
**Demo Email:** `demo@example.com`
**Demo Password:** `demo1234`

## English Version

### 📋 Project Overview

A flexible, production-ready SEO data analysis tool that searches any keyword, scrapes search results, extracts entities using AI, classifies them by customizable themes, and visualizes the results in an interactive dashboard. Built with Python backend, Supabase cloud database, and deployed on Vercel.

### ✨ Features

- **Flexible Web Scraping**: Search any keyword using Serper API and scrape content from top results
- **AI-Powered Entity Extraction**: Uses OpenAI GPT-4o-mini to intelligently extract relevant entities from content
- **Rule-Based Classification**: Customizable classification system for categorizing entities by theme
- **Cloud Database**: Scalable data storage and management using Supabase PostgreSQL
- **Interactive Dashboard**: Web-based visualization deployed on Vercel with:
  - Real-time summary statistics
  - Theme distribution visualization
  - Detailed entity listing with occurrence counts
  - User authentication & RLS security
  - Responsive design for all devices

### 🔧 Tech Stack

**Backend:**
- Python 3.x
- requests, BeautifulSoup4 (web scraping)
- OpenAI API (entity extraction)
- Supabase Python SDK (database operations)
- python-dotenv (environment management)

**Frontend & Deployment:**
- HTML5 + Vanilla JavaScript
- Supabase JS SDK v2 (real-time database)
- Chart.js (interactive visualizations)
- **Deployed on Vercel** (serverless hosting)

**Database:**
- Supabase PostgreSQL (managed cloud database)
- Row-Level Security (RLS) for access control
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

3. **Run the scraper with any keyword**
```bash
python main.py
# Enter your search keyword when prompted
# Examples: "4G 吃到飽", "iPhone 15", "Python Framework", etc.
```

4. **Upload to Supabase**
```bash
python upload_to_supabase.py
```

5. **View the dashboard**
- Visit your deployed dashboard on Vercel (or open `index.html` locally)
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

Edit `main.py` to customize:
- `MAX_WORDS_LIMIT = 6000` - Maximum characters extracted per page
- Search results limit in `get_serp_data()` - currently set to 10 results
- Classification rules in `classify_by_rules()` - add/modify keywords for your domain

Edit `index.html` to customize:
- Summary statistics display and labels
- Chart colors and styling
- Table columns and formatting

### � Deployment on Vercel

1. **Push to GitHub**
```bash
git add .
git commit -m "Deploy to Vercel"
git push origin main
```

2. **Connect to Vercel**
- Visit [Vercel Dashboard](https://vercel.com)
- Click "New Project"
- Import your GitHub repository
- Set environment variables in Vercel settings:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`

3. **Deploy**
- Vercel automatically deploys on each push
- Your dashboard is live at `your-project.vercel.app`

### 🔐 Security Features

- Supabase Row-Level Security (RLS) for data access control
- Environment variables for sensitive credentials (never commit .env)
- User authentication required for dashboard access
- Secure API keys stored in Vercel environment

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

**🌐 線上儀表板:** https://seo-analyzer-neon-beta.vercel.app/
**Demo 帳號:** `demo@example.com`
**Demo 密碼:** `demo1234`

### 📋 專案概述

一個靈活、生產就緒的 SEO 資料分析工具，可搜尋任何關鍵字，抓取搜尋結果，使用 AI 智能提取實體，按可自訂主題分類，並在互動式儀表板中可視化呈現。採用 Python 後端、Supabase 雲端資料庫，並部署在 Vercel。

### ✨ 功能特色

- **靈活的網頁爬蟲**：使用 Serper API 搜尋任何關鍵字並抓取搜尋結果內容
- **AI 實體提取**：使用 OpenAI GPT-4o-mini 智能從內容中提取相關實體
- **自訂分類系統**：基於規則的可自訂分類系統，按主題分類實體
- **雲端資料庫**：使用 Supabase PostgreSQL 進行可擴展的資料存儲和管理
- **互動式儀表板**：部署在 Vercel 上的網頁可視化，包含：
  - 即時摘要統計數據
  - 主題分佈可視化
  - 詳細實體清單（含出現次數）
  - 用戶身份驗證和 RLS 安全性
  - 響應式設計（支持所有裝置）

### 🔧 技術堆棧

**後端：**
- Python 3.x
- requests、BeautifulSoup4（網頁爬蟲）
- OpenAI API（實體提取）
- Supabase Python SDK（資料庫操作）
- python-dotenv（環境變數管理）

**前端和部署：**
- HTML5 + 原生 JavaScript
- Supabase JS SDK v2（實時資料庫）
- Chart.js（互動式可視化）
- **部署在 Vercel**（無伺服器主機）

**資料庫：**
- Supabase PostgreSQL（管理型雲端資料庫）
- 列級安全性（RLS）進行存取控制
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

3. **執行爬蟲（支持任何關鍵字）**
```bash
python main.py
# 出現提示時輸入搜尋關鍵字
# 範例："4G 吃到飽"、"iPhone 15"、"Python 框架" 等
```

4. **上傳至 Supabase**
```bash
python upload_to_supabase.py
```

5. **查看儀表板**
- 訪問您在 Vercel 上部署的儀表板（或在本地開啟 `index.html`）
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

編輯 `main.py` 以自訂：
- `MAX_WORDS_LIMIT = 6000` - 每頁提取的最大字數
- `get_serp_data()` 中的搜尋結果限制 - 目前設為 10 筆結果
- `classify_by_rules()` 中的分類規則 - 為您的領域新增/修改關鍵字

編輯 `index.html` 以自訂：
- 摘要統計標籤和顯示內容
- 圖表顏色和樣式
- 表格欄位和格式

### � Vercel 部署

1. **推送至 GitHub**
```bash
git add .
git commit -m "部署至 Vercel"
git push origin main
```

2. **連接至 Vercel**
- 訪問 [Vercel 儀表板](https://vercel.com)
- 點擊「New Project」
- 匯入您的 GitHub 儲存庫
- 在 Vercel 設置中設定環境變數：
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`

3. **部署**
- Vercel 在每次推送時自動部署
- 您的儀表板在 `your-project.vercel.app` 上線

### 🔐 安全功能

- Supabase 列級安全性（RLS）進行資料存取控制
- 敏感認證使用環境變數儲存（切勿提交 .env）
- 儀表板存取需要用戶身份驗證
- 安全 API 金鑰儲存在 Vercel 環境變數

### 🐛 錯誤處理

- 分類前驗證實體名稱
- 過濾掉空值/null 實體
- 優雅處理網路逾時
- 提供詳細的主控台日誌用於除錯

### � Use Cases

- **Market Research**: Analyze competitor mentions and market trends
- **SEO Analysis**: Track entity mentions across search results
- **Product Research**: Extract product features and pricing from web content
- **Industry Monitoring**: Track mentions of companies, technologies, or trends
- **Content Analysis**: Extract and categorize key topics from any domain
- **Competitive Intelligence**: Monitor competitor information across the web

### 📈 Future Enhancements

- Export data to CSV/Excel
- Advanced filtering and search capabilities
- Historical data comparison and trends
- Custom theme templates and rules editor
- Real-time data updates via webhooks
- Multi-language entity extraction
- Sentiment analysis integration
- API endpoint for programmatic access
- Batch processing for multiple queries

### � 使用案例

- **市場研究**：分析競爭對手提及和市場趨勢
- **SEO 分析**：追蹤實體在搜尋結果中的提及
- **產品研究**：從網頁內容提取產品功能和定價
- **行業監測**：追蹤公司、技術或趨勢的提及
- **內容分析**：提取和分類任何領域的關鍵主題
- **競爭智報**：監測網路上的競爭對手資訊

### 📈 未來增強功能

- 匯出資料為 CSV/Excel
- 進階篩選和搜尋功能
- 歷史資料比較和趨勢分析
- 自訂主題範本和規則編輯器
- 透過 Webhook 進行即時資料更新
- 多語言實體提取
- 情感分析整合
- 用於程式存取的 API 端點
- 批量處理多個查詢

### �📝 授權

本專案用於教育和研究目的。

---

**Last Updated:** 2026-08-09
