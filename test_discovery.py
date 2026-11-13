
from crawler.discovery import discover_urls
from urllib.parse import urlparse

topic = "problems small businesses face with WhatsApp automation"

print("Discovering webpages...")

try:
    urls = discover_urls(
        topic=topic,
        keywords=["customer support", "automation"],
        max_pages=25
    )

    print(f"\nFound {len(urls)} URLs:\n")

    for index, url in enumerate(urls, start=1):
        print(f"{index}. {url}")

    domains = {
        urlparse(url).netloc.lower().removeprefix("www.")
        for url in urls
    }

    print("\nUnique domains:", len(domains))

    for domain in sorted(domains):
        print("-", domain)

except Exception as error:
    print("Discovery failed:", error)
