
from crawler.discovery import discover_urls
from crawler.scraper import scrape_page

topic = "problems small businesses face with WhatsApp automation"

urls = discover_urls(
    topic=topic,
    keywords=["customer support", "automation"],
    max_pages=35
)

successful = []
failed = []

for index, url in enumerate(urls, start=1):
    print(f"\nTesting {index}/{len(urls)}")
    print(url)

    try:
        page = scrape_page(url)
        successful.append(page)
        print("SUCCESS:", page["title"])

    except Exception as error:
        failed.append({
            "url": url,
            "error": str(error)
        })
        print("FAILED:", error)

print("\n========== RESULTS ==========")
print("Discovered:", len(urls))
print("Successfully scraped:", len(successful))
print("Failed:", len(failed))

print("\nSuccessful domains:")
for domain in sorted({
    page["source_domain"] for page in successful
}):
    print("-", domain)
