import json
from datetime import datetime, timezone, timedelta

# 把毫秒时间戳转换为 UTC+8（北京时间）
def convert_time(ms):
    if not ms:
        return None
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) + timedelta(hours=8)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 读取 JSON
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 选择语言（en / zh）
lang_data = data.get("en")  # or data["zh"] if你想看繁体中文

# 路径：catalog -> webstoreCategoriesList
categories = lang_data["pageProps"]["catalog"]["webstoreCategoriesList"]

# 收集目标信息
items_info = []

for category in categories[1:]:
    cat_name = category["category"]
    for item in category.get("itemsList", []):
        imageUrl = item.get("imageUrl")
        name = item.get("localizationNameKey", "")
        end_time = item.get("webstoreLimitInfo", {}).get("endTimeMs")
        bundle_coin = item.get("bundledCurrencyList", [])
        bundle = item.get("bundledItemList", [])
        price = item.get("priceList")

        bundle_coin_info = [
            {
                "itemId": b.get("currency"),
                "quantity": b.get("quantity")
            }
            for b in bundle_coin
        ]

        bundle_info = [
            {
                "itemId": b.get("itemId"),
                "quantity": b.get("quantity")
            }
            for b in bundle
        ]

        bundle_info += bundle_coin_info

        items_info.append({
            "category": cat_name,
            "name": name,
            "endTimeMs": convert_time(end_time),
            "bundledItems": bundle_info,
            "price": price,
            "imageUrl": imageUrl
        })

# 输出或保存
import pandas as pd
df = pd.DataFrame(items_info)
df.to_csv("webstore_items_limited.csv", index=False, encoding="utf-8-sig")
df.to_json("webstore_items_limited.json", orient="records", force_ascii=False, indent=2)
print(df.head())
