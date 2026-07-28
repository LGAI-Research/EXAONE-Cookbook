#!/usr/bin/env python3
"""
주간 AI 뉴스 브리프 생성 스크립트
RSS 피드와 arXiv 논문을 수집하여 구조화된 마크다운 브리프를 생성합니다.
"""
import sys
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json
import datetime
import subprocess
import time
import feedparser
from typing import List, Dict, Any

# =========================================
# 설정: RSS 피드 목록
# =========================================
RSS_FEEDS = [
    {
        "name": "AI Research: The Gradient",
        "url": "https://thegradient.pub/feed",
        "category": "Research Blog"
    },
    {
        "name": "AI Research: Distill",
        "url": "https://distill.pub/feed",
        "category": "Research Blog"
    },
    {
        "name": "Google Research Blog",
        "url": "https://ai.google/research/blog/atom.xml",
        "category": "Research Blog"
    },
    {
        "name": "Meta AI Research Blog",
        "url": "https://research.fb.com/feed",
        "category": "Research Blog"
    },
    {
        "name": "MIT CSAIL",
        "url": "https://d4m.org/feed",
        "category": "Research Blog"
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/tag/ai/rss.xml",
        "category": "Industry"
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/tag/ai-ar-vr/feed.xml",
        "category": "Industry"
    },
    {
        "name": "NeurIPS",
        "url": "https://neurips.cc/feed",
        "category": "Conference"
    },
    {
        "name": "ICML",
        "url": "https://icml.cc/feed",
        "category": "Conference"
    }
]

# =========================================
# arXiv 검색 함수
# =========================================
def search_arxiv(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Search arXiv papers and return metadata."""
    # Build arXiv API URL
    base_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}" if query != "all:ai" else "all:ai",
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Error fetching arXiv: {e}", file=sys.stderr)
        return []
    
    # Parse XML
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        return []
    
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    papers = []
    
    for entry in root.findall('a:entry', ns):
        title_elem = entry.find('a:title', ns)
        if title_elem is None or title_elem.text is None:
            continue
        title = title_elem.text.strip()
        
        # arXiv ID
        link_elem = entry.find('a:id', ns)
        if link_elem is None or link_elem.text is None:
            continue
        arxiv_id_full = link_elem.text
        arxiv_id = arxiv_id_full.split('/')[-1]
        
        # Link
        link = f"https://arxiv.org/abs/{arxiv_id}"
        
        # Published date
        published_elem = entry.find('a:published', ns)
        published = published_elem.text if published_elem is not None else ''
        
        # Summary/abstract
        summary_elem = entry.find('a:summary', ns)
        abstract = summary_elem.text if summary_elem is not None else ''
        # Truncate abstract to 300 chars for preview
        abstract_preview = abstract[:300] + "..." if len(abstract) > 300 else abstract
        
        # Authors
        authors = []
        for author_elem in entry.findall('a:author', ns):
            name_elem = author_elem.find('a:name', ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text)
        authors_str = ", ".join(authors)
        
        # Categories
        categories = []
        for category_elem in entry.findall('a:category', ns):
            term = category_elem.get('term')
            if term:
                categories.append(term)
        categories_str = ", ".join(categories)
        
        papers.append({
            "title": title,
            "arxiv_id": arxiv_id,
            "link": link,
            "published": published[:10] if published else '',
            "authors": authors_str,
            "abstract": abstract_preview,
            "categories": categories_str,
            "published_full": published
        })
    
    return papers

# =========================================
# RSS 피드 파싱 함수
# =========================================
def fetch_rss_feed(url: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch latest entries from RSS/Atom feed."""
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"Error fetching RSS feed {url}: {e}", file=sys.stderr)
        return []
    
    entries = []
    for entry in feed.entries[:limit]:
        entry_dict = {
            "title": entry.get('title', ''),
            "link": entry.get('link', ''),
            "published": entry.get('published', ''),
            "summary": entry.get('summary', ''),
            "category": entry.get('tags', []),
            "source": feed.feed.get('title', ''),
            "feed_url": url
        }
        # Format date to YYYY-MM-DD
        if entry_dict['published']:
            try:
                # Parse date string (feedparser returns datetime)
                dt = entry.get('published_parsed')
                if dt:
                    dt_obj = datetime.datetime(*dt[:6])
                    entry_dict['published_date'] = dt_obj.strftime('%Y-%m-%d')
                else:
                    # fallback: take first 10 chars
                    entry_dict['published_date'] = entry_dict['published'][:10]
            except:
                entry_dict['published_date'] = entry_dict['published'][:10]
        else:
            entry_dict['published_date'] = ''
        
        entries.append(entry_dict)
    
    return entries

# =========================================
# 데이터 수집 함수
# =========================================
def collect_data() -> Dict[str, Any]:
    """Collect data from RSS feeds and arXiv."""
    print("Collecting RSS feeds...")
    rss_entries = []
    for feed in RSS_FEEDS:
        print(f"  - {feed['name']}")
        entries = fetch_rss_feed(feed['url'])
        for entry in entries:
            entry['category'] = feed['category']
            entry['source'] = feed['name']
        rss_entries.extend(entries)
        time.sleep(0.1)  # Rate limiting
    
    print("Searching arXiv for latest papers...")
    arxiv_papers = search_arxiv("machine learning", max_results=15)
    print(f"  Found {len(arxiv_papers)} papers.")
    
    # Combine all entries
    all_entries = rss_entries + arxiv_papers
    
    # Sort by date (newest first)
    all_entries.sort(key=lambda x: x.get('published_date', ''), reverse=True)
    
    return {
        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "timestamp": datetime.datetime.now().isoformat(),
        "entries": all_entries,
        "arxiv_count": len(arxiv_papers),
        "rss_count": len(rss_entries)
    }

# =========================================
# 마크다운 생성 함수
# =========================================
def generate_markdown(data: Dict[str, Any]) -> str:
    """Generate markdown content from collected data."""
    date_str = data['date']
    timestamp = data['timestamp']
    entries = data['entries']
    
    # Categorize entries
    categories = ['Research Blog', 'Industry', 'Conference', 'ArXiv Research']
    categorized = {cat: [] for cat in categories}
    
    for entry in entries:
        cat = entry.get('category', '')
        if 'arxiv' in str(entry).lower():
            cat = 'ArXiv Research'
        elif cat not in categorized:
            # Handle other categories
            pass
        categorized.setdefault(cat, []).append(entry)
    
    # Build markdown for each category
    def build_list(category_entries, category_name):
        if not category_entries:
            return f"### {category_name}\nNo entries this week.\n"
        
        md = f"### {category_name}\n"
        for entry in category_entries[:5]:  # limit to 5 per category
            title = entry.get('title', '')
            link = entry.get('link', '')
            source = entry.get('source', '')
            published = entry.get('published_date', '')
            
            if link:
                md += f"- **[{title}]({link})**"
            else:
                md += f"- **{title}**"
            
            if source:
                md += f"\n  _Source_: {source}"
            if published:
                md += f"\n  _Date_: {published}"
            
            # Add summary or abstract if available and not too long
            summary = entry.get('summary', '')
            abstract = entry.get('abstract', '')
            content = summary if summary else abstract
            if content and len(content) > 100:
                content = content[:100] + "..."
            if content:
                md += f"\n  _Summary_: {content}"
            md += "\n"
        
        if len(category_entries) > 5:
            md += f"\n_Showing 5 of {len(category_entries)} entries._
"
        
        return md
    
    news_section = ""
    for cat in categories:
        if cat in categorized and categorized[cat]:
            news_section += build_list(categorized[cat], cat) + "\n"
    
    # Summary
    summary = f"이번 주는 총 {data['rss_count']}개의 RSS 항목과 {data['arxiv_count']}개의 arXiv 논문이 수집되었습니다. 주요 주제는 기계 학습, 자연어 처리, 컴퓨터 비전입니다.\n"
    
    # Analysis
    analysis = f"이번 주 주요 트렌드: {', '.join(categories[:3])}\n주목할 점: 최신 연구 동향과 산업 발전.
"
    
    # Render template
    template = f"""
# 주간 AI 뉴스 브리프 – {{date}}

## 📊 요약
{{summary}}

## 🔬 연구 소식
{news_section}

## 📈 분석 및 인사이트
{{analysis}}

\n---

*수집 시점: {{timestamp}}*
*자동 생성: Hermes Agent weekly_brief*
"""
    
    # Replace placeholders
    template = template.replace('{{date}}', date_str)
    template = template.replace('{{timestamp}}', timestamp)
    template = template.replace('{{summary}}', summary)
    template = template.replace('{{news_section}}', news_section)
    template = template.replace('{{analysis}}', analysis)
    
    return template

# =========================================
# 메인 함수
# =========================================
def main():
    print("Weekly AI News Brief Generator")
    print("=" * 50)
    
    # Collect data
    data = collect_data()
    
    # Generate markdown
    markdown = generate_markdown(data)
    
    # Save to file
    output_filename = f"weekly_brief_{data['date']}.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"\nBrief saved to: {output_filename}")
    print(f"Total entries: {len(data['entries'])}")
    print("Done!")

if __name__ == "__main__":
    main()