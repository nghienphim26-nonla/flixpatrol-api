import asyncio
import json
import time
import random
import string
from playwright.async_api import async_playwright

def generate_uid(length=20):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

async def scrape_flixpatrol():
    target_url = "https://flixpatrol.com/top10/netflix/vietnam/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--ignore-certificate-errors",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        # Ẩn dấu vết tự động hóa
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        flat_results = []
        
        try:
            print("Đang truy cập trang FlixPatrol...")
            # Dùng domcontentloaded thay vì networkidle để không bị timeout
            await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
            
            # Chờ thêm 5 giây để Cloudflare nhả trang và render nội dung bảng
            print("Đang chờ hiển thị dữ liệu...")
            await page.wait_for_timeout(5000)
            
            # Thử tìm thẻ chứa dữ liệu bảng phim
            html_content = await page.content()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            cards = soup.select('div.card')
            
            current_index = 1
            current_timestamp = int(time.time() * 1000)
            timestamp_str = "Mon, 15 Jun 2026 20:36:56 GMT"
            
            for card in cards:
                title_elem = card.select_first('h3')
                if not title_elem:
                    continue
                
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

            print(f"Cào thành công tổng cộng: {len(flat_results)} bộ phim.")

        except Exception as e:
            print(f"Lỗi trong quá trình cào dữ liệu: {e}")
            
        finally:
            # Ghi đè vào file JSON với dữ liệu đã cào được
            with open("flixpatrol_netflix_vn.json", "w", encoding="utf-8") as f:
                json.dump(flat_results, f, ensure_ascii=False, indent=2)
            print("Đã cập nhật file flixpatrol_netflix_vn.json")
            
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_flixpatrol())
