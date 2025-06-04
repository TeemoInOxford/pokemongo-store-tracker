import json
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
from opencc import OpenCC
import os
import requests

# 售价映射表（非金币）
idr_price_map = {
    5000: 8.99,
    10000: 9.99,
    15000: 12.99,
    25000: 22.22,
    30500: 25.55,
    41000: 29.99,
    50000: 33.33,
    76000: 55.55,
    101000: 59.99
}

# 金币定价表（只有金币商品用）
coin_price_map = {
    600: 18.99,
    1300: 29.99,
    2700: 54.99,
    5600: 104.99,
    15500: 249.99
}

# 判断金币商品
def is_coin_item(category, name_en):
    return category.startswith("POKECOIN") or "coin" in name_en.lower()

# 获取售价
def get_final_price(idr_price, category, name_en, quantity):
    idr = int(idr_price)
    if is_coin_item(category, name_en):
        price = coin_price_map.get(quantity)
        return f"{price} CNY 人民币" if price else f"{idr_price:.2f} CNY（未定价）"
    else:
        price = idr_price_map.get(idr)
        return f"{price} CNY 人民币" if price else f"{idr_price:.2f} CNY（未定价）"


# 图片保存目录
IMG_DIR = "images"
os.makedirs(IMG_DIR, exist_ok=True)

# 下载图片函数
def download_image(url, filename=None):
    if not filename:
        filename = os.path.basename(url)
    local_path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ Downloaded: {filename}")
            else:
                print(f"❌ Failed: {url}")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
    return local_path

cc = OpenCC('t2s')

def convert_time(ms):
    if not ms:
        return None
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) + timedelta(hours=8)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def extract_key_parts(localization_key):
    raw_key = localization_key.replace("sku.name.", "")
    match = re.match(r"^([a-zA-Z0-9\-_]+)(?:\.(\w+))?$", raw_key)
    if match:
        return match.group(1), match.group(2)
    return raw_key, None

def resolve_name(map_dict, main_key, sub_key):
    val = map_dict.get(main_key, "")
    if isinstance(val, str):
        return val
    elif isinstance(val, dict):
        return val.get(sub_key, "") if sub_key else list(val.values())[0]
    return ""

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lang_data = data.get("zh")
i18n = lang_data["pageProps"].get("_nextI18Next", {}).get("initialI18nStore", {})
name_map_en = i18n.get("en-US", {}).get("common", {}).get("sku", {}).get("name", {})
name_map_zh = i18n.get("zh-TW", {}).get("common", {}).get("sku", {}).get("name", {})

categories = lang_data["pageProps"]["catalog"]["webstoreCategoriesList"]
items_info = []

category_map = {
    "TICKETS": "门票礼盒",
    "BUNDLE": "道具礼盒",
    "LIMITED_TIME": "限时礼盒",
    "ITEMS": "道具",
    "POKECOINS": "宝可币",
    "POKECOIN": "宝可币"
}

def suggest_price(idr, premium=0.15):
    base = 0.00048 * idr + 10
    bundle_price = base * (1 + premium)
    return round(bundle_price) - 0.01 if bundle_price > 10 else round(bundle_price, 2)

for category in categories[1:]:
    raw_cat = category["category"]
    cat_cn = category_map.get(raw_cat, raw_cat)
    cat_name = f"{raw_cat}\n{cat_cn}"
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
        idr_price = int(price[0].get("priceE6")) / 1_000_000
        quantity = price[0].get("quantity", 0)
        selling_price = get_final_price(idr_price, raw_cat, name_en, quantity)


        # 下载主图
        if imageUrl:
            image_filename = f"main_{main_key.lower()}.png"
            download_image(imageUrl, image_filename)
            local_main_image_path = f"{IMG_DIR}/{image_filename}"
        else:
            local_main_image_path = ""

        # 打包道具内容
        bundle_info = []
        icon_ids = set()
        for b in bundle:
            raw_id = b.get("itemId")
            b_main_key, b_sub_key = extract_key_parts(raw_id)
            b_name_en = resolve_name(name_map_en, b_main_key, b_sub_key) or raw_id
            b_name_zh_trad = resolve_name(name_map_zh, b_main_key, b_sub_key)
            b_name_zh_simp = cc.convert(b_name_zh_trad)
            bundle_info.append({
                "itemId": f"{b_name_en}\n{b_name_zh_simp}",
                "rawId": raw_id.lower(),
                "quantity": b.get("quantity")
            })
            icon_ids.add(raw_id.lower())

        # 打包货币内容
        for b in bundle_coin:
            currency_id = b.get("currency").lower()
            bundle_info.append({
                "itemId": b.get("currency") + "\n" + category_map.get(b.get("currency"), b.get("currency")),
                "rawId": currency_id,
                "quantity": b.get("quantity")
            })
            icon_ids.add(currency_id)

        # 下载所有小图
        for rid in icon_ids:
            icon_url = f"https://storage.googleapis.com/platform-webstore-rel-assets/pgo/sku_assets/{rid}.png"
            icon_filename = f"icon_{rid}.png"
            download_image(icon_url, icon_filename)

        items_info.append({
            "category": cat_name,
            "name": full_name,
            "endTimeMs": convert_time(end_time),
            "bundledItems": bundle_info,
            "sellingPrice": f"{selling_price} CNY 人民币",
            "price": price,
            "imageUrl": imageUrl,
            "localImage": local_main_image_path
        })

df = pd.DataFrame(items_info)
df.to_csv("webstore_items_limited.csv", index=False, encoding="utf-8-sig")
df.to_json("webstore_items_limited.json", orient="records", force_ascii=False, indent=2)
print("✅ 导出完成")
