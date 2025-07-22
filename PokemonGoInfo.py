import os
import re
import json
import requests
from datetime import datetime
    
headers = {
    'User-Agent': 'Mozilla/5.0'
}

# 从 GitHub Secrets 或环境变量读取代理设置
def get_proxies():
    user = os.getenv("PROXY_USER")
    pwd = os.getenv("PROXY_PASS")
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")

    if not all([user, pwd, host, port]):
        raise Exception("❌ 缺少代理环境变量")

    proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    print(f"🛰️ 当前使用代理地址: {host}:{port}")
    return {
        "http": proxy_url,
        "https": proxy_url
    }

# 从页面源码中提取 buildId（来自 /_next/static/.../_buildManifest.js）
def get_build_id(proxies):
    url = "https://store.pokemongo.com/"
    print(f"🔍 正在访问页面获取 buildId: {url}")
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=10)

    print(f"📄 页面状态码: {resp.status_code}")
    if resp.status_code != 200:
        raise Exception(f"❌ 页面获取失败 status={resp.status_code}")

    match = re.search(r'/_next/static/([a-zA-Z0-9\-_]+)/_ssgManifest\.js', resp.text)
    if match:
        build_id = match.group(1)
        print(f"✅ 成功提取 buildId: {build_id}")
        with open("build_id.json", "w", encoding="utf-8") as f:
            json.dump({
                "buildId": build_id,
                "timestamp": datetime.now().astimezone().isoformat()
            }, f, ensure_ascii=False, indent=2)
        print("📄 已写入 build_id.json")
        return build_id
    else:
        raise Exception("❌ 无法在 HTML 中找到 buildId")

# 主爬虫逻辑
def crawl():
    proxies = get_proxies()
    build_id = get_build_id(proxies)

    base_url = f"https://store.pokemongo.com/_next/data/{build_id}"
    urls = {
        "en": f"{base_url}/en.json",
        "zh": f"{base_url}/zh-Hant.json"
    }

    data = {}
    for lang, url in urls.items():
        print(f"🌐 抓取 {lang} 数据: {url}")
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        print(f"➡️ 状态码: {resp.status_code}")
        if resp.status_code == 200:
            data[lang] = resp.json()
        else:
            raise Exception(f"❌ 请求失败: {url} - status: {resp.status_code}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ 数据已写入 data.json")

if __name__ == "__main__":
    crawl()
