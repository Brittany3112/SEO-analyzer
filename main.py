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
# 設定您的 OpenAI API Key
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

        # 這裡可以決定要拿幾字
        return raw_text[:MAX_WORDS_LIMIT], len(raw_text) # 同時回傳截取內容與總字數
    except Exception as e:
        return f"抓取失敗: {e}", 0


def classify_by_rules(entity_name):
    if isinstance(entity_name, dict):
        entity_name = entity_name.get("entity") or entity_name.get("name") or ""
    if not isinstance(entity_name, str):
        entity_name = str(entity_name or "")
    name = entity_name.lower()

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

    # 依序進行精細判斷
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

    # 剩下的全部歸入「其他」（包含串流、家電、外送等）
    return "其他"

def analyze_entities(content):
    print("正在透過 AI 提取 Entity 與分群...")
    prompt = f"""
    請從以下文章中提取重要的實體（Entity）。
    請回傳 JSON 格式，包含一個 "entities" 列表，每個項目格式如下：
    {{
        "entity": "實體名稱",
        "suggested_theme": "分類（品牌、價格、合約、或技術）"
    }} 

    文章內容：
    {content}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # 使用 mini 版本速度快且便宜
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        # 解析回傳的 JSON
        result = json.loads(response.choices[0].message.content)
        return result.get('entities', [])  # 這邊回傳的會是 [{"entity": "...", "suggested_theme": "..."}, ...]
    except Exception as e:
        print(f"AI 分析失敗: {e}")
        return []

if __name__ == "__main__":
    keyword = input("請輸入關鍵字: ") or "4G 吃到飽"
    search_results = get_serp_data(keyword)

    all_data = []
    flat_rows = []
    total_chars_all = 0  # 累積總字數
    total_entities_count = 0  # 累積萃取出的實體總數

    for idx, item in enumerate(search_results):
        content, raw_len = fetch_content(item['link'])
        total_chars_all += raw_len  # 把這篇的字數加進總和

        raw_entities = analyze_entities(content)

        entities = []
        for entity_item in raw_entities:
            if isinstance(entity_item, dict):
                entity_name = entity_item.get("entity") or entity_item.get("name") or ""
            else:
                entity_name = entity_item

            if not isinstance(entity_name, str) or not entity_name.strip():
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
            total_entities_count += 1  # 實體數加 1

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

    # 計算平均每篇文章字數
    articles_count = len(search_results)
    avg_words = int(total_chars_all / articles_count) if articles_count > 0 else 0

    # 升級版的豐富中繼資料
    output_payload = {
        "query": keyword,
        "total_articles": articles_count,
        "total_words": total_chars_all,
        "avg_words_per_article": avg_words,
        "total_entities_extracted": total_entities_count,
        "data": all_data,
        "articles": all_data,
        "rows": flat_rows
    }

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=4)
    print("分析完成，豐富的中繼資料已存至 results.json")