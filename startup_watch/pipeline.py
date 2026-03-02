import csv
import datetime as dt
import os

import yaml

from startup_watch.adapters.a16z import A16zAdapter
from startup_watch.adapters.agfunder_news import AgfunderNewsAdapter
from startup_watch.adapters.alchemist import AlchemistAdapter
from startup_watch.adapters.berkeley_skydeck import BerkeleySkydeckAdapter
from startup_watch.adapters.bessemer import BessemerAdapter
from startup_watch.adapters.betalist import BetalistAdapter
from startup_watch.adapters.linkedin import LinkedInAdapter
from startup_watch.adapters.mit_deltav import MitDeltavAdapter
from startup_watch.adapters.plugandplay_sc import PlugandplayScAdapter
from startup_watch.adapters.producthunt import ProducthuntAdapter
from startup_watch.adapters.freightwaves import FreightwavesAdapter
from startup_watch.adapters.iot_analytics import IotAnalyticsAdapter
from startup_watch.adapters.sequoia import SequoiaAdapter
from startup_watch.adapters.stanford_startx import StanfordStartxAdapter
from startup_watch.adapters.startupstream import StartupStreamAdapter
from startup_watch.adapters.smart_industry import SmartIndustryAdapter
from startup_watch.adapters.spendmatters import SpendmattersAdapter
from startup_watch.adapters.techcrunch_funding import TechcrunchFundingAdapter
from startup_watch.adapters.thrive_agtech import ThriveAgtechAdapter
from startup_watch.adapters.wellfound import WellfoundAdapter
from startup_watch.adapters.yc import YCombinatorAdapter
from startup_watch.dedup import deduplicate_signals
from startup_watch.enrichment import enrich_batch
from startup_watch.filters import filter_by_category, filter_by_stage, filter_excluded
from startup_watch.logger import get_logger
from startup_watch.schema import StartupSignal


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def collect_signals(config: dict) -> list[StartupSignal]:
    logger = get_logger()
    adapters = [
        YCombinatorAdapter(config.get("yc_directory", {})),
        StartupStreamAdapter(config.get("startupstream", {})),
        LinkedInAdapter(config.get("linkedin", {})),
        MitDeltavAdapter(config.get("mit_deltav_adapter", {})),
        StanfordStartxAdapter(config.get("stanford_startx_adapter", {})),
        BerkeleySkydeckAdapter(config.get("berkeley_skydeck_adapter", {})),
        AlchemistAdapter(config.get("alchemist_adapter", {})),
        PlugandplayScAdapter(config.get("plugandplay_sc_adapter", {})),
        ThriveAgtechAdapter(config.get("thrive_agtech_adapter", {})),
        A16zAdapter(config.get("a16z_adapter", {})),
        SequoiaAdapter(config.get("sequoia_adapter", {})),
        BessemerAdapter(config.get("bessemer_adapter", {})),
        TechcrunchFundingAdapter(config.get("techcrunch_funding_adapter", {})),
        AgfunderNewsAdapter(config.get("agfunder_news_adapter", {})),
        FreightwavesAdapter(config.get("freightwaves_adapter", {})),
        WellfoundAdapter(config.get("wellfound_adapter", {})),
        BetalistAdapter(config.get("betalist_adapter", {})),
        ProducthuntAdapter(config.get("producthunt_adapter", {})),
        SpendmattersAdapter(config.get("spendmatters_adapter", {})),
        SmartIndustryAdapter(config.get("smart_industry_adapter", {})),
        IotAnalyticsAdapter(config.get("iot_analytics_adapter", {})),
    ]
    collected: list[StartupSignal] = []
    for adapter in adapters:
        batch = adapter.fetch()
        logger.info("adapter=%s signals=%s", adapter.source_name, len(batch))
        collected.extend(batch)
    return collected


def run_pipeline(config: dict) -> list[StartupSignal]:
    signals = collect_signals(config)
    signals = filter_excluded(signals, config.get("filters", {}).get("exclude_companies", []))
    signals = filter_by_category(signals, config.get("categories", []))
    signals = filter_by_stage(signals, config.get("stages", []))
    signals = enrich_batch(signals)
    signals = deduplicate_signals(signals)
    return [s.normalize() for s in signals]


def write_csv(signals: list[StartupSignal], output_dir: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/startup_watch_{timestamp}.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "company_name",
            "website",
            "description",
            "stage",
            "categories",
            "source_name",
            "source_url",
            "scraped_at",
            "founders",
            "linkedin_url",
            "location",
            "funding_amount",
            "investor_names",
            "notes",
            "headcount_range",
            "total_raised",
            "investor_tier",
        ])
        for signal in signals:
            writer.writerow([
                signal.company_name,
                signal.website,
                signal.description,
                signal.stage,
                "|".join(signal.categories),
                signal.source_name,
                signal.source_url,
                signal.scraped_at,
                "|".join(signal.founders),
                signal.linkedin_url,
                signal.location,
                signal.funding_amount,
                "|".join(signal.investor_names),
                signal.notes,
                signal.headcount_range,
                signal.total_raised,
                signal.investor_tier,
            ])
    return path
