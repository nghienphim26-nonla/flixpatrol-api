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
                "--start-maximized"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="vi-VN"
        )
        
        # Xóa dấu vết bot
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en-US', 'en'] });
        """)
        
        page = await context.new_page()
        flat_results = []
        
        try:
            print("Đang truy cập và chờ vượt qua Cloudflare...")
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            # Giả lập hành vi di chuyển chuột và cuộn trang để kích hoạt Cloudflare cho qua
            await page.mouse.move(100, 100)
            await page.wait_for_timeout(3000)
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(4000)
            
            # Lấy nội dung HTML sau khi đã tương tác
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

            print(f"Số lượng phim cào được: {len(flat_results)}")

        except Exception as e:
            print(f"Lỗi: {e}")
            
        finally:
            with open("flixpatrol_netflix_vn.json", "w", encoding="utf-8") as f:
                json.dump(flat_results, f, ensure_ascii=False, indent=2)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_flixpatrol())
