#!/usr/bin/env python3

import os
import re
import time
import json
import requests
import shutil
from pathlib import Path
from html.parser import HTMLParser

# Constants
BASE_URL = "https://www.dgca.gov.in/digigov-portal/scan?"
PARENT_CONTENT_ID = "4184"
RULE_BOOK_ID = "259"
REQUEST_DATA = {
    "baseLocale": "",
    "screenId": "10000001",
    "classification": "",
    "actionVal": "viewStaticData",
    "requestType": "ApplicationRH",
    "attachId": "",
    "langType": "2",
    "ruleBookId": RULE_BOOK_ID,
    "attr": ""
}

# Patterns
JSP_URL_PATTERN = r"jsp[a-zA-Z0-9/ _%,]*\.[a-z]+"
YEARLY_PATTERN = r"yearly[^\"']*html"
CITY_PAIR_PATTERN = r'city.*?pair|CITYPAIR'


def make_request(content_id: str, service_name: str) -> str:
    """Make a POST request to DGCA API and return response text."""
    data = {**REQUEST_DATA, "contentId": content_id, "serviceName": service_name}
    response = requests.post(BASE_URL, data=data)
    response.raise_for_status()
    return response.text


class DataUrlExtractor(HTMLParser):
    """HTML parser to extract data-url attributes from anchor tags."""
    def __init__(self):
        super().__init__()
        self.data_urls = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'data-url' and attr_value:
                    self.data_urls.append(attr_value)


def extract_data_urls_from_html(html_content: str) -> list:
    """Extract all data-url attributes from HTML content."""
    parser = DataUrlExtractor()
    parser.feed(html_content)
    return parser.data_urls


def find_html_in_json(obj, html_strings=None):
    """Recursively search JSON object for HTML content strings."""
    if html_strings is None:
        html_strings = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Check if this field might contain HTML (like contentType, content, html, etc.)
            if isinstance(value, str) and ('<table' in value.lower() or '<a' in value.lower() or 'data-url' in value.lower()):
                html_strings.append(value)
            else:
                find_html_in_json(value, html_strings)
    elif isinstance(obj, list):
        for item in obj:
            find_html_in_json(item, html_strings)
    elif isinstance(obj, str):
        # Try to parse as nested JSON
        if obj.strip().startswith('{') or obj.strip().startswith('['):
            try:
                nested = json.loads(obj)
                find_html_in_json(nested, html_strings)
            except (json.JSONDecodeError, ValueError):
                pass
    
    return html_strings


def extract_urls(content: str) -> set:
    """Extract Excel URLs from content, including from HTML tables in JSON responses."""
    urls = set()
    
    # Method 1: Extract from JSON response with HTML embedded in it
    try:
        # Try to parse as JSON first
        if content.strip().startswith('{') or content.strip().startswith('['):
            data = json.loads(content)
            # Recursively find all HTML strings in the JSON
            html_strings = find_html_in_json(data)
            for html_content in html_strings:
                data_urls = extract_data_urls_from_html(html_content)
                for data_url in data_urls:
                    # Process XLS/XLSX URLs
                    if data_url.startswith('jsp/') and data_url.endswith(('.xls', '.xlsx')):
                        url = data_url.replace("jsp/dgca", "https://public-prd-dgca.s3.ap-south-1.amazonaws.com")
                        urls.add(url)
    except (json.JSONDecodeError, KeyError, TypeError):
        # Not JSON or doesn't have expected structure, continue with regex method
        pass
    
    # Method 2: Use regex pattern (original method) - also works on raw HTML in response
    matches = re.findall(JSP_URL_PATTERN, content)
    for match in matches:
        url = match.replace("jsp/dgca", "https://public-prd-dgca.s3.ap-south-1.amazonaws.com")
        if url.endswith((".xls", ".xlsx")):
            urls.add(url)
    
    return urls


def extract_html_content_ids(content: str) -> set:
    """Extract HTML content IDs from content, including from HTML tables in JSON responses."""
    html_content_ids = set()
    
    # Method 1: Extract from JSON response with HTML embedded in it
    try:
        # Try to parse as JSON first
        if content.strip().startswith('{') or content.strip().startswith('['):
            data = json.loads(content)
            # Recursively find all HTML strings in the JSON
            html_strings = find_html_in_json(data)
            for html_content in html_strings:
                data_urls = extract_data_urls_from_html(html_content)
                for data_url in data_urls:
                    # Process HTML links like "yearly/259/9467/html"
                    if '/html' in data_url.lower() or data_url.endswith('.html'):
                        parts = data_url.split('/')
                        # Look for numeric content ID (typically the last part before /html)
                        # For "yearly/259/9467/html", the content ID is 9467
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) >= 3:
                                html_content_ids.add(part)
    except (json.JSONDecodeError, KeyError, TypeError):
        # Not JSON or doesn't have expected structure, continue with regex method
        pass
    
    # Method 2: Use the same JSP pattern to find HTML links
    matches = re.findall(JSP_URL_PATTERN, content)
    for match in matches:
        # Only process HTML files (not XLS/XLSX which are handled separately)
        if match.endswith((".html", ".htm")):
            # Extract content ID from paths like "jsp/dgca/contentId/..."
            parts = match.split("/")
            if len(parts) >= 3:
                # The content ID is typically the third part
                content_id = parts[2]
                # Validate it's a numeric content ID
                if content_id.isdigit():
                    html_content_ids.add(content_id)
    
    # Method 3: Use a more general pattern to catch HTML links (similar to extract_content_ids)
    # Look for patterns like "yearly/259/9467/html"
    yearly_html_pattern = r"yearly/[^\"']*html"
    yearly_matches = re.findall(yearly_html_pattern, content, re.IGNORECASE)
    for match in yearly_matches:
        parts = match.split("/")
        # Content ID is typically the third part in "yearly/259/9467/html"
        if len(parts) >= 3:
            content_id = parts[2]
            if content_id.isdigit():
                html_content_ids.add(content_id)
    
    # Method 4: General HTML pattern
    general_html_pattern = r"jsp/[^\"']*\.html"
    general_matches = re.findall(general_html_pattern, content, re.IGNORECASE)
    for match in general_matches:
        parts = match.split("/")
        if len(parts) >= 3:
            content_id = parts[2]
            if content_id.isdigit():
                html_content_ids.add(content_id)
    
    return html_content_ids


def extract_content_ids(content: str, pattern: str) -> set:
    """Extract content IDs from content using pattern."""
    content_ids = set()
    matches = re.findall(pattern, content, re.IGNORECASE)
    for match in matches:
        parts = match.split("/")
        if len(parts) >= 3:
            content_ids.add(parts[2])
    return content_ids


def get_years_from_parent(content: str) -> set:
    """Extract year content IDs from parent data."""
    return extract_content_ids(content, YEARLY_PATTERN)


def get_domestic_city_pair_content_id(year_content: str) -> str | None:
    """Extract domestic city pair content ID from year content."""
    if not re.search(CITY_PAIR_PATTERN, year_content, re.IGNORECASE):
        return None
    
    # Find all yearly HTML links in the content
    html_matches = re.findall(YEARLY_PATTERN, year_content, re.IGNORECASE)
    for match in html_matches:
        parts = match.split("/")
        if len(parts) >= 3:
            return parts[2]
    return None


def recursively_extract_urls(content_id: str, visited: set = None, depth: int = 0, max_depth: int = 10) -> set:
    """Recursively extract URLs from content, following HTML links."""
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    if content_id in visited or depth > max_depth:
        return set()
    
    visited.add(content_id)
    all_urls = set()
    
    # Fetch content for this content ID
    try:
        content = make_request(content_id, "fetchRulebookContentDtlsList")
        time.sleep(3)  # Rate limiting
        
        # Extract XLS/XLSX URLs from current content
        urls = extract_urls(content)
        all_urls.update(urls)
        if urls:
            print(f"    {'  ' * depth}Found {len(urls)} XLS/XLSX URLs")
        
        # Extract HTML content IDs from current content
        html_content_ids = extract_html_content_ids(content)
        
        # Recursively process each HTML content ID
        for html_content_id in html_content_ids:
            if html_content_id not in visited:
                print(f"    {'  ' * depth}Following HTML link (contentId: {html_content_id})...")
                nested_urls = recursively_extract_urls(html_content_id, visited, depth + 1, max_depth)
                all_urls.update(nested_urls)
    
    except Exception as e:
        print(f"    {'  ' * depth}Error processing contentId {content_id}: {e}")
    
    return all_urls


def process_domestic_data():
    """Process domestic data: get years, then XLS files and recursively extract from HTMLs."""
    print("Fetching parent data (contentId: 4184)...")
    parent_content = make_request(PARENT_CONTENT_ID, "getParentData")
    print(f"Parent data fetched, response length: {len(parent_content)}")
    
    # Extract year content IDs from parent
    print("Extracting year content IDs...")
    year_content_ids = extract_content_ids(parent_content, r"monthlyStatistics.*?html")
    print(f"Found {len(year_content_ids)} year content IDs")
    
    # Fetch year data and recursively extract URLs
    print(f"Fetching {len(year_content_ids)} year data files...")
    all_domestic_urls = set()
    visited = set()
    
    for content_id in sorted(year_content_ids):
        time.sleep(3)  # Rate limiting
        print(f"  Fetching year {content_id}...")
        
        # Recursively extract URLs from this year's content
        year_urls = recursively_extract_urls(content_id, visited)
        all_domestic_urls.update(year_urls)
        print(f"  Year {content_id}: Found {len(year_urls)} URLs (total so far: {len(all_domestic_urls)})")
    
    print(f"Found {len(all_domestic_urls)} total domestic URLs")
    
    return sorted(all_domestic_urls)


def process_international_data():
    """Generate international URLs (retain existing flow)."""
    print("Generating international URLs...")
    international_urls = []
    for table in range(1, 5):  # 1 to 4
        for year in range(15, 26):  # 15 to 25
            for quarter in range(1, 5):  # 1 to 4
                url = f"https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/dataReports/aviationDataStatistics/airTransport/international/quaterly/{year}Q{quarter}_{table}.xlsx"
                international_urls.append(url)
    return international_urls


def save_urls(urls: list, filename: str):
    """Save URLs to file."""
    with open(filename, "w") as f:
        f.write("\n".join(urls) + "\n")


def main():
    """Main execution function."""
    # Process domestic data
    domestic_urls = process_domestic_data()
    save_urls(domestic_urls, "urls/domestic.txt")
    
    # Process international data
    international_urls = process_international_data()
    save_urls(international_urls, "urls/international.txt")
    
    # Merge all URLs
    print("Merging all URLs...")
    all_urls = sorted(set(domestic_urls + international_urls))
    save_urls(all_urls, "urls.txt")
    
    print(f"Done! Found {len(all_urls)} total URLs saved to urls.txt")


if __name__ == "__main__":
    # Create urls directory
    urls_dir = Path("urls")
    urls_dir.mkdir(exist_ok=True)
    
    try:
        main()
    finally:
        # Cleanup temporary files
        print("Cleaning up temporary files...")
        if Path("list.json").exists():
            os.remove("list.json")
        if urls_dir.exists():
            shutil.rmtree(urls_dir)
