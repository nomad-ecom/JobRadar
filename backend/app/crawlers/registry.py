from collections.abc import Callable

from app.config import Settings
from app.crawlers.linkedin import collect_linkedin
from app.crawlers.sample import collect_sample
from app.crawlers.topcv import collect_topcv
from app.crawlers.types import CrawlResult
from app.crawlers.vietnamworks import collect_vietnamworks

Collector = Callable[..., CrawlResult]

COLLECTORS: dict[str, Collector] = {
    "vietnamworks": collect_vietnamworks,
    "topcv": collect_topcv,
    "linkedin": collect_linkedin,
    "sample": collect_sample,
}

REAL_SOURCES = ["vietnamworks", "topcv", "linkedin"]


def sources_for(settings: Settings) -> list[str]:
    sources = list(REAL_SOURCES)
    if settings.sample_source:
        sources.append("sample")
    return sources
