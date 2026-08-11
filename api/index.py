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

            for item in search_results[:10]:
                url = item['link']
                content = self.fetch_content(url)
                total_words += len(content)
                entities = self.analyze_with_ai(content, keyword)
                total_entities += len(entities)

                for ent in entities:
                    supabase.table("seo_data").insert({
                        "title": item['title'],
                        "url": url,
                        "entity": ent['entity'],
                        "count": ent['count'],
                        "theme": ent['theme']
                    }).execute()

            # ✅ 寫入 metadata 摘要
            articles_count = min(len(search_results), 5)
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
    prompt = f"""分析關於『{keyword}』的文章，盡可能多地提取重要實體（至少15個以上）。
    
分類規則：
- 品牌：公司名、產品名、品牌名
- 價格：任何金額、價格、折扣資訊
- 技術：製程、成分、規格、認證標章
- 合約：方案、期限、條件、優惠活動

回傳JSON格式: {{"entities": [{{"entity": "...", "count": 1, "theme": "..."}}]}}"""
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt + "\n\n" + content}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content).get('entities', [])



