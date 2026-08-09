import requests
from bs4 import BeautifulSoup
import json
import openai
import os
from dotenv import load_dotenv

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

        # 這裡可以決定要拿幾字（如果資費方案都在前段，2000字可能夠；但如果是長篇評比，可能需要 4000-5000 字）
        return raw_text[:6000]
    except Exception as e:
        return f"抓取失敗: {e}"


def classify_by_rules(entity_name):
    """規則優先：利用關鍵字對照表強制歸類核心項目"""
    name = entity_name.lower()

    brand_keywords = ["中華", "遠傳", "台灣大哥大", "亞太", "台灣之星"]
    price_keywords = ["元", "$", "月租", "價格", "費率", "優惠價"]
    tech_keywords = ["5g", "4g", "不限速", "限速", "熱點", "volte", "網速", "吃到飽"]
    contract_keywords = ["個月", "年", "綁約", "期限", "合約"] # 統一歸到「合約」

    if any(k in name for k in brand_keywords):
        return "品牌"
    if any(k in name for k in price_keywords):
        return "價格"
    if any(k in name for k in tech_keywords):
        return "技術"
    if any(k in name for k in contract_keywords):
        return "合約" # 確保這裡回傳的是「合約」，絕對不是「合約時間」

    return None

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

# 執行測試
if __name__ == "__main__":
    keyword = input("請輸入關鍵字: ") or "4G 吃到飽"
    search_results = get_serp_data(keyword)

    all_data = []
    for idx, item in enumerate(search_results):
        print(item)
        content = fetch_content(item['link'])
        raw_entities = analyze_entities(content)
        print(raw_entities)

        entities = []
        for entity_item in raw_entities:
            entity_name = entity_item.get("entity", "")
            ai_suggested_theme = entity_item.get("suggested_theme", "技術")

            if not entity_name:
                continue

            # 1. 優先使用規則分類
            theme = classify_by_rules(entity_name)

            # 2. 如果規則認不出來，用 AI 建議
            if not theme:
                theme = "技術"

            # 4. 執行精確計數
            exact_count = content.count(entity_name)
            if exact_count == 0:
                exact_count = 1

            entities.append({
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
        print(f"完成分析第 {idx + 1} 篇文章，精算後有效實體數: {len(entities)}")

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("分析完成，資料已存至 results.json")