import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "alert_state.json"
DEFAULT_TIMEOUT = 20
DEFAULT_MAX_MESSAGE_CHARS = 1400
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)
EURO_AMOUNT_PATTERN = re.compile(r"(?<!\d)(\d[\d. ,]*)\s*€", re.IGNORECASE)
MONTHLY_PAYMENT_PATTERN = re.compile(
    r"(?:desde\s*)?(?<!\d)(\d[\d. ,]*)\s*€\s*/?\s*mes",
    re.IGNORECASE,
)
AUTOHERO_DISCOUNT_PATTERN = re.compile(r"^Ahorra\s+(?<!\d)\d[\d. ,]*\s*€\s*", re.IGNORECASE)


@dataclass(frozen=True)
class Listing:
    source: str
    title: str
    url: str
    price: float | None
    monthly_payment: float | None


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    link_selector: str
    href_contains: str


SOURCES = [
    Source(
        name="Autohero",
        url=(
            "https://www.autohero.com/es/search/"
            "?sort=financed_price_asc&priceType=fixed&priceMax=10000&transmission=automatic"
        ),
        link_selector='a[href*="/id/"]',
        href_contains="/id/",
    ),
    Source(
        name="Clicars",
        url=(
            "https://www.clicars.com/coches-segunda-mano-ocasion/automatico"
            "?order=price.asc&priceMax=10000&financingMax=200"
        ),
        link_selector='a[href*="/comprar-"]',
        href_contains="/comprar-",
    ),
    Source(
        name="OcasionPlus",
        url=(
            "https://www.ocasionplus.com/coches-segunda-mano"
            "?v2&orderBy=lowerPrice&cuote%5Bto%5D=150&transmission=AUTO"
        ),
        link_selector='a[href*="/coches-segunda-mano/"]',
        href_contains="/coches-segunda-mano/",
    ),
]


def load_env() -> None:
    load_dotenv(BASE_DIR / ".env")


def env_float(name: str, default: float | None = None) -> float | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return float(value.strip().replace(",", "."))


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    items = []
    for part in value.split(","):
        cleaned = part.strip().lower()
        if cleaned:
            items.append(cleaned)
    return items


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": os.getenv("HTTP_USER_AGENT", DEFAULT_USER_AGENT),
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }
    )
    return session


def fetch_html(session: requests.Session, url: str) -> str:
    timeout = int(env_float("REQUEST_TIMEOUT", DEFAULT_TIMEOUT) or DEFAULT_TIMEOUT)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def to_number(raw_value: str) -> float:
    normalized = raw_value.replace(".", "").replace(" ", "").replace(",", ".")
    return float(normalized)


def extract_monthly_payment(text: str) -> float | None:
    match = MONTHLY_PAYMENT_PATTERN.search(text)
    if not match:
        return None
    return to_number(match.group(1))


def normalize_autohero_segment(text: str) -> str:
    first_segment = clean_text(text.split("•")[0])
    without_monthly = MONTHLY_PAYMENT_PATTERN.sub("", first_segment).strip()
    return AUTOHERO_DISCOUNT_PATTERN.sub("", without_monthly).strip()


def extract_price(text: str, monthly_payment: float | None, source: Source) -> float | None:
    if source.name == "Autohero":
        match = EURO_AMOUNT_PATTERN.search(normalize_autohero_segment(text))
        if match:
            return to_number(match.group(1))

    amounts = []
    for match in EURO_AMOUNT_PATTERN.finditer(text):
        try:
            value = to_number(match.group(1))
        except ValueError:
            continue
        if monthly_payment is not None and abs(value - monthly_payment) < 0.01:
            continue
        amounts.append(value)

    if not amounts:
        return None

    return min(amounts)


def extract_autohero_title(text: str) -> str:
    segment = normalize_autohero_segment(text)
    price_match = EURO_AMOUNT_PATTERN.search(segment)
    if not price_match:
        return segment[:140]

    left = clean_text(segment[: price_match.start()])
    right = clean_text(segment[price_match.end() :])
    if left and right:
        return f"{left} - {right}"
    if left:
        return left
    return segment[:140]


def extract_title(text: str, source: Source) -> str:
    text = clean_text(text)
    if source.name == "Autohero":
        return extract_autohero_title(text)
    if source.name == "Clicars":
        title_match = re.match(r"(?:delivery\s+one_day\s+24h\s+)?(.+?)\s+\d{4}\s*\|", text, re.IGNORECASE)
        if title_match:
            return clean_text(title_match.group(1))
    if source.name == "OcasionPlus":
        title_match = re.search(r"de segunda mano\s+(.+?)\s+(?:\d+[.]?\d*€|desde)", text, re.IGNORECASE)
        if title_match:
            return clean_text(title_match.group(1))
    return text[:140]


def parse_source(session: requests.Session, source: Source) -> list[Listing]:
    html = fetch_html(session, source.url)
    soup = BeautifulSoup(html, "html.parser")
    listings: list[Listing] = []
    seen_urls: set[str] = set()

    for link in soup.select(source.link_selector):
        href = link.get("href")
        if not href or source.href_contains not in href:
            continue

        full_url = urljoin(source.url, href)
        if full_url in seen_urls:
            continue

        text = clean_text(link.get_text(" ", strip=True))
        if not text or len(text) < 20:
            continue

        monthly_payment = extract_monthly_payment(text)
        price = extract_price(text, monthly_payment, source)
        if price is None and monthly_payment is None:
            continue

        title = extract_title(text, source)
        listings.append(
            Listing(
                source=source.name,
                title=title,
                url=full_url,
                price=price,
                monthly_payment=monthly_payment,
            )
        )
        seen_urls.add(full_url)

    return listings


def listing_matches_filters(listing: Listing) -> bool:
    haystack = clean_text(f"{listing.title} {listing.url}").lower()
    exclude_keywords = env_list("EXCLUDE_KEYWORDS", "puretech")
    max_price = env_float("MAX_PRICE")
    max_monthly_payment = env_float("MAX_MONTHLY_PAYMENT")

    if any(keyword in haystack for keyword in exclude_keywords):
        return False

    if max_price is not None and listing.price is not None and listing.price > max_price:
        return False

    if (
        max_monthly_payment is not None
        and listing.monthly_payment is not None
        and listing.monthly_payment > max_monthly_payment
    ):
        return False

    return True


def load_seen_urls() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {item for item in data.get("seen_urls", []) if isinstance(item, str)}


def save_seen_urls(urls: Iterable[str]) -> None:
    payload = {"seen_urls": sorted(set(urls))}
    STATE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def shorten_url(url: str) -> str:
    parsed = urlsplit(url)
    clean_path = parsed.path.rstrip("/") or parsed.path
    return urlunsplit((parsed.scheme, parsed.netloc, clean_path, "", ""))


def shorten_title(title: str, max_length: int = 55) -> str:
    compact_title = clean_text(title)
    if len(compact_title) <= max_length:
        return compact_title
    return compact_title[: max_length - 3].rstrip() + "..."


def format_price(price: float | None) -> str:
    if price is None:
        return "s/p"
    return f"{price:,.0f}€".replace(",", ".")


def format_listing(listing: Listing) -> str:
    return f"{shorten_title(listing.title)} | {format_price(listing.price)} | {shorten_url(listing.url)}"


def build_grouped_lines(listings: list[Listing]) -> list[str]:
    grouped: dict[str, list[str]] = {}
    for listing in listings:
        grouped.setdefault(listing.source, []).append(format_listing(listing))

    lines: list[str] = []
    for source in [source.name for source in SOURCES]:
        urls = grouped.get(source)
        if not urls:
            continue

        if lines:
            lines.append("")
        lines.append(f"[{source}]")
        lines.extend(urls)

    return lines


def normalize_message_lines(lines: list[str], max_chars: int) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            if normalized and normalized[-1] != "":
                normalized.append("")
            continue

        normalized.append(cleaned[:max_chars])

    if normalized and normalized[-1] == "":
        normalized.pop()

    return normalized


def build_message_chunks(lines: list[str]) -> list[str]:
    max_chars = int(env_float("MAX_MESSAGE_CHARS", DEFAULT_MAX_MESSAGE_CHARS) or DEFAULT_MAX_MESSAGE_CHARS)
    normalized_lines = normalize_message_lines(lines, max_chars)
    chunks: list[str] = []
    current_chunk = ""

    for line in normalized_lines:
        candidate = line if not current_chunk else f"{current_chunk}\n{line}"
        if current_chunk and len(candidate) > max_chars:
            chunks.append(current_chunk)
            current_chunk = line
            continue

        current_chunk = candidate

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def notify_whatsapp(messages: list[str]) -> bool:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()
    to_number = os.getenv("DESTINO_WHATSAPP_NUMBER", "").strip()

    if not all([account_sid, auth_token, from_number, to_number]):
        logging.warning("Faltan variables de entorno de Twilio. No se enviará WhatsApp.")
        return False

    try:
        client = Client(account_sid, auth_token)
        for message in messages:
            message_response = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number,
            )
            logging.info("Mensaje enviado con SID %s", message_response.sid)
    except TwilioRestException as exc:
        logging.error("Error enviando WhatsApp: %s", exc)
        return False

    return True


def collect_matches() -> list[Listing]:
    session = make_session()
    matches: list[Listing] = []
    for source in SOURCES:
        try:
            scraped = parse_source(session, source)
        except requests.RequestException as exc:
            logging.error("No se pudo leer %s: %s", source.name, exc)
            continue

        matches.extend(item for item in scraped if listing_matches_filters(item))

    return matches


def only_new_matches(listings: list[Listing]) -> list[Listing]:
    if not env_bool("SEND_ONLY_NEW", True):
        return listings

    seen_urls = load_seen_urls()
    return [listing for listing in listings if listing.url not in seen_urls]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_env()

    matches = collect_matches()
    if not matches:
        logging.info("No se encontraron coches que cumplan los filtros.")
        return

    pending = only_new_matches(matches)
    if not pending:
        logging.info("No hay coches nuevos que alertar.")
        return

    limit = int(env_float("MAX_ALERT_ITEMS", 10) or 10)
    selected = pending[:limit]
    grouped_lines = build_grouped_lines(selected)
    messages = build_message_chunks(grouped_lines)

    sent = notify_whatsapp(messages)
    if sent:
        all_seen = load_seen_urls()
        all_seen.update(listing.url for listing in pending)
        save_seen_urls(all_seen)

    if not sent:
        print("\n\n".join(messages))


if __name__ == "__main__":
    main()