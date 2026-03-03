import csv
import datetime as dt
import os

import yaml

from startup_watch.adapters.a16z import A16zAdapter
from startup_watch.adapters.agdaily import AgdailyAdapter
from startup_watch.adapters.agfunder_news import AgfunderNewsAdapter
from startup_watch.adapters.agfunder import AgfunderAdapter
from startup_watch.adapters.agfunder_pod import AgfunderPodAdapter
from startup_watch.adapters.agriinvestor import AgriinvestorAdapter
from startup_watch.adapters.agweb import AgwebAdapter
from startup_watch.adapters.antler import AntlerAdapter
from startup_watch.adapters.angellist_startups import AngellistStartupsAdapter
from startup_watch.adapters.alchemist import AlchemistAdapter
from startup_watch.adapters.atdc import AtdcAdapter
from startup_watch.adapters.berkeley_skydeck import BerkeleySkydeckAdapter
from startup_watch.adapters.dealroom import DealroomAdapter
from startup_watch.adapters.cornell_tech import CornellTechAdapter
from startup_watch.adapters.climateinsider import ClimateinsiderAdapter
from startup_watch.adapters.crunchbase_news import CrunchbaseNewsAdapter
from startup_watch.adapters.cleanenergywire import CleanenergywireAdapter
from startup_watch.adapters.bessemer import BessemerAdapter
from startup_watch.adapters.supplychaindive import SupplychaindiveAdapter
from startup_watch.adapters.betalist import BetalistAdapter
from startup_watch.adapters.linkedin import LinkedInAdapter
from startup_watch.adapters.industryweek import IndustryweekAdapter
from startup_watch.adapters.iiot_world import IiotWorldAdapter
from startup_watch.adapters.indiehackers import IndiehackersAdapter
from startup_watch.adapters.logisticsmgmt import LogisticsmgmtAdapter
from startup_watch.adapters.mit_deltav import MitDeltavAdapter
from startup_watch.adapters.plugandplay_sc import PlugandplayScAdapter
from startup_watch.adapters.plugandplay_food import PlugandplayFoodAdapter
from startup_watch.adapters.pitchbook_blog import PitchbookBlogAdapter
from startup_watch.adapters.producthunt import ProducthuntAdapter
from startup_watch.adapters.reddit_startups import RedditStartupsAdapter
from startup_watch.adapters.freightwaves import FreightwavesAdapter
from startup_watch.adapters.foodbytes import FoodbytesAdapter
from startup_watch.adapters.gust import GustAdapter
from startup_watch.adapters.fivehundred_global import FivehundredGlobalAdapter
from startup_watch.adapters.hackernews import HackernewsAdapter
from startup_watch.adapters.harvard_ilab import HarvardIlabAdapter
from startup_watch.adapters.eu_startups import EuStartupsAdapter
from startup_watch.adapters.enterprise_ireland import EnterpriseIrelandAdapter
from startup_watch.adapters.eth_pioneer import EthPioneerAdapter
from startup_watch.adapters.eit_food import EitFoodAdapter
from startup_watch.adapters.f6s import F6sAdapter
from startup_watch.adapters.firstround import FirstroundAdapter
from startup_watch.adapters.future_ag import FutureAgAdapter
from startup_watch.adapters.iot_analytics import IotAnalyticsAdapter
from startup_watch.adapters.manufacturing_net import ManufacturingNetAdapter
from startup_watch.adapters.masschallenge import MasschallengeAdapter
from startup_watch.adapters.mfg_dive import MfgDiveAdapter
from startup_watch.adapters.mmh import MmhAdapter
from startup_watch.adapters.owler import OwlerAdapter
from startup_watch.adapters.oxford_foundry import OxfordFoundryAdapter
from startup_watch.adapters.openvc import OpenvcAdapter
from startup_watch.adapters.sequoia import SequoiaAdapter
from startup_watch.adapters.stanford_startx import StanfordStartxAdapter
from startup_watch.adapters.startupstream import StartupStreamAdapter
from startup_watch.adapters.startupland import StartuplandAdapter
from startup_watch.adapters.startup_genome import StartupGenomeAdapter
from startup_watch.adapters.smart_industry import SmartIndustryAdapter
from startup_watch.adapters.skydeck_fund import SkydeckFundAdapter
from startup_watch.adapters.sifted import SiftedAdapter
from startup_watch.adapters.spendmatters import SpendmattersAdapter
from startup_watch.adapters.s2g_companies import S2gCompaniesAdapter
from startup_watch.adapters.seedtable import SeedtableAdapter
from startup_watch.adapters.techcrunch_funding import TechcrunchFundingAdapter
from startup_watch.adapters.tech_eu import TechEuAdapter
from startup_watch.adapters.techstars import TechstarsAdapter
from startup_watch.adapters.techfundingnews import TechfundingnewsAdapter
from startup_watch.adapters.techinasia import TechinasiaAdapter
from startup_watch.adapters.tractica_ai import TracticaAiAdapter
from startup_watch.adapters.siliconcanals import SiliconcanalsAdapter
from startup_watch.adapters.vestbee import VestbeeAdapter
from startup_watch.adapters.startupdaily import StartupdailyAdapter
from startup_watch.adapters.yourstory import YourstoryAdapter
from startup_watch.adapters.builtin import BuiltinAdapter
from startup_watch.adapters.euvc import EuvcAdapter
from startup_watch.adapters.sifted_news import SiftedNewsAdapter
from startup_watch.adapters.unicornnest import UnicornnestAdapter
from startup_watch.adapters.startupnewsfyi import StartupnewsfyiAdapter
from startup_watch.adapters.latitud import LatitudAdapter
from startup_watch.adapters.refreshmiami import RefreshmiamiAdapter
from startup_watch.adapters.geekwire import GeekwireAdapter
from startup_watch.adapters.thenextweb import ThenextwebAdapter
from startup_watch.adapters.e27 import E27Adapter
from startup_watch.adapters.startupbeat import StartupbeatAdapter
from startup_watch.adapters.entrepreneurshiplife import EntrepreneurshiplifeAdapter
from startup_watch.adapters.innovationorigins import InnovationoriginsAdapter
from startup_watch.adapters.startupsmagazine import StartupsmagazineAdapter
from startup_watch.adapters.vccircle import VccircleAdapter
from startup_watch.adapters.techpoint_africa import TechpointAfricaAdapter
from startup_watch.adapters.disruptafrica import DisruptafricaAdapter
from startup_watch.adapters.vested import VestedAdapter
from startup_watch.adapters.therecursive import TherecursiveAdapter
from startup_watch.adapters.supplychainbrain import SupplychainbrainAdapter
from startup_watch.adapters.greenqueen import GreenqueenAdapter
from startup_watch.adapters.finsmes import FinsmesAdapter
from startup_watch.adapters.sustainability_mag import SustainabilityMagAdapter
from startup_watch.adapters.thrive_agtech import ThriveAgtechAdapter
from startup_watch.adapters.therobotreport import TherobotreportAdapter
from startup_watch.adapters.wellfound import WellfoundAdapter
from startup_watch.adapters.venturebeat_ai import VenturebeatAiAdapter
from startup_watch.adapters.uw_comotion import UwComotionAdapter
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
        AgdailyAdapter(config.get("agdaily_adapter", {})),
        StartupStreamAdapter(config.get("startupstream", {})),
        LinkedInAdapter(config.get("linkedin", {})),
        MitDeltavAdapter(config.get("mit_deltav_adapter", {})),
        StanfordStartxAdapter(config.get("stanford_startx_adapter", {})),
        BerkeleySkydeckAdapter(config.get("berkeley_skydeck_adapter", {})),
        CornellTechAdapter(config.get("cornell_tech_adapter", {})),
        HarvardIlabAdapter(config.get("harvard_ilab_adapter", {})),
        OxfordFoundryAdapter(config.get("oxford_foundry_adapter", {})),
        EthPioneerAdapter(config.get("eth_pioneer_adapter", {})),
        UwComotionAdapter(config.get("uw_comotion_adapter", {})),
        AtdcAdapter(config.get("atdc_adapter", {})),
        TechstarsAdapter(config.get("techstars_adapter", {})),
        FivehundredGlobalAdapter(config.get("fivehundred_global_adapter", {})),
        AntlerAdapter(config.get("antler_adapter", {})),
        AlchemistAdapter(config.get("alchemist_adapter", {})),
        MasschallengeAdapter(config.get("masschallenge_adapter", {})),
        PlugandplayFoodAdapter(config.get("plugandplay_food_adapter", {})),
        StartuplandAdapter(config.get("startupland_adapter", {})),
        PlugandplayScAdapter(config.get("plugandplay_sc_adapter", {})),
        ThriveAgtechAdapter(config.get("thrive_agtech_adapter", {})),
        A16zAdapter(config.get("a16z_adapter", {})),
        SequoiaAdapter(config.get("sequoia_adapter", {})),
        BessemerAdapter(config.get("bessemer_adapter", {})),
        FirstroundAdapter(config.get("firstround_adapter", {})),
        SkydeckFundAdapter(config.get("skydeck_fund_adapter", {})),
        S2gCompaniesAdapter(config.get("s2g_companies_adapter", {})),
        DealroomAdapter(config.get("dealroom_adapter", {})),
        F6sAdapter(config.get("f6s_adapter", {})),
        OpenvcAdapter(config.get("openvc_adapter", {})),
        StartupGenomeAdapter(config.get("startup_genome_adapter", {})),
        OwlerAdapter(config.get("owler_adapter", {})),
        CrunchbaseNewsAdapter(config.get("crunchbase_news_adapter", {})),
        GustAdapter(config.get("gust_adapter", {})),
        EnterpriseIrelandAdapter(config.get("enterprise_ireland_adapter", {})),
        TechEuAdapter(config.get("tech_eu_adapter", {})),
        CleanenergywireAdapter(config.get("cleanenergywire_adapter", {})),
        SustainabilityMagAdapter(config.get("sustainability_mag_adapter", {})),
        ClimateinsiderAdapter(config.get("climateinsider_adapter", {})),
        AngellistStartupsAdapter(config.get("angellist_startups_adapter", {})),
        EuStartupsAdapter(config.get("eu_startups_adapter", {})),
        FutureAgAdapter(config.get("future_ag_adapter", {})),
        PitchbookBlogAdapter(config.get("pitchbook_blog_adapter", {})),
        SiftedAdapter(config.get("sifted_adapter", {})),
        AgriinvestorAdapter(config.get("agriinvestor_adapter", {})),
        SeedtableAdapter(config.get("seedtable_adapter", {})),
        TracticaAiAdapter(config.get("tractica_ai_adapter", {})),
        IiotWorldAdapter(config.get("iiot_world_adapter", {})),
        HackernewsAdapter(config.get("hackernews_adapter", {})),
        RedditStartupsAdapter(config.get("reddit_startups_adapter", {})),
        IndiehackersAdapter(config.get("indiehackers_adapter", {})),
        TechcrunchFundingAdapter(config.get("techcrunch_funding_adapter", {})),
        AgfunderNewsAdapter(config.get("agfunder_news_adapter", {})),
        AgfunderAdapter(config.get("agfunder_adapter", {})),
        EitFoodAdapter(config.get("eit_food_adapter", {})),
        FoodbytesAdapter(config.get("foodbytes_adapter", {})),
        AgfunderPodAdapter(config.get("agfunder_pod_adapter", {})),
        AgwebAdapter(config.get("agweb_adapter", {})),
        IndustryweekAdapter(config.get("industryweek_adapter", {})),
        FreightwavesAdapter(config.get("freightwaves_adapter", {})),
        WellfoundAdapter(config.get("wellfound_adapter", {})),
        BetalistAdapter(config.get("betalist_adapter", {})),
        ProducthuntAdapter(config.get("producthunt_adapter", {})),
        SpendmattersAdapter(config.get("spendmatters_adapter", {})),
        SmartIndustryAdapter(config.get("smart_industry_adapter", {})),
        IotAnalyticsAdapter(config.get("iot_analytics_adapter", {})),
        ManufacturingNetAdapter(config.get("manufacturing_net_adapter", {})),
        MfgDiveAdapter(config.get("mfg_dive_adapter", {})),
        MmhAdapter(config.get("mmh_adapter", {})),
        LogisticsmgmtAdapter(config.get("logisticsmgmt_adapter", {})),
        SupplychaindiveAdapter(config.get("supplychaindive_adapter", {})),
        TherobotreportAdapter(config.get("therobotreport_adapter", {})),
        VenturebeatAiAdapter(config.get("venturebeat_ai_adapter", {})),
        SupplychainbrainAdapter(config.get("supplychainbrain_adapter", {})),
        TechfundingnewsAdapter(config.get("techfundingnews_adapter", {})),
        GreenqueenAdapter(config.get("greenqueen_adapter", {})),
        FinsmesAdapter(config.get("finsmes_adapter", {})),
        SiliconcanalsAdapter(config.get("siliconcanals_adapter", {})),
        VestbeeAdapter(config.get("vestbee_adapter", {})),
        StartupdailyAdapter(config.get("startupdaily_adapter", {})),
        TechinasiaAdapter(config.get("techinasia_adapter", {})),
        YourstoryAdapter(config.get("yourstory_adapter", {})),
        BuiltinAdapter(config.get("builtin_adapter", {})),
        EuvcAdapter(config.get("euvc_adapter", {})),
        SiftedNewsAdapter(config.get("sifted_news_adapter", {})),
        UnicornnestAdapter(config.get("unicornnest_adapter", {})),
        StartupnewsfyiAdapter(config.get("startupnewsfyi_adapter", {})),
        LatitudAdapter(config.get("latitud_adapter", {})),
        RefreshmiamiAdapter(config.get("refreshmiami_adapter", {})),
        GeekwireAdapter(config.get("geekwire_adapter", {})),
        ThenextwebAdapter(config.get("thenextweb_adapter", {})),
        E27Adapter(config.get("e27_adapter", {})),
        StartupbeatAdapter(config.get("startupbeat_adapter", {})),
        EntrepreneurshiplifeAdapter(config.get("entrepreneurshiplife_adapter", {})),
        InnovationoriginsAdapter(config.get("innovationorigins_adapter", {})),
        StartupsmagazineAdapter(config.get("startupsmagazine_adapter", {})),
        VccircleAdapter(config.get("vccircle_adapter", {})),
        TechpointAfricaAdapter(config.get("techpoint_africa_adapter", {})),
        DisruptafricaAdapter(config.get("disruptafrica_adapter", {})),
        VestedAdapter(config.get("vested_adapter", {})),
        TherecursiveAdapter(config.get("therecursive_adapter", {})),
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
