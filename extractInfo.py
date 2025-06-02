import json
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
from opencc import OpenCC
import os
import requests

# 图片保存目录
IMG_DIR = "images"
os.makedirs(IMG_DIR, exist_ok=True)

# 下载图片函数
def download_image(url):
    filename = os.path.basename(url)
    local_path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(local_path):  # 避免重复下载
        try:
            response = requests.get(url, timeout=10)
            with open(local_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"❌ Failed to download image: {url} - {e}")
    return local_path
    
cc = OpenCC('t2s')  # 繁体转简体

# 把毫秒时间戳转为北京时间字符串
def convert_time(ms):
    if not ms:
        return None
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) + timedelta(hours=8)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 从 localization key 提取主 key 和可选子 key
def extract_key_parts(localization_key):
    raw_key = localization_key.replace("sku.name.", "")
    match = re.match(r"^([a-zA-Z0-9\-_]+)(?:\.(\w+))?$", raw_key)
    if match:
        return match.group(1), match.group(2)
    return raw_key, None

# 从映射中解析英文或中文名（支持嵌套结构）
def resolve_name(map_dict, main_key, sub_key):
    val = map_dict.get(main_key, "")
    if isinstance(val, str):
        return val
    elif isinstance(val, dict):
        return val.get(sub_key, "") if sub_key else list(val.values())[0]
    return ""

# 加载 JSON 数据
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lang_data = data.get("zh")

# 加载国际化字符串映射
i18n = lang_data["pageProps"].get("_nextI18Next", {}).get("initialI18nStore", {})
name_map_en = i18n.get("en-US", {}).get("common", {}).get("sku", {}).get("name", {})
name_map_zh = i18n.get("zh-TW", {}).get("common", {}).get("sku", {}).get("name", {})

# 抓商品分类列表
categories = lang_data["pageProps"]["catalog"]["webstoreCategoriesList"]
items_info = []

# 中英文分类映射
category_map = {
    "TICKETS": "门票礼盒",
    "BUNDLE": "道具礼盒",
    "LIMITED_TIME": "限时礼盒",
    "ITEMS": "道具",
    "POKECOINS": "宝可币",
    "POKECOIN": "宝可币"
}

# 设计售价公式
def suggest_price(idr, premium=0.15):
    base = 0.00048 * idr + 10
    bundle_price = base * (1 + premium)
    return round(bundle_price) - 0.01 if bundle_price > 10 else round(bundle_price, 2)


# 替换原来的 for category in categories[1:]:
for category in categories[1:]:
    raw_cat = category["category"]
    cat_cn = category_map.get(raw_cat, raw_cat)  # 没匹配上就显示英文
    cat_name = f"{raw_cat}\n{cat_cn}"  # 中英文一行一行展示
    for item in category.get("itemsList", []):
        imageUrl = item.get("imageUrl")
        localization_key = item.get("localizationNameKey", "")
        main_key, sub_key = extract_key_parts(localization_key)

        name_en = resolve_name(name_map_en, main_key, sub_key) or main_key
        name_zh_trad = resolve_name(name_map_zh, main_key, sub_key)
        name_zh_simp = cc.convert(name_zh_trad)
        full_name = f"{name_en}\n{name_zh_simp}"

        end_time = item.get("webstoreLimitInfo", {}).get("endTimeMs")
        bundle_coin = item.get("bundledCurrencyList", [])
        bundle = item.get("bundledItemList", [])
        price = item.get("priceList")


        idr_price_micros = int(price[0]["priceE6"])
            idr_price = idr_price_micros / 1_000_000
            selling_price = calc_price_rmb(idr_price)
        
        # 打包货币内容
        bundle_coin_info = [
            {"itemId": b.get("currency") + "\n" + category_map.get(b.get("currency"),b.get("currency")), "quantity": b.get("quantity")}
            for b in bundle_coin
        ]

        # 打包道具内容
        bundle_info = []
        for b in bundle:
            raw_id = b.get("itemId")
            b_main_key, b_sub_key = extract_key_parts(raw_id)
            b_name_en = resolve_name(name_map_en, b_main_key, b_sub_key) or raw_id
            b_name_zh_trad = resolve_name(name_map_zh, b_main_key, b_sub_key)
            b_name_zh_simp = cc.convert(b_name_zh_trad)
            bundle_info.append({
                "itemId": f"{b_name_en}\n{b_name_zh_simp}",
                "quantity": b.get("quantity")
            })

        bundle_info += bundle_coin_info

        items_info.append({
            "category": cat_name,
            "name": full_name,
            "endTimeMs": convert_time(end_time),
            "bundledItems": bundle_info,
            "sellingPrice": selling_price,
            "price": price,
            "imageUrl": imageUrl
        })

# 导出为 CSV + JSON
df = pd.DataFrame(items_info)
df.to_csv("webstore_items_limited.csv", index=False, encoding="utf-8-sig")
df.to_json("webstore_items_limited.json", orient="records", force_ascii=False, indent=2)
print(df.head())
