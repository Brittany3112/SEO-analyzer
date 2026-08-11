from http.server import BaseHTTPRequestHandler
import json
import os

import openai
import requests
from bs4 import BeautifulSoup
from supabase import create_client


# =====================================================
# 設定區：這些值由 Vercel Environment Variables 提供
# =====================================================
MAX_CHARS_LIMIT = 2000
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """接收前端傳來的 keyword，執行 SERP 分析並寫入 Supabase。"""
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data or b"{}")
            keyword = data.get("keyword", "4G 吃到飽").strip()

            if not keyword:
                self.send_json(400, {"status": "error", "message": "keyword 不可以是空白"})
                return

            # 每次新分析前，清空上一次的結果
            supabase.table("seo_data").delete().neq("id", 0).execute()
            supabase.table("seo_metadata").delete().neq("id", 0).execute()

            search_results = self.get_serp_data(keyword)
            total_entities = 0
            total_chars = 0
            processed_urls = set()
            processed_titles = set()

            # 題目要求分析 Google 第一頁前 10 名
            for item in search_results[:10]:
                url = item.get("link", "")
                title = item.get("title", "")
                article_has_data = False

                if not url:
                    continue

                try:
                    content = self.fetch_content(url)
                    if not content:
                        print(f"文章沒有可分析內容：{url}")
                        continue

                    total_chars += len(content)
                    ai_entities = self.analyze_with_ai(content, keyword)
                    seen_entities = set()

                                        # AI 只提出候選 Entity；Python 以原文驗證並重新計數
                    article_rows = []

                    for entity_item in ai_entities:
                        if not isinstance(entity_item, dict):
                            continue

                        entity_name = str(entity_item.get("entity", "")).strip()
                        if not entity_name or entity_name in seen_entities:
                            continue

                        seen_entities.add(entity_name)

                        # 確認 Entity 確實出現在抓回來的文章內容中
                        exact_count = content.count(entity_name)
                        if exact_count <= 0:
                            continue

                        theme = str(entity_item.get("theme", "其他")).strip() or "其他"

                        # 先放進清單，暫時不要立刻寫入 Supabase
                        article_rows.append({
                            "title": title,
                            "url": url,
                            "entity": entity_name,
                            "count": exact_count,
                            "theme": theme,
                        })

                    # 一篇文章的所有 Entity 都整理完後，只發送一次 Supabase request
                    if article_rows:
                        supabase.table("seo_data").insert(article_rows).execute()
                        article_has_data = True
                        total_entities += len(article_rows)

                    # 只有至少寫入一個 Entity，才算這篇文章成功進入 seo_data
                    if article_has_data:
                        processed_urls.add(url)
                        processed_titles.add(title)

                except Exception as error:
                    # 單篇文章失敗不影響其他文章繼續處理
                    print(f"處理文章失敗：{url}，原因：{error}")
                    continue

            # 這裡以實際寫入 seo_data 的 unique URL 數量作為文章篇數
            articles_count = len(processed_urls)
            unique_title_count = len(processed_titles)

            # 保留原本的資料表欄位名稱，避免影響前端
            supabase.table("seo_metadata").insert({
                "query": keyword,
                "total_articles": articles_count,
                "avg_words_per_article": (
                    total_chars // articles_count if articles_count > 0 else 0
                ),
                "total_entities_extracted": total_entities,
                "max_chars_limit": MAX_CHARS_LIMIT,
            }).execute()

            self.send_json(200, {
                "status": "success",
                "keyword": keyword,
                "articles": articles_count,
                "unique_titles": unique_title_count,
                "entities": total_entities,
            })

        except Exception as error:
            print(f"API 執行失敗：{error}")
            self.send_json(500, {"status": "error", "message": str(error)})

    def do_OPTIONS(self):
        """處理瀏覽器可能發送的 CORS preflight request。"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, status_code, payload):
        """統一回傳 JSON，避免每個錯誤分支重複寫 response header。"""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def get_serp_data(self, query):
        """呼叫 Serper.dev，取得 Google 第一頁的自然搜尋結果。"""
        url = "https://google.serper.dev/search"
        payload = {
            "q": query,
            "gl": "tw",
            "hl": "zh-tw",
            "num": 10,
        }
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=8,
        )
        response.raise_for_status()
        return response.json().get("organic", [])

    def fetch_content(self, url):
        """抓取網頁文字，優先使用 article/main，並排除常見雜訊區塊。"""
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        # 移除通常不是文章正文的區塊
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Meta description 可補充文章摘要
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_text = ""
        if meta_desc and meta_desc.get("content"):
            meta_text = meta_desc.get("content", "")

        # 優先抓文章主體；沒有時才退回整個 body
        main_content = soup.find("article") or soup.find("main") or soup.body or soup
        body_text = main_content.get_text(separator=" ", strip=True)

        text = f"{meta_text} {body_text}".strip()
        return text[:MAX_CHARS_LIMIT]

    def analyze_with_ai(self, content, keyword):
        """請模型提出 Entity 與初步分類，再由 do_POST 以原文驗證。"""
        prompt = f"""
請分析以下關於「{keyword}」的文章，提取與搜尋主題直接相關的重要 Entity。

只能回傳文章內容中實際出現的詞，不可以根據常識猜測文章沒有提到的品牌、認證或資訊。
請特別注意以下分類：
- 品牌：公司名、品牌名、產品名
- 價格：金額、月租、折扣、優惠價格
- 成分：原料、食材、營養成分
- 功效：功能、用途、適用對象
- 認證：HACCP、ISO 22000、CAS、SGS、產銷履歷等認證、檢驗標章與獎項
- 規格：容量、尺寸、製程、保存方式、技術規格
- 方案：方案名稱、期限、購買條件、配送條件
- 其他：確實與主題相關，但無法歸入上述分類的 Entity

請排除導覽列、頁尾、廣告、推薦文章，以及和「{keyword}」無關的地名或一般詞語。

請回傳 JSON，格式如下：
{{
    "entities": [
        {{
            "entity": "原文中的完整 Entity 名稱",
            "theme": "品牌|價格|成分|功效|認證|規格|方案|其他"
        }}
    ]
}}
"""

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是專業的中文 SEO Entity 抽取與分類工具。",
                },
                {
                    "role": "user",
                    "content": prompt + "\n\n文章內容：\n" + content,
                },
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("entities", [])
