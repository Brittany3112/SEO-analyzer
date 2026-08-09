import json
import os
from dotenv import load_dotenv
from supabase import create_client

# 載入 .env 檔案
load_dotenv()

# 安全地把金鑰抓出來用
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("請先在 .env 中設定 SUPABASE_URL 與 SUPABASE_KEY")

supabase = create_client(url, key)

# 【關鍵防線】上傳前先清空資料庫舊資料，避免垃圾分類累積疊加！
print("正在清除 Supabase 舊有的 SEO 數據...")
try:
    # 刪除 id 不為 0 的所有資料（等同於清空整張表）
    supabase.table("seo_data").delete().neq("id", 0).execute()
    print("舊資料已清空！")
except Exception as e:
    print(f"清空資料庫時發生錯誤（如果表是空的可以忽略）：{e}")

with open("results.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

# 提取元數據
metadata = {
    "query": payload.get("query", "未知"),
    "total_articles": payload.get("total_articles", 0),
    "total_words": payload.get("total_words", 0),
    "avg_words_per_article": payload.get("avg_words_per_article", 0),
    "total_entities_extracted": payload.get("total_entities_extracted", 0)
}}

if isinstance(payload, dict):
    if isinstance(payload.get("rows"), list):
        source_items = payload["rows"]
    elif isinstance(payload.get("data"), list):
        source_items = payload["data"]
    else:
        source_items = []
else:
    source_items = payload

rows_to_insert = []
for item in source_items:
    if isinstance(item, dict) and "entity" in item:
        rows_to_insert.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "entity": item.get("entity"),
            "count": item.get("count"),
            "theme": item.get("theme")
        })
        continue

    title = item.get("title")
    url = item.get("url")
    for entity_item in item.get("entities", []):
        rows_to_insert.append({
            "title": title,
            "url": url,
            "entity": entity_item.get("entity"),
            "count": entity_item.get("count"),
            "theme": entity_item.get("theme")
        })

# 先上傳元數據到 seo_metadata 表
print("正在上傳元數據到 seo_metadata 表...")
try:
    supabase.table("seo_metadata").delete().neq("id", 0).execute()
    supabase.table("seo_metadata").insert([metadata]).execute()
    print("元數據已成功上傳！")
except Exception as e:
    print(f"上傳元數據時發生錯誤：{e}")

# 再上傳實體資料
if rows_to_insert:
    supabase.table("seo_data").insert(rows_to_insert).execute()
    print(f"資料已成功匯入 Supabase！共 {len(rows_to_insert)} 筆")
else:
    print("沒有可匯入的資料。")

print('\a')