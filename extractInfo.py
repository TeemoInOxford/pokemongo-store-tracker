import json
from datetime import datetime, timezone, timedelta
import pandas as pd

# 转北京时间
def convert_time(ms):
    if not ms:
        return None
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) + timedelta(hours=8)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 加载 JSON
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lang_data = data.get("en")

# 加载中英文映射
i18n = lang_data["pageProps"].get("_nextI18Next", {}).get("initialI18nStore", {})
name_map_en = i18n.get("en-US", {}).get("common", {}).get("sku", {}).get("name", {})
name_map_zh = i18n.get("zh-TW", {}).get("common", {}).get("sku", {}).get("name", {})

# 抓商品分类
categories = lang_data["pageProps"]["catalog"]["webstoreCategoriesList"]
items_info = []

for category in categories[1:]:
    cat_name = category["category"]
    for item in category.get("itemsList", []):
        imageUrl = item.get("imageUrl")
        key = item.get("localizationNameKey", "")
        name_en = name_map_en.get(key, key)
        name_zh = name_map_zh.get(key, "")
        full_name = f"{name_en}\n{name_zh}"

        end_time = item.get("webstoreLimitInfo", {}).get("endTimeMs")
        bundle_coin = item.get("bundledCurrencyList", [])
        bundle = item.get("bundledItemList", [])
        price = item.get("priceList")

        bundle_coin_info = [
            {"itemId": b.get("currency"), "quantity": b.get("quantity")}
            for b in bundle_coin
        ]

        bundle_info = [
            {"itemId": b.get("itemId"), "quantity": b.get("quantity")}
            for b in bundle
        ]

        bundle_info += bundle_coin_info

        items_info.append({
            "category": cat_name,
            "name": full_name,
            "endTimeMs": convert_time(end_time),
            "bundledItems": bundle_info,
            "price": price,
            "imageUrl": imageUrl
        })

# 导出为 CSV + JSON
df = pd.DataFrame(items_info)
df.to_csv("webstore_items_limited.csv", index=False, encoding="utf-8-sig")
df.to_json("webstore_items_limited.json", orient="records", force_ascii=False, indent=2)
print(df.head())
