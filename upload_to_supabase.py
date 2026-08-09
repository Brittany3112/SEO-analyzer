import json
from supabase import create_client
import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 安全地把金鑰抓出來用
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
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
    data = json.load(f)

rows_to_insert = []
for item in data:
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

# 一次性把全部打包送出
response = supabase.table("seo_data").insert(rows_to_insert).execute()

print("資料已成功匯入 Supabase！")
print('\a')