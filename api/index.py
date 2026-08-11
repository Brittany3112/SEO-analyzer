from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
import openai
import os
from supabase import create_client

# ===== 設定區（寫在最上面 ，class 外面）=====
MAX_CHARS_LIMIT = 2000
# 請在 Vercel Settings -> Environment Variables 設定這些
openai.api_key = os.getenv("OPENAI_API_KEY" )
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== 主程式（class 在下面）=====
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        keyword = data.get('keyword', '4G 吃到飽')

        try:
            # ✅ 清空兩張表的舊資料
            supabase.table("seo_data").delete().neq("id", 0).execute()
            supabase.table("seo_metadata").delete().neq("id", 0).execute()

            # 1. 搜尋與爬取
            search_results = self.get_serp_data(keyword)
            total_entities = 0
            total_words = 0

            processed_urls = set()
            processed_titles = set()
            
            for item in search_results[:10]:
                url = item.get('link', '')
                title = item.get('title', '')

                try:
                    content = self.fetch_content(url)
                    if not content:
                        continue

                    total_words += len(content)
                    entities = self.analyze_with_ai(content, keyword)

                    # AI 只負責提出候選 Entity；實際次數由 Python 從文章原文計算
                    for ent in entities:
                        entity_name = str(ent.get("entity", "")).strip()

                        if not entity_name:
                            continue

                        # 到實際抓回來的文章內容中精確計數
                        exact_count = content.count(entity_name)

                        # 找不到的 Entity 不寫入資料庫，避免 AI 幻覺污染結果
                        if exact_count <= 0:
                            continue

                        theme = ent.get("theme", "其他") or "其他"

                        supabase.table("seo_data").insert({
                            "title": item["title"],
                            "url": url,
                            "entity": entity_name,
                            "count": exact_count,
                            "theme": theme
                        }).execute()

                        # 只有真正通過原文驗證、寫入資料庫的 Entity 才計入總數
                        total_entities += 1

                        article_has_data = True
                        total_entities += 1

                        if article_has_data:
                            processed_urls.add(url)
                            processed_titles.add(title)

                except Exception as e:
                    print(f"處理文章失敗：{url}，原因：{e}")
                    continue


            # ✅ 寫入 metadata 摘要
            articles_count = len(processed_urls)
            unique_title_count = len(processed_titles)

            supabase.table("seo_metadata").insert({
                "query": keyword,
                "total_articles": articles_count,
                "avg_words_per_article": total_words // articles_count if articles_count > 0 else 0,
                "total_entities_extracted": total_entities,
                "max_chars_limit": MAX_CHARS_LIMIT
            }).execute()


            # 回傳成功
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode())



    def get_serp_data(self, query):
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "gl": "tw", "hl": "zh-tw"} )
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        return requests.post(url, headers=headers, data=payload).json().get('organic', [])

    def fetch_content(self, url):
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # 優先抓取 Meta Description 和 Keywords
        meta_desc = soup.find("meta", attrs={"name": "description"})
        text = (meta_desc["content"] if meta_desc else "") + " " + soup.get_text()
        return text[:MAX_CHARS_LIMIT]

    def analyze_with_ai(self, content, keyword):
        prompt = f"""請從以下文章正文抽取與搜尋主題直接相關的 Entity。
                    只能回傳文章中實際出現的詞，不可以根據常識補猜。
                    每個 Entity 必須附上原文證據片段。

                    請特別檢查以下類型：
                    1. 品牌與產品
                    2. 價格與折扣
                    3. 成分與原料
                    4. 功效與適用對象
                    5. 認證、檢驗、標章與獎項，例如 HACCP、ISO 22000、CAS、SGS、產銷履歷
                    6. 規格、容量、保存方式與製程
                    7. 購買條件、方案與配送資訊

                    請排除：
                    - 導覽列、頁尾、廣告、推薦文章
                    - 與主題無關的地名或一般詞語
                    - 只出現一次且沒有主題關聯的雜訊，除非它是重要認證、品牌或規格

                    回傳 JSON：
                    {
                    "entities": [
                        {
                        "entity": "原文中的完整名稱",
                        "theme": "品牌|價格|成分|功效|認證|規格|方案|其他",
                        "evidence": "包含該 Entity 的原文短句"
                        }
                    ]
                    }
                    """

        MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是專業的 SEO 語義分析與中文實體抽取工具。"},
                {"role": "user", "content": prompt + "\n\n" + content}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content).get('entities', [])



