import json
from supabase import create_client

# 在 Supabase 後台的 Project Settings -> API 找這兩個值
url = "https://kmtplcbcgtyjzupseclr.supabase.co"
key = "your_supabase_secret_api_key_here"
supabase = create_client(url, key)

with open("results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for page in data:
    for entity in page['entities']:
        row = {
            "title": page['title'],
            "url": page['url'],
            "entity": entity['entity'],
            "count": entity['count'],
            "theme": entity['theme']
        }
        supabase.table("seo_data").insert(row).execute()

print("資料已成功匯入 Supabase！")