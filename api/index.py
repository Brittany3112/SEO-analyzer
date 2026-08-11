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
MAX_DYNAMIC_THEMES = 5  # 加上「其他」後，整體最多顯示 6 個類別

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """接收 keyword，執行兩階段 SERP Entity 分析並寫入 Supabase。"""
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data or b"{}")
            keyword = data.get("keyword", "4G 吃到飽").strip()

            if not keyword:
                self.send_json(400, {"status": "error", "message": "keyword 不可以是空白"})
                return

            # 每次新分析前，清空上一次結果。
            supabase.table("seo_data").delete().neq("id", 0).execute()
            supabase.table("seo_metadata").delete().neq("id", 0).execute()

            search_results = self.get_serp_data(keyword)
            validated_rows = []
            total_chars = 0
            processed_urls = set()
            processed_titles = set()

            # -------------------------------------------------
            # 第一階段：逐篇文章抽取 Entity，再用原文驗證與計數。
            # 此階段不分類，避免每篇文章各自產生不一致的主題。
            # -------------------------------------------------
            for item in search_results[:10]:
                url = item.get("link", "")
                title = item.get("title", "")

                if not url:
                    continue

                try:
                    content = self.fetch_content(url)
                    if not content:
                        print(f"文章沒有可分析內容：{url}")
                        continue

                    candidate_entities = self.extract_entities(content, keyword)
                    seen_entities = set()
                    article_rows = []

                    for candidate in candidate_entities:
                        if isinstance(candidate, dict):
                            entity_name = str(candidate.get("entity", "")).strip()
                        else:
                            entity_name = str(candidate).strip()

                        if not entity_name or entity_name in seen_entities:
                            continue

                        seen_entities.add(entity_name)

                        # 用 Python 重新計數，避免模型回傳原文沒有出現的 Entity。
                        exact_count = content.count(entity_name)
                        if exact_count <= 0:
                            continue

                        article_rows.append({
                            "title": title,
                            "url": url,
                            "entity": entity_name,
                            "count": exact_count,
                        })

                    if article_rows:
                        validated_rows.extend(article_rows)
                        total_chars += len(content)
                        processed_urls.add(url)
                        processed_titles.add(title)

                except Exception as error:
                    # 單篇文章 403、timeout 或解析失敗時，不中斷整體分析。
                    print(f"處理文章失敗：{url}，原因：{error}")
                    continue

            # -------------------------------------------------
            # 第二階段：整合所有已驗證 Entity，做全局動態主題分群。
            # 最多 5 個動態主題；無法歸類或超出的 Entity 一律進「其他」。
            # -------------------------------------------------
            entity_totals = {}
            for row in validated_rows:
                entity = row["entity"]
                entity_totals[entity] = entity_totals.get(entity, 0) + row["count"]

            theme_map = self.cluster_entities_globally(keyword, entity_totals)

            for row in validated_rows:
                row["theme"] = theme_map.get(row["entity"], "其他")

            # 所有文章統一完成分群後，一次批次寫入，避免逐 Entity insert。
            if validated_rows:
                supabase.table("seo_data").insert(validated_rows).execute()

            articles_count = len(processed_urls)
            unique_title_count = len(processed_titles)
            total_entities = len(validated_rows)
            unique_entities = len(entity_totals)

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
                "unique_entities": unique_entities,
                "themes": sorted(set(theme_map.values())),
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
        """統一回傳 JSON。"""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def get_serp_data(self, query):
        """呼叫 Serper.dev，取得 Google 第一頁最多 10 筆自然搜尋結果。"""
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "gl": "tw",
                "hl": "zh-tw",
                "num": 10,
            },
            timeout=8,
        )
        response.raise_for_status()
        return response.json().get("organic", [])

    def fetch_content(self, url):
        """抓取完整網頁正文，優先 article/main，並排除常見雜訊區塊。"""
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_text = meta_desc.get("content", "") if meta_desc else ""

        main_content = soup.find("article") or soup.find("main") or soup.body or soup
        body_text = main_content.get_text(separator=" ", strip=True)

        return f"{meta_text} {body_text}".strip()[:MAX_CHARS_LIMIT]

    def extract_entities(self, content, keyword):
        """第一階段：只抽取 Entity，不指定預先定義的 theme。"""
        prompt = f"""
請從以下關於「{keyword}」的文章正文中，盡可能完整地提取與搜尋主題直接相關的重要 Entity。

Entity 可以包含品牌、產品名稱、型號、價格、規格、技術名詞、成分、功效、認證、方案、期限、服務或其他具體且可識別的概念。

規則：
1. 只能回傳文章正文中實際出現的 Entity，不可以依常識補猜。
2. 只回傳 Entity 名稱，不要分類、不要解釋、不要回傳出現次數。
3. 請排除完整句子、導覽列文字、廣告詞、頁尾資訊、泛用詞與和「{keyword}」無關的地名。
4. Entity 盡量保持原文中的完整表達，例如「ISO 22000」不可簡化成「ISO」。

請回傳 JSON：
{{
  "entities": ["Entity A", "Entity B"]
}}
"""

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是嚴謹的中文 SEO Entity extraction 工具。只抽取原文可驗證的實體。",
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

    def cluster_entities_globally(self, keyword, entity_totals):
        """第二階段：對本次 query 的全部已驗證 Entity 建立一致、動態的主題分類。"""
        if not entity_totals:
            return {}

        entities_for_prompt = [
            {"entity": entity, "total_occurrences": count}
            for entity, count in sorted(
                entity_totals.items(), key=lambda pair: pair[1], reverse=True
            )
        ]

        prompt = f"""
你是 SEO 語義分群分析師。以下是關鍵字「{keyword}」在 Google 第一頁文章中抽取、並已由程式驗證過的 Entity 清單。

請根據本次搜尋主題與 Entity 的語義關係，建立動態主題分類。

硬性規則：
1. 最多只能建立 {MAX_DYNAMIC_THEMES} 個自訂主題；此外固定保留「其他」作為唯一的 fallback 類別，因此總類別數最多 {MAX_DYNAMIC_THEMES + 1} 個。
2. 主題名稱必須簡潔、可讀、以繁體中文表達，例如「資費與價格」、「網路規格」、「產品功能」、「購買方案」。不要使用過度籠統的名稱，例如「分類一」。
3. 每個 Entity 必須分配到一個主題。若不適合前述主要主題，請分配為「其他」。
4. 不可新增、改寫、合併或遺漏任何 Entity；回傳的 entity 字串必須與輸入完全相同。
5. 同一個 Entity 只能出現一次。
6. 不要使用固定通用分類（例如固定的品牌／價格／規格清單）；主題應隨「{keyword}」的語意動態生成。

請只回傳 JSON：
{{
  "assignments": [
    {{"entity": "輸入清單中的原始 Entity", "theme": "動態主題名稱或其他"}}
  ]
}}

Entity 清單：
{json.dumps(entities_for_prompt, ensure_ascii=False)}
"""

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是嚴謹的中文 SEO 主題分群工具，必須遵守最大主題數與完整 Entity 對應規則。",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        assignments = result.get("assignments", [])

        valid_entities = set(entity_totals.keys())
        theme_map = {}
        dynamic_themes = []

        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue

            entity = str(assignment.get("entity", "")).strip()
            theme = str(assignment.get("theme", "其他")).strip() or "其他"

            if entity not in valid_entities or entity in theme_map:
                continue

            if theme == "其他":
                theme_map[entity] = "其他"
                continue

            # 若模型提出超過 5 個動態主題，額外主題自動收斂至「其他」。
            if theme not in dynamic_themes:
                if len(dynamic_themes) >= MAX_DYNAMIC_THEMES:
                    theme_map[entity] = "其他"
                    continue
                dynamic_themes.append(theme)

            theme_map[entity] = theme

        # 模型漏分或回傳不符規則的 Entity，一律安全歸類至「其他」。
        for entity in valid_entities:
            theme_map.setdefault(entity, "其他")

        return theme_map
