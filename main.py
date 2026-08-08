import requests
from bs4 import BeautifulSoup
import json
import openai

# 設定您的 API Key
SERPER_API_KEY = "your_serper_api_key_here"
# 設定您的 OpenAI API Key
openai.api_key = "your_openai_api_key_here"

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
        # 只拿掉 script 和 style，保留文字
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True)[:2000]  # 先拿前 2000 字，避免 AI 處理太慢
    except Exception as e:
        return f"抓取失敗: {e}"


def analyze_entities(content):
    print("正在透過 AI 提取 Entity 與分群...")
    prompt = f"""
    請分析以下關於『4G 吃到飽』的文章內容，提取出重要的實體（Entity），包括：
    1. 品牌/電信商（如：中華電信、遠傳）
    2. 資費/價格（如：499元、199元）
    3. 技術/服務術語（如：5G、不限速、熱點分享）

    請回傳 JSON 格式，包含一個列表，每個項目要有：
    "entity": 實體名稱,
    "count": 在文中提到的預估次數,
    "theme": 主題分類（品牌、價格、或技術）

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
        return result.get('entities', [])  # 假設 AI 回傳的 key 是 entities
    except Exception as e:
        print(f"AI 分析失敗: {e}")
        return []

# 執行測試
if __name__ == "__main__":
    keyword = input("請輸入關鍵字: ") or "4G吃到飽"
    search_results = get_serp_data(keyword)

    all_data = []
    for idx, item in enumerate(search_results):
        content = fetch_content(item['link'])
        entities = analyze_entities(content)

        # 整理成最終要存入資料庫的格式
        page_data = {
            "title": item['title'],
            "url": item['link'],
            "entities": entities
        }
        all_data.append(page_data)
        print(f"完成分析第 {idx + 1} 篇文章，提取到 {len(entities)} 個實體。")

    # 將結果存成 JSON 檔案，方便下一步匯入 Supabase
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("所有分析已完成，結果已存至 results.json")