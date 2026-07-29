import time
import random
import string
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from curl_cffi import requests

app = FastAPI(title="FlixPatrol Scraper API")

def generate_uid(length=20):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@app.get("/")
def home():
    return {
        "message": "FlixPatrol API is running!",
        "endpoint": "/scrape"
    }

@app.get("/scrape")
def scrape_flixpatrol():
    target_url = "https://flixpatrol.com/top10/netflix/vietnam/"
    try:
        response = requests.get(target_url, impersonate="chrome", timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Lỗi kết nối trang đích, mã lỗi: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.select('div.card')
        
        flat_results = []
        current_index = 1
        current_timestamp = int(time.time() * 1000)
        timestamp_str = "Mon, 15 Jun 2026 20:36:56 GMT" # Hoặc lấy thời gian thực nếu muốn
        
        for card in cards:
            title_elem = card.select_first('h3')
            if not title_elem:
                continue
            
            table_title = title_elem.get_text(strip=True)
            rows = card.select('tbody.tabular-nums tr')
            
            for row in rows:
                cols = row.select('td')
                if len(cols) >= 3:
                    rank_str = cols[0].get_text(strip=True)
                    title_tag = cols[2].select_first('a')
                    
                    name = title_tag.get_text(strip=True) if title_tag else cols[2].get_text(strip=True)
                    href = title_tag['href'] if title_tag and title_tag.has_attr('href') else ""
                    full_link = f"https://flixpatrol.com{href}" if href.startswith('/') else href
                    
                    item = {
                        "stt": rank_str,
                        "url_uid": 1,
                        "index": current_index,
                        "tenphim_link": full_link,
                        "url": target_url,
                        "timestamp": current_timestamp,
                        "uid": generate_uid(),
                        "tenphim": name,
                        "timestampString": timestamp_str
                    }
                    flat_results.append(item)
                    current_index += 1

        # Trả về trực tiếp định dạng mảng JSON giống yêu cầu
        return flat_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
