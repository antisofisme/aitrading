#!/usr/bin/env python3
"""
Analyze MQL5 Calendar Data in Detail
Show exact dates, events, and data quality
"""
from bs4 import BeautifulSoup
import re
from datetime import datetime
from collections import defaultdict

# Read saved HTML
with open('/app/logs/mql5_simple.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')
text = soup.get_text()

# Extract event lines with detailed regex
lines = text.split('\n')
event_pattern = r'(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2}),\s+([A-Z]{3}),\s+([^,]+)'

events = []
for line in lines:
    match = re.search(event_pattern, line)
    if match:
        date, time, currency, event_name = match.groups()

        # Extract values
        actual = re.search(r'Actual:\s*([^,]+)', line)
        forecast = re.search(r'Forecast:\s*([^,]+)', line)
        previous = re.search(r'Previous:\s*([^,]+)', line)

        events.append({
            'date': date,
            'time': time,
            'currency': currency,
            'event': event_name.strip(),
            'actual': actual.group(1).strip() if actual else None,
            'forecast': forecast.group(1).strip() if forecast else None,
            'previous': previous.group(1).strip() if previous else None,
            'raw_line': line.strip()
        })

print("=" * 100)
print("📊 DETAIL LENGKAP - DATA CALENDAR MQL5")
print("=" * 100)
print()

# Get unique dates
unique_dates = sorted(set(e['date'] for e in events))

print(f"🗓️  INFORMASI TANGGAL:")
print(f"   Tanggal Pertama: {unique_dates[0]}")
print(f"   Tanggal Terakhir: {unique_dates[-1]}")
print(f"   Total Hari: {len(unique_dates)} hari")
print(f"   Total Events: {len(events)} events")
print()

# Group by date
by_date = defaultdict(list)
for event in events:
    by_date[event['date']].append(event)

print("=" * 100)
print("📅 DETAIL PER TANGGAL (Showing ALL dates)")
print("=" * 100)
print()

for date in unique_dates:
    events_on_date = by_date[date]

    # Parse date
    try:
        date_obj = datetime.strptime(date, '%Y.%m.%d')
        day_name = date_obj.strftime('%A')
        formatted = date_obj.strftime('%d %B %Y')
    except:
        day_name = "Unknown"
        formatted = date

    print(f"📆 {formatted} ({day_name})")
    print(f"   Total Events: {len(events_on_date)}")
    print("-" * 100)

    # Show ALL events for this date
    for i, evt in enumerate(events_on_date, 1):
        print(f"\n   {i}. [{evt['time']}] {evt['currency']} - {evt['event']}")

        # Show values in detail
        if evt['forecast'] or evt['previous'] or evt['actual']:
            parts = []
            if evt['forecast']:
                parts.append(f"Forecast: {evt['forecast']}")
            if evt['previous']:
                parts.append(f"Previous: {evt['previous']}")
            if evt['actual']:
                parts.append(f"Actual: {evt['actual']}")
            print(f"      {' | '.join(parts)}")

    print()

print("=" * 100)
print("💱 BREAKDOWN BY CURRENCY")
print("=" * 100)
print()

by_currency = defaultdict(list)
for event in events:
    by_currency[event['currency']].append(event)

for currency in sorted(by_currency.keys()):
    curr_events = by_currency[currency]
    print(f"{currency}: {len(curr_events)} events")

    # Show sample events for this currency
    print(f"   Sample events:")
    for evt in curr_events[:3]:
        print(f"   - {evt['date']} {evt['time']}: {evt['event'][:50]}")
    if len(curr_events) > 3:
        print(f"   ... and {len(curr_events) - 3} more events")
    print()

print("=" * 100)
print("📈 TOP 20 EVENT TYPES")
print("=" * 100)
print()

event_types = defaultdict(int)
for event in events:
    event_types[event['event']] += 1

top_events = sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:20]
for i, (event_name, count) in enumerate(top_events, 1):
    print(f"{i:2d}. {event_name:<70} ({count}x)")

print()

print("=" * 100)
print("✅ DATA QUALITY ANALYSIS")
print("=" * 100)
print()

total = len(events)
with_forecast = sum(1 for e in events if e['forecast'])
with_previous = sum(1 for e in events if e['previous'])
with_actual = sum(1 for e in events if e['actual'])
complete = sum(1 for e in events if e['forecast'] and e['previous'] and e['actual'])

print(f"Total Events:           {total}")
print(f"With Forecast:          {with_forecast:4d} ({with_forecast/total*100:.1f}%)")
print(f"With Previous:          {with_previous:4d} ({with_previous/total*100:.1f}%)")
print(f"With Actual:            {with_actual:4d} ({with_actual/total*100:.1f}%)")
print(f"Complete (F+P+A):       {complete:4d} ({complete/total*100:.1f}%)")
print()

print("=" * 100)
print("📊 KESIMPULAN")
print("=" * 100)
print()
print(f"✅ Berhasil extract {total} economic events")
print(f"✅ Dari tanggal {unique_dates[0]} sampai {unique_dates[-1]}")
print(f"✅ Mencakup {len(unique_dates)} hari trading")
print(f"✅ Meliputi {len(by_currency)} mata uang berbeda")
print(f"✅ {len(event_types)} jenis event ekonomi unik")
print(f"✅ Data completeness: {complete/total*100:.1f}% events punya F+P+A")
print()
