import requests
from bs4 import BeautifulSoup
import json
import openai
import os
from dotenv import load_dotenv

# 改每篇抓取字數上限，只要改這裡一次就好
MAX_WORDS_LIMIT = 6000

# 載入 .env 檔案
load_dotenv()

# 安全地把金鑰抓出來用
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_serp_data(query):
    print(f"正在搜尋關鍵字: {query}...")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "tw", "hl": "zh-tw"})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload)
    return response.json().get('organic', [])[:10]


def fetch_content(url):
    try:
        print(f"正在抓取內文: {url}")
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 拿掉 script 和 style
        for script in soup(["script", "style"]):
            script.extract()

        raw_text = soup.get_text(separator=' ', strip=True)
        print(f"-> 該網頁總字數: {len(raw_text)} 字")

        return raw_text[:MAX_WORDS_LIMIT], len(raw_text)
    except Exception as e:
        return f"抓取失敗: {e}", 0


def classify_by_rules(entity_name):
    if not entity_name or not isinstance(entity_name, str):
        return "其他"
    
    name = entity_name.strip().lower()
    if not name:
        return "其他"

    # 1. 電信營運商
    telecom_keywords = ["中華", "遠傳", "台灣大哥大", "亞太", "台灣之星", "cht", "fet", "twm"]    
    # 2. 手機與硬體品牌/裝置
    hardware_keywords = [
        "apple", "samsung", "vivo", "oppo", "小米", "sony", "realme", "htc", "nothing", "asus", "motorola",
        "iphone", "ipad", "galaxy", "watch", "airpods", "z fold", "空機", "預付卡"
    ]   
    # 3. 價格與資費數字
    price_keywords = ["元", "$", "月租", "價格", "費率", "優惠價", "0元"]    
    # 4. 合約與方案類型
    contract_keywords = ["個月", "年", "綁約", "期限", "合約", "銀髮", "學生", "企業", "兒童"]    
    # 5. 技術與網速規格
    tech_keywords = ["5g", "4g", "不限速", "限速", "熱點", "volte", "網速", "吃到飽", "mbps", "gb", "上網", "通話"]

    if any(k in name for k in telecom_keywords):
        return "電信品牌"
    if any(k in name for k in hardware_keywords):
        return "手機與硬體"
    if any(k in name for k in price_keywords):
        return "價格"
    if any(k in name for k in contract_keywords) or "方案" in name:
        return "合約"
    if any(k in name for k in tech_keywords):
        return "技術"
    
    return "其他"


def analyze_entities_ai(content):
    print("正在透過 AI 提取 Entity 與動態分群...")
    prompt = f"""
    請從以下文章中提取重要的實體（Entity），並為每個實體分配一個最適合的主題分類。
    分類請盡量精簡並歸納為 4 到 6 個核心大類（例如：品牌、價格、規格技術、合約方案、其他等）。
    請回傳嚴格的 JSON 格式，包含一個 "entities" 列表，每個項目格式如下：
    {{
        "entities": [
            {{
                "entity": "實體名稱",
                "theme": "該實體所屬的主題分類"
            }}
        ]
    }} 

    文章內容：
    {content}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get('entities', []) 
    except Exception as e:
        print(f"AI 分析失敗: {e}")
        return []


if __name__ == "__main__":
    keyword = input("請輸入關鍵字: ") or "4G 吃到飽"
    search_results = get_serp_data(keyword)

    all_data = []
    flat_rows = []
    total_chars_all = 0  
    total_entities_count = 0  

    # 判斷是否為指定的 4G 吃到飽專案，決定要用「固定規則」還是「AI 動態分群」
    is_default_query = ("4g" in keyword.lower() and "吃到飽" in keyword.lower()) or (keyword == "4G 吃到飽")

    for idx, item in enumerate(search_results):
        content, raw_len = fetch_content(item['link'])
        total_chars_all += raw_len  

        entities = []

        if is_default_query:
            # --- 模式 A：使用原本的 AI 提取實體名稱 + 固定的 classify_by_rules 規則分類 ---
            print("使用固定規則分類模式...")
            prompt_simple = f"""
            請從以下文章中提取重要的實體（Entity）。
            請回傳 JSON 格式，包含一個 "entities" 列表，每個項目格式如下：
            {{
                "entities": [
                    {{"entity": "實體名稱"}}
                ]
            }} 
            文章內容：{content}
            """
            try:
                res = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_simple}],
                    response_format={"type": "json_object"}
                )
                raw_entities = json.loads(res.choices[0].message.content).get('entities', [])
            except Exception as e:
                print(f"AI 提取失敗: {e}")
                raw_entities = []

            for entity_item in raw_entities:
                entity_name = None
                if isinstance(entity_item, dict):
                    entity_name = entity_item.get("entity") or entity_item.get("name")
                elif isinstance(entity_item, str):
                    entity_name = entity_item
                
                if not entity_name or not isinstance(entity_name, str):
                    continue
                
                entity_name = entity_name.strip()
                if not entity_name:
                    continue

                theme = classify_by_rules(entity_name)
                if not theme:
                    continue

                exact_count = content.count(entity_name)
                if exact_count == 0:
                    exact_count = 1

                entity_entry = {
                    "entity": entity_name,
                    "count": exact_count,
                    "theme": theme
                }
                entities.append(entity_entry)
                total_entities_count += 1

                flat_rows.append({
                    "title": item['title'],
                    "url": item['link'],
                    "entity": entity_name,
                    "count": exact_count,
                    "theme": theme
                })
        else:
            # --- 模式 B：使用 AI 直接決定實體與動態 theme 分類 ---
            print("使用 AI 動態分群模式...")
            raw_entities = analyze_entities_ai(content)

            for item_ai in raw_entities:
                entity_name = item_ai.get("entity")
                theme = item_ai.get("theme") or "其他"
                
                if not entity_name or not isinstance(entity_name, str):
                    continue
                
                entity_name = entity_name.strip()
                if not entity_name:
                    continue

                exact_count = content.count(entity_name)
                if exact_count == 0:
                    exact_count = 1

                entity_entry = {
                    "entity": entity_name,
                    "count": exact_count,
                    "theme": theme
                }
                entities.append(entity_entry)
                total_entities_count += 1

                flat_rows.append({
                    "title": item['title'],
                    "url": item['link'],
                    "entity": entity_name,
                    "count": exact_count,
                    "theme": theme
                })

        page_data = {
            "title": item['title'],
            "url": item['link'],
            "entities": entities
        }
        all_data.append(page_data)

    articles_count = len(search_results)
    avg_words = int(total_chars_all / articles_count) if articles_count > 0 else 0

    output_payload = {
        "query": keyword,
        "total_articles": articles_count,
        "total_words": total_chars_all,
        "avg_words_per_article": avg_words,
        "total_entities_extracted": total_entities_count,
        "max_words_limit": MAX_WORDS_LIMIT,
        "data": all_data,
        "articles": all_data,
        "rows": flat_rows
    }

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=4)
    print("分析完成，豐富的中繼資料已存至 results.json")