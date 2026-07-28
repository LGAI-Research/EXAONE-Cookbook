#!/usr/bin/env python3
"""
Search arXiv papers and extract metadata.
Usage: python scripts/search_arxiv.py [query] [max_results]
"""
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def search_arxiv(query, max_results=20):
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

def main():
    # Parse command line arguments
    query = sys.argv[1] if len(sys.argv) > 1 else "all:ai"
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"Searching arXiv for: {query}")
    print(f"Max results: {max_results}")
    
    papers = search_arxiv(query, max_results)
    
    if not papers:
        print("No papers found.")
        return
    
    # Print results in tab-separated format for easy parsing
    for paper in papers:
        print(f"{paper['arxiv_id']}\t{paper['title']}\t{paper['authors']}\t{paper['link']}\t{paper['published']}")
    
    # Also output as JSON for programmatic use
    json_output = json.dumps(papers, indent=2)
    print(f"\nJSON output ({len(papers)} papers):")
    print(json_output)

if __name__ == "__main__":
    main()