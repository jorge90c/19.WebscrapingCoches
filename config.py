from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    max_price: float = 10000
    max_monthly_payment: float = 200
    exclude_keywords: tuple[str, ...] = ("puretech",)
    send_only_new: bool = True
    max_alert_items: int = 10
    max_message_chars: int = 1400
    request_timeout: int = 20
    flexicar_province: str = "madrid"


APP_CONFIG = AppConfig()


def build_source_urls(config: AppConfig) -> dict[str, str]:
    max_price = int(config.max_price)
    max_monthly_payment = int(config.max_monthly_payment)
    return {
        "Autohero": (
            "https://www.autohero.com/es/search/"
            f"?sort=financed_price_asc&priceType=fixed&priceMax={max_price}&transmission=automatic"
        ),
        "Clicars": (
            "https://www.clicars.com/coches-segunda-mano-ocasion/automatico"
            f"?order=price.asc&priceMax={max_price}&financingMax={max_monthly_payment}"
        ),
        "OcasionPlus": (
            "https://www.ocasionplus.com/coches-segunda-mano"
            f"?v2&orderBy=lowerPrice&cuote%5Bto%5D={max_monthly_payment}&transmission=AUTO"
        ),
        "Flexicar": (
            "https://www.flexicar.es/coches-segunda-mano/search/"
            f"?priceTo={max_price}&transmission=automatica&sortBy=price&order=ASC"
            f"&province={config.flexicar_province}&quotaTo={max_monthly_payment}"
        ),
    }