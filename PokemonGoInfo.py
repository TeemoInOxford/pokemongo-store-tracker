import requests
import json

headers = {'User-Agent': 'Mozilla/5.0'}

def get_build_id():
    url = "https://store.pokemongo.com/buildId"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.text.strip().strip('"')
    else:
        raise Exception("Failed to fetch build ID")

def crawl():
    build_id = get_build_id()
    print(f"Current build ID: {build_id}")
    base_url = f"https://store.pokemongo.com/_next/data/{build_id}"
    urls = {
        "en": f"{base_url}/en-US.json",
        "zh": f"{base_url}/zh-TW.json"
    }

    data = {}
    for lang, url in urls.items():
        print(f"Fetching {lang}: {url}")
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data[lang] = resp.json()
        else:
            raise Exception(f"Fetch failed: {url} - Status: {resp.status_code}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    crawl()
