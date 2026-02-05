#!/usr/bin/env python3
"""
Simple web crawler for extracting article URLs and titles
"""
import json
import sys
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import re
import socket

def fetch_html(url):
    """Fetch HTML content from URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        req = Request(url, headers=headers)
        socket.setdefaulttimeout(15)
        with urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError, socket.timeout) as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}", file=sys.stderr)
        return None

def extract_anthropic_news(html):
    """Extract articles from Anthropic news page"""
    articles = []
    # Look for article links in the news page
    pattern = r'href="(/news/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
    matches = re.finditer(pattern, html, re.DOTALL)
    for match in matches[:5]:
        url = f"https://anthropic.com{match.group(1)}"
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        articles.append({'url': url, 'title': title})
    return articles

def extract_openai_news(html):
    """Extract articles from OpenAI news page"""
    articles = []
    pattern = r'href="(/index/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
    matches = re.finditer(pattern, html, re.DOTALL)
    for match in matches[:5]:
        url = f"https://openai.com{match.group(1)}"
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        articles.append({'url': url, 'title': title})
    return articles

def extract_github_blog(html):
    """Extract articles from GitHub blog"""
    articles = []
    pattern = r'href="(https://github\.blog/[^"]+)"[^>]*>\s*<h3[^>]*>(.*?)</h3>'
    matches = re.finditer(pattern, html, re.DOTALL)
    for match in matches[:5]:
        url = match.group(1).split('#')[0].split('?')[0]
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if url not in [a['url'] for a in articles]:
            articles.append({'url': url, 'title': title})
    return articles

def extract_github_releases(html):
    """Extract releases from GitHub releases page"""
    articles = []
    pattern = r'href="(/anthropics/claude-code/releases/tag/[^"]+)"'
    matches = re.finditer(pattern, html)
    for match in list(matches)[:5]:
        url = f"https://github.com{match.group(1)}"
        tag = match.group(1).split('/')[-1]
        articles.append({'url': url, 'title': f'Claude Code {tag}'})
    return articles

def extract_techcrunch(html):
    """Extract articles from TechCrunch"""
    articles = []
    pattern = r'href="(https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[^"]+)"[^>]*>.*?<h2[^>]*>(.*?)</h2>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = match.group(1).split('?')[0]
        if url not in seen:
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            articles.append({'url': url, 'title': title})
            if len(articles) >= 5:
                break
    return articles

def extract_venturebeat(html):
    """Extract articles from VentureBeat"""
    articles = []
    pattern = r'href="(https://venturebeat\.com/[^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = match.group(1).split('?')[0].split('#')[0]
        if url not in seen and '/ai/' in url:
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            articles.append({'url': url, 'title': title})
            if len(articles) >= 5:
                break
    return articles

def extract_deepmind_blog(html):
    """Extract articles from DeepMind blog"""
    articles = []
    pattern = r'href="(https://deepmind\.google/blog/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = match.group(1).split('?')[0].split('#')[0]
        if url not in seen:
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            articles.append({'url': url, 'title': title})
            if len(articles) >= 5:
                break
    return articles

def extract_suno_blog(html):
    """Extract articles from Suno blog"""
    articles = []
    # Suno blog uses about.suno.com domain
    pattern = r'href="((?:https://(?:about\.)?suno\.(?:ai|com)/blog/|/blog/)[^"]+)"'
    matches = re.finditer(pattern, html)
    seen = set()
    for match in matches:
        url = match.group(1)
        if url.startswith('/'):
            url = f"https://about.suno.com{url}"
        elif 'suno.ai' in url:
            url = url.replace('suno.ai', 'about.suno.com')
        url = url.split('?')[0].split('#')[0]
        if url not in seen and url != 'https://about.suno.com/blog':
            seen.add(url)
            articles.append({'url': url, 'title': url.split('/')[-1].replace('-', ' ').title()})
            if len(articles) >= 5:
                break
    return articles

def extract_domoai_blog(html):
    """Extract articles from DomoAI blog"""
    articles = []
    pattern = r'href="(/blog/[^"]+)"[^>]*>.*?<h[23][^>]*>(.*?)</h[23]>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = f"https://domoai.app{match.group(1)}"
        url = url.split('?')[0].split('#')[0]
        if url not in seen and url != 'https://domoai.app/blog':
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if title:
                articles.append({'url': url, 'title': title})
                if len(articles) >= 5:
                    break
    return articles

def extract_google_cloud_blog(html):
    """Extract articles from Google Cloud blog"""
    articles = []
    pattern = r'href="(/blog/products/ai-machine-learning/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = f"https://cloud.google.com{match.group(1)}"
        url = url.split('?')[0].split('#')[0]
        if url not in seen:
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            articles.append({'url': url, 'title': title})
            if len(articles) >= 5:
                break
    return articles

def extract_claudelog(html):
    """Extract articles from ClaudeLog"""
    articles = []
    pattern = r'href="(https://claudelog\.com/claude-news/[^"]+)"[^>]*>.*?<h[23][^>]*>(.*?)</h[23]>'
    matches = re.finditer(pattern, html, re.DOTALL)
    seen = set()
    for match in matches:
        url = match.group(1).split('?')[0].split('#')[0]
        if url not in seen and url != 'https://claudelog.com/claude-news/':
            seen.add(url)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            articles.append({'url': url, 'title': title})
            if len(articles) >= 5:
                break
    return articles

def crawl_source(source_id, url):
    """Crawl a source and extract articles"""
    print(f"Crawling {source_id}: {url}", file=sys.stderr)
    html = fetch_html(url)
    if not html:
        return []

    extractors = {
        'anthropic': extract_anthropic_news,
        'openai': extract_openai_news,
        'github-blog': extract_github_blog,
        'claude-code-github': extract_github_releases,
        'techcrunch-ai-music': extract_techcrunch,
        'techcrunch-anthropic': extract_techcrunch,
        'venturebeat-ai': extract_venturebeat,
        'deepmind': extract_deepmind_blog,
        'suno-ai-official': extract_suno_blog,
        'domoai-video': extract_domoai_blog,
        'google-cloud-ai': extract_google_cloud_blog,
        'claudelog': extract_claudelog,
    }

    extractor = extractors.get(source_id)
    if extractor:
        articles = extractor(html)
        print(f"Found {len(articles)} articles from {source_id}", file=sys.stderr)
        return articles
    else:
        print(f"No extractor for {source_id}", file=sys.stderr)
        return []

def main():
    # Read sources config
    with open('/home/runner/work/claude-auto-agent/claude-auto-agent/config/sources.json') as f:
        config = json.load(f)

    # Read notified URLs
    try:
        with open('/home/runner/work/claude-auto-agent/claude-auto-agent/data/latest.json') as f:
            latest = json.load(f)
            notified_urls = set(latest.get('notified_urls', []))
    except FileNotFoundError:
        notified_urls = set()

    # Crawl all enabled sources
    results = {}
    for idx, source in enumerate(config['sources']):
        if not source.get('enabled', False):
            continue

        # Rate limiting - wait between requests
        if idx > 0:
            time.sleep(2)

        articles = crawl_source(source['id'], source['url'])

        # Filter out already notified URLs
        new_articles = [a for a in articles if a['url'] not in notified_urls]

        if new_articles:
            results[source['id']] = {
                'name': source['name'],
                'categories': source['categories'],
                'articles': new_articles
            }

    # Output as JSON
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
