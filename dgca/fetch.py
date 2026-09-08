"""Refresh DGCA workbooks atomically, keeping unavailable reports out of the cache."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import time
from urllib.parse import quote, unquote, urlsplit
from zipfile import ZipFile, is_zipfile

import requests


def is_workbook(content):
    if content.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        return True
    if not is_zipfile(BytesIO(content)):
        return False
    with ZipFile(BytesIO(content)) as workbook:
        return 'xl/workbook.xml' in workbook.namelist() and workbook.testzip() is None


def is_source(content, suffix):
    if suffix.lower() != '.pdf':
        return is_workbook(content)
    if not content.startswith(b'%PDF-'):
        return False
    import pdfplumber
    try:
        with pdfplumber.open(BytesIO(content)) as document:
            return bool(document.pages)
    except Exception:
        return False


def fetch(url):
    # Preserve URL-list filenames, including legacy %20 names used by the parser.
    filename = urlsplit(url).path.rsplit('/', 1)[-1]
    url = quote(unquote(url), safe=':/')
    kind = 'domestic' if '/domestic/' in url else 'international'
    format_directory = 'pdf' if filename.lower().endswith('.pdf') else 'xlsx'
    destination = Path('raw') / format_directory / kind / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = destination.read_bytes() if destination.exists() else None
    if previous is not None and not is_source(previous, destination.suffix):
        # Older fetches saved HTTP error documents as spreadsheets and CSVs.
        rejected = Path('raw/rejected') / kind / destination.name
        rejected.parent.mkdir(parents=True, exist_ok=True)
        destination.replace(rejected)
        (Path('raw/csv') / kind / destination.with_suffix('.csv').name).unlink(missing_ok=True)
        previous = None

    result = {'url': url, 'file': str(destination)}
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(15, 90))
            result['http_status'] = response.status_code
            if response.status_code in (403, 404):
                # DGCA lists some reports before publication, including future months.
                result['status'] = 'unavailable_cached' if previous is not None else 'unavailable'
                return result
            response.raise_for_status()
            if not is_source(response.content, destination.suffix):
                raise ValueError('Response is not a valid Excel workbook or PDF')
            result['bytes'] = len(response.content)
            if response.content == previous:
                result['status'] = 'unchanged'
            else:
                temporary = destination.with_suffix(destination.suffix + '.tmp')
                temporary.write_bytes(response.content)
                temporary.replace(destination)
                result['status'] = 'updated' if previous is not None else 'downloaded'
            return result
        except (requests.RequestException, ValueError) as error:
            if attempt == 2:
                return {**result, 'status': 'error', 'error': str(error)}
            time.sleep(attempt + 1)


def main():
    # Clean invalid legacy files even when DGCA no longer lists their URLs.
    for destination in Path('raw/xlsx').glob('*/*'):
        if destination.is_file() and not is_workbook(destination.read_bytes()):
            kind = destination.parent.name
            rejected = Path('raw/rejected') / kind / destination.name
            rejected.parent.mkdir(parents=True, exist_ok=True)
            destination.replace(rejected)
            (Path('raw/csv') / kind / destination.with_suffix('.csv').name).unlink(missing_ok=True)
    urls = sorted(set(Path('urls.txt').read_text().splitlines()))
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(fetch, filter(None, urls)))
    counts = {status: sum(r['status'] == status for r in results)
              for status in sorted({r['status'] for r in results})}
    report = {'fetched_at': datetime.now(timezone.utc).isoformat(),
              'counts': counts, 'files': results}
    Path('raw/fetch-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(counts, indent=2))
    for result in results:
        if result['status'] in ('error', 'unavailable', 'unavailable_cached'):
            print(result['status'], result['url'], result.get('error', ''))
    if counts.get('error') or counts.get('unavailable_cached'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
