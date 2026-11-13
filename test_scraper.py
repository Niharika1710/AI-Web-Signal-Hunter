
from crawler.discovery import discover_urls
from crawler.scraper import scrape_page

topic = "WhatsApp automation problems for small businesses"

print("Discovering webpages...\n")

urls = discover_urls(
    topic=topic,
    max_pages=25
)

print(f"\nTesting {len(urls)} discovered URLs...\n")

successful = 0
failed = 0

for index, url in enumerate(urls, start=1):

    print(f"\n[{index}/{len(urls)}] {url}")

    try:
        page = scrape_page(url)

        successful += 1

        print("SUCCESS:", page["title"])
        print("Domain:", page["source_domain"])
        print("Extracted characters:", len(page["content"]))
        print("Preview:", page["content"][:250])

    except Exception as error:

        failed += 1
        print("FAILED:", error)

print("\n========== SCRAPING SUMMARY ==========")
print("Discovered:", len(urls))
print("Successfully scraped:", successful)
print("Failed:", failed)
