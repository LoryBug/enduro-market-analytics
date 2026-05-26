import csv
import html
import json
import os
import re
import socket
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "enduro_listings_wayback.csv"
socket.setdefaulttimeout(20)

TARGET_URLS = [
    "https://www.moto.it/moto-usate/ktm/300-exc",
    "https://www.moto.it/moto-usate/ktm/exc-300",
    "https://www.moto.it/moto-usate/ktm/250-exc",
    "https://www.moto.it/moto-usate/ktm/exc-250",
    "https://www.moto.it/moto-usate/ktm/350-exc-f",
    "https://www.moto.it/moto-usate/ktm/exc-350",
    "https://www.moto.it/moto-usate/ktm/exc-250-f",
    "https://www.moto.it/moto-usate/ktm/450-exc",
    "https://www.moto.it/moto-usate/ktm/exc-450",
    "https://www.moto.it/moto-usate/ktm/690-enduro",
    "https://www.moto.it/moto-usate/betamotor",
    "https://www.moto.it/moto-usate/husqvarna",
    "https://www.moto.it/moto-usate/gasgas",
    "https://www.moto.it/moto-epoca/ktm",
    "https://www.moto.it/moto-epoca/fantic-motor",
    "https://www.moto.it/moto-epoca/cagiva",
    "https://www.moto.it/moto-epoca/yamaha",
]


def expanded_target_urls():
    urls = []
    for url in TARGET_URLS:
        urls.append(url)
        urls.append(f"{url}/pagina-2")
        urls.append(f"{url}/pagina-3")
    return urls

ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

PROVINCE_TO_REGION = {
    "ag": "sicilia", "al": "piemonte", "an": "marche", "ao": "valle d'aosta", "ap": "marche",
    "aq": "abruzzo", "ar": "toscana", "at": "piemonte", "av": "campania", "ba": "puglia",
    "bg": "lombardia", "bi": "piemonte", "bl": "veneto", "bn": "campania", "bo": "emilia-romagna",
    "br": "puglia", "bs": "lombardia", "bt": "puglia", "bz": "trentino-alto adige", "ca": "sardegna",
    "cb": "molise", "ce": "campania", "ch": "abruzzo", "ci": "sardegna", "cl": "sicilia",
    "cn": "piemonte", "co": "lombardia", "cr": "lombardia", "cs": "calabria", "ct": "sicilia",
    "cz": "calabria", "en": "sicilia", "fc": "emilia-romagna", "fe": "emilia-romagna", "fg": "puglia",
    "fi": "toscana", "fm": "marche", "fr": "lazio", "ge": "liguria", "go": "friuli-venezia giulia",
    "gr": "toscana", "im": "liguria", "is": "molise", "kr": "calabria", "lc": "lombardia",
    "le": "puglia", "li": "toscana", "lo": "lombardia", "lt": "lazio", "lu": "toscana",
    "mb": "lombardia", "mc": "marche", "me": "sicilia", "mi": "lombardia", "mn": "lombardia",
    "mo": "emilia-romagna", "ms": "toscana", "mt": "basilicata", "na": "campania", "no": "piemonte",
    "nu": "sardegna", "or": "sardegna", "pa": "sicilia", "pc": "emilia-romagna", "pd": "veneto",
    "pe": "abruzzo", "pg": "umbria", "pi": "toscana", "pn": "friuli-venezia giulia", "po": "toscana",
    "pr": "emilia-romagna", "pt": "toscana", "pu": "marche", "pv": "lombardia", "pz": "basilicata",
    "ra": "emilia-romagna", "rc": "calabria", "re": "emilia-romagna", "rg": "sicilia", "ri": "lazio",
    "rm": "lazio", "rn": "emilia-romagna", "ro": "veneto", "sa": "campania", "si": "toscana",
    "so": "lombardia", "sp": "liguria", "sr": "sicilia", "ss": "sardegna", "su": "sardegna",
    "sv": "liguria", "ta": "puglia", "te": "abruzzo", "tn": "trentino-alto adige", "to": "piemonte",
    "tp": "sicilia", "tr": "umbria", "ts": "friuli-venezia giulia", "tv": "veneto", "ud": "friuli-venezia giulia",
    "va": "lombardia", "vb": "piemonte", "vc": "piemonte", "ve": "veneto", "vi": "veneto",
    "vr": "veneto", "vt": "lazio", "vv": "calabria",
}


def fetch_text(url, timeout=20, retries=1):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 academic project data collection",
            "Accept": "text/html,application/json,text/plain,*/*",
        },
    )
    last_error = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5)
    raise last_error


def get_snapshots(url, from_year=2020, to_year=2026, max_snapshots=6):
    encoded = urllib.parse.quote(url, safe="")
    cdx_url = (
        "https://web.archive.org/cdx?"
        f"url={encoded}&from={from_year}01&to={to_year}12&output=json"
        "&fl=timestamp,original,statuscode,mimetype"
        "&filter=statuscode:200&filter=mimetype:text/html&collapse=digest"
    )
    data = json.loads(fetch_text(cdx_url, timeout=20, retries=1))
    rows = data[1:] if len(data) > 1 else []
    if len(rows) <= max_snapshots:
        return rows

    # Keep snapshots spread across the available time range.
    step = (len(rows) - 1) / (max_snapshots - 1)
    indexes = sorted({round(i * step) for i in range(max_snapshots)})
    return [rows[i] for i in indexes]


def strip_tags(value):
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_italian_date(value, fallback_timestamp):
    value = strip_tags(value).lower()
    match = re.search(r"(\d{1,2})\s+([a-zà]+)\s+(\d{4})", value)
    if match:
        day = int(match.group(1))
        month = ITALIAN_MONTHS.get(match.group(2).replace("à", "a"))
        year = int(match.group(3))
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"
    return datetime.strptime(fallback_timestamp[:8], "%Y%m%d").date().isoformat()


def parse_number(value):
    if value is None:
        return ""
    value = html.unescape(value)
    value = re.sub(r"[^0-9]", "", value)
    return value


def infer_engine_cc(text):
    match = re.search(r"\b(125|150|200|250|300|350|400|450|500|525|530|600|620|640|690|701)\b", text.lower())
    return match.group(1) if match else ""


def normalize_original_url(archive_href):
    href = html.unescape(archive_href)
    match = re.search(r"https://www\.moto\.it[^\"'\s<]+", href)
    if match:
        return match.group(0)
    if href.startswith("/"):
        return f"https://www.moto.it{href}"
    return href


def parse_live_mcard_block(block, timestamp, archive_page_url, source_page):
    title_match = re.search(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]+)"', block, re.S)
    if not title_match:
        return None

    price_match = re.search(r'class="mcard-price-value"[^>]*>\s*(.*?)\s*</div>', block, re.S)
    price = parse_number(price_match.group(1)) if price_match else ""
    if not price:
        return None

    original_url = normalize_original_url(title_match.group(1))
    title = strip_tags(title_match.group(2)).replace(" usata", "").replace(" d'epoca", "")
    brand = title.split(" ")[0]
    model = title

    seller_match = re.search(r'class="mcard-seller[^>]*>(.*?)</div>', block, re.S)
    seller_type = strip_tags(seller_match.group(1)).lower() if seller_match else ""

    date_match = re.search(r'class="mcard-date"[^>]*>(.*?)</div>', block, re.S)
    listing_date = parse_italian_date(date_match.group(1), timestamp) if date_match else datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()

    location_match = re.search(r'class="mcard-grid-city"[^>]*title="\s*([^"]+)"', block, re.S)
    location = strip_tags(location_match.group(1)) if location_match else ""
    province_match = re.search(r"\(([A-Z]{2})\)", location)
    province = province_match.group(1).lower() if province_match else ""
    region = PROVINCE_TO_REGION.get(province, "")

    year = ""
    year_match = re.search(r"\((\d{4})(?:\s*-\s*\d{2,4})?\)", model)
    if year_match:
        year = year_match.group(1)
    if not year:
        year_cell = re.search(r'class="mcard-grid-item text-center"[^>]*>\s*(19[6-9][0-9]|20[0-2][0-9])\s*</div>', block, re.S)
        year = year_cell.group(1) if year_cell else ""

    km_match = re.search(r'class="mcard-grid-item text-center"[^>]*>\s*([0-9\.]+)\s*Km\s*</div>', block, re.S)
    km = parse_number(km_match.group(1)) if km_match else ""

    is_2stroke = bool(re.search(r"\b(2t|tpi|tbi|exc e|ec 300|te 300|rr 300)\b", model.lower()))

    return {
        "listing_date": listing_date,
        "snapshot_date": datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat(),
        "source": "moto.it-live",
        "brand": brand.lower(),
        "model": model.lower(),
        "year": year,
        "km": km,
        "engine_cc": infer_engine_cc(model),
        "price": price,
        "region": region,
        "province": province,
        "seller_type": seller_type,
        "is_2stroke": is_2stroke,
        "condition_score": "3",
        "has_documents": True,
        "url": original_url,
        "archive_url": archive_page_url,
        "source_page": source_page,
    }


def parse_listing_block(block, timestamp, archive_page_url, source_page):
    title_match = re.search(r'class="app-linked-title"\s+href="([^"]+)"\s+title="([^"]+)"', block)
    if not title_match:
        title_match = re.search(r'<h2 class="app-titles">\s*<a\s+href="([^"]+)"\s+title="([^"]+)"', block, re.S)
    if not title_match:
        return parse_live_mcard_block(block, timestamp, archive_page_url, source_page)

    original_url = normalize_original_url(title_match.group(1))
    title = strip_tags(title_match.group(2)).replace(" usata", "").replace(" d'epoca", "")

    brand_match = re.search(r'class="app-leaf">(.*?)</span>', block, re.S)
    model_match = re.search(r'class="app-title">(.*?)</span>', block, re.S)
    brand = strip_tags(brand_match.group(1)) if brand_match else title.split(" ")[0]
    model = strip_tags(model_match.group(1)) if model_match else title

    price_match = re.search(r'class="app-price">\s*([0-9\.]+)\s*&euro;', block, re.S)
    price = parse_number(price_match.group(1)) if price_match else ""
    if not price:
        return None

    seller_match = re.search(r'class="app-seller">(.*?)</div>', block, re.S)
    seller_type = strip_tags(seller_match.group(1)).lower() if seller_match else ""

    date_match = re.search(r'class="app-date">(.*?)</div>', block, re.S)
    listing_date = parse_italian_date(date_match.group(1), timestamp) if date_match else datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()

    specs_match = re.search(r'<ul class="app-specs">(.*?)</ul>', block, re.S)
    specs = re.findall(r"<li[^>]*>(.*?)</li>", specs_match.group(1), re.S) if specs_match else []
    clean_specs = [strip_tags(item) for item in specs]

    year_match = re.search(r"\((\d{4})(?:\s*-\s*\d{2,4})?\)", model)
    year = year_match.group(1) if year_match else ""
    if not year:
        for item in clean_specs:
            spec_year = re.fullmatch(r"(19[6-9][0-9]|20[0-2][0-9])", item)
            if spec_year:
                year = spec_year.group(1)
                break

    location = clean_specs[0] if clean_specs else ""
    province_match = re.search(r"\(([A-Z]{2})\)", location)
    province = province_match.group(1).lower() if province_match else ""
    region = PROVINCE_TO_REGION.get(province, "")

    km = ""
    for item in clean_specs:
        if item.lower().startswith("km"):
            km = parse_number(item)
            break

    is_2stroke = bool(re.search(r"\b(2t|tpi|tbi|exc e|ec 300|te 300|rr 300)\b", model.lower()))

    return {
        "listing_date": listing_date,
        "snapshot_date": datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat(),
        "source": "moto.it-wayback",
        "brand": brand.lower(),
        "model": model.lower(),
        "year": year,
        "km": km,
        "engine_cc": infer_engine_cc(model),
        "price": price,
        "region": region,
        "province": province,
        "seller_type": seller_type,
        "is_2stroke": is_2stroke,
        "condition_score": "3",
        "has_documents": True,
        "url": original_url,
        "archive_url": archive_page_url,
        "source_page": source_page,
    }


def parse_archive_page(html_text, timestamp, archive_page_url, source_page):
    starts = [match.start() for match in re.finditer(r'<li class="app-list-item', html_text)]
    if not starts:
        starts = [match.start() for match in re.finditer(r'<li class="list-item"', html_text)]
    blocks = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else html_text.find("</ul>", start)
        if end == -1:
            end = len(html_text)
        blocks.append(html_text[start:end])
    listings = []
    for block in blocks:
        row = parse_listing_block(block, timestamp, archive_page_url, source_page)
        if row:
            listings.append(row)
    return listings


FIELDNAMES = [
    "listing_date",
    "snapshot_date",
    "source",
    "brand",
    "model",
    "year",
    "km",
    "engine_cc",
    "price",
    "region",
    "province",
    "seller_type",
    "is_2stroke",
    "condition_score",
    "has_documents",
    "url",
    "archive_url",
    "source_page",
]


def save_rows(rows):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = OUTPUT_PATH.with_suffix(".tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    try:
        os.replace(tmp_path, OUTPUT_PATH)
    except PermissionError:
        fallback = OUTPUT_PATH.with_name(f"{OUTPUT_PATH.stem}_{int(time.time())}.csv")
        os.replace(tmp_path, fallback)
        print(f"  output locked, saved fallback: {fallback}")


def load_existing_rows():
    if not OUTPUT_PATH.exists():
        return []
    with OUTPUT_PATH.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def collect():
    all_rows = load_existing_rows()
    seen = {(row.get("snapshot_date"), row.get("url")) for row in all_rows}
    targets = expanded_target_urls()
    from_year = int(os.getenv("FROM_YEAR", "2020"))
    to_year = int(os.getenv("TO_YEAR", "2026"))
    max_snapshots = int(os.getenv("MAX_SNAPSHOTS", "6"))
    start_target = int(os.getenv("START_TARGET", "0"))
    max_targets = os.getenv("MAX_TARGETS")
    targets = targets[start_target:]
    if max_targets:
        targets = targets[: int(max_targets)]

    for offset, target_url in enumerate(targets, start=start_target):
        print(f"[{offset}] Snapshots for {target_url}", flush=True)
        try:
            snapshots = get_snapshots(target_url, from_year=from_year, to_year=to_year, max_snapshots=max_snapshots)
        except Exception as exc:
            print(f"  CDX failed: {exc}")
            continue

        for timestamp, original, _status, _mime in snapshots:
            archive_url = f"https://web.archive.org/web/{timestamp}/{original}"
            try:
                page = fetch_text(archive_url, timeout=20, retries=1)
                rows = parse_archive_page(page, timestamp, archive_url, target_url)
                print(f"  {timestamp}: {len(rows)} listings")
                for row in rows:
                    key = (row["snapshot_date"], row["url"])
                    if key not in seen:
                        seen.add(key)
                        all_rows.append(row)
                save_rows(all_rows)
                time.sleep(0.8)
            except Exception as exc:
                print(f"  fetch/parse failed {timestamp}: {exc}")
        save_rows(all_rows)
        print(f"  progressive save: {len(all_rows)} rows")
    return all_rows


def main():
    rows = collect()
    save_rows(rows)
    print(f"Saved {len(rows)} real historical rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
