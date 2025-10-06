#!/usr/bin/env python3
"""
Test MQL5 with aiohttp + BeautifulSoup (No Playwright!)
Bypass bot detection by using simple HTTP requests
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime


async def test_mql5_simple():
    """Test MQL5 with simple HTTP request"""
    print("=" * 80)
    print("🧪 MQL5 TEST - aiohttp + BeautifulSoup")
    print("=" * 80)
    print()

    url = "https://www.mql5.com/en/economic-calendar"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',  # Removed 'br' (brotli)
        'Connection': 'keep-alive',
    }

    try:
        print("1️⃣  Fetching MQL5 calendar with aiohttp...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"   Status: {response.status}")

                if response.status == 200:
                    print("   ✅ SUCCESS! No bot detection!")
                    html = await response.text()

                    print(f"   📄 HTML size: {len(html)} bytes")
                    print()

                    # Parse with BeautifulSoup
                    print("2️⃣  Parsing HTML with BeautifulSoup...")
                    soup = BeautifulSoup(html, 'lxml')

                    # Get page title
                    title = soup.title.string if soup.title else "No title"
                    print(f"   Page title: {title}")
                    print()

                    # Look for calendar table
                    print("3️⃣  Looking for calendar content...")

                    # Find tables
                    tables = soup.find_all('table')
                    print(f"   Tables found: {len(tables)}")

                    # Find calendar-specific elements
                    calendar_elements = soup.find_all(class_=lambda x: x and 'calendar' in x.lower())
                    print(f"   Calendar elements: {len(calendar_elements)}")

                    # Find event rows
                    event_rows = soup.find_all('tr', class_=lambda x: x and ('event' in x.lower() or 'row' in x.lower()))
                    print(f"   Event-like rows: {len(event_rows)}")
                    print()

                    # Show first table structure
                    if tables:
                        print("4️⃣  First table structure:")
                        first_table = str(tables[0])[:1000]
                        print(first_table)
                        print()

                    # Look for common economic calendar indicators
                    print("5️⃣  Searching for economic event keywords...")
                    keywords = ['GDP', 'NFP', 'Employment', 'Inflation', 'PMI', 'CPI', 'Fed', 'ECB']
                    text = soup.get_text()

                    for keyword in keywords:
                        count = text.count(keyword)
                        if count > 0:
                            print(f"   ✅ '{keyword}': {count} occurrences")
                    print()

                    # Save HTML for manual inspection
                    with open('/app/logs/mql5_simple.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("6️⃣  Saved HTML to: /app/logs/mql5_simple.html")
                    print()

                    print("=" * 80)
                    print("✅ MQL5 ACCESSIBLE!")
                    print("=" * 80)
                    print()
                    print("Next: Parse actual events from HTML")

                else:
                    print(f"   ❌ HTTP {response.status}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_mql5_simple())
