from crawler.discovery import discover_urls

urls = discover_urls(
    topic="WhatsApp automation problems for small businesses",
    keywords=["customer support", "automation", "business problems"],
    max_pages=3
)

print("\nURLs discovered:", len(urls))

for index, url in enumerate(urls, start=1):
    print(index, url)