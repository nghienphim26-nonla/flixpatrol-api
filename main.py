from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from curl_cffi import requests

app = FastAPI(title="FlixPatrol Scraper API")

@app.get("/scrape")
def scrape_flixpatrol():
    url = "https://flixpatrol.com/top10/netflix/vietnam/"
    try:
        # Dùng curl_cffi để vượt qua Cloudflare
        response = requests.get(url, impersonate="chrome", timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Lỗi kết nối trang đích: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = {
            "movies": [],
            "tv_shows": []
        }

        cards = soup.select('.card')
        for card in cards:
            title_elem = card.select_first('.card-title')
            if not title_elem:
                continue
            
            table_title = title_elem.get_text(strip=True)
            rows = card.select('tbody tr')
            
            table_data = []
            for row in rows:
                cols = row.select('td')
                if len(cols) >= 3:
                    rank = cols[0].get_text(strip=True)
                    name = cols[2].get_text(strip=True)
                    metric = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                    
                    table_data.append({
                        "rank": rank,
                        "title": name,
                        "metric": metric
                    })
            
            if "Movies" in table_title:
                result["movies"] = table_data
            elif "TV Shows" in table_title:
                result["tv_shows"] = table_data

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))