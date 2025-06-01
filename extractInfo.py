import json
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
from opencc import OpenCC

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

for category in categories[1:]:
    cat_name = category["category"]
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

        # 打包货币内容
        bundle_coin_info = [
            {"itemId": b.get("currency"), "quantity": b.get("quantity")}
            for b in bundle_coin
        ]

        # 打包道具内容
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
import json
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
from opencc import OpenCC

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

for category in categories[1:]:
    cat_name = category["category"]
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

        # 打包货币内容
        bundle_coin_info = [
            {"itemId": b.get("currency"), "quantity": b.get("quantity")}
            for b in bundle_coin
        ]

        # 打包道具内容
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
