"""
GDELT to Supabase ingestion pipeline.
Fetches real-time conflict events from BigQuery and stores in Supabase.

- Find out when we last fetched data.
- Ask BigQuery for new conflict events in the chokepoints.
- Clean & - Transform the raw data and decide how much we trust it.
- Push the cleaned data into Supabase.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Iterator, Optional, Dict, Any, List
from decimal import Decimal

from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from supabase import Client
from ..supabase_client import _get_client
from backend.gdelt_pipeline.config import CHOKEPOINTS, CONFLICT_CODES, get_bigquery_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_chokepoint_where_clause() -> str:
    """Build SQL WHERE clause for chokepoint bounding boxes."""
    conditions = []
    for name, bounds in CHOKEPOINTS.items():
        condition = (
            f"(e.ActionGeo_Lat BETWEEN {bounds['lat_min']} AND {bounds['lat_max']} "
            f"AND e.ActionGeo_Long BETWEEN {bounds['lon_min']} AND {bounds['lon_max']})"
        )
        conditions.append(condition)
    return " OR ".join(conditions)


def fetch_gdelt_events(
    bq_client: bigquery.Client,
    since_datetime: datetime,
    limit: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Query BigQuery for GDELT events within chokepoint regions.
    
    Args:
        bq_client: Initialized BigQuery client
        since_datetime: Fetch events from this timestamp
        limit: Optional row limit for testing
    
    Yields:
        Dict containing event data from GDELT
    """
    date_str = since_datetime.strftime('%Y%m%d')
    chokepoint_clause = build_chokepoint_where_clause()
    conflict_codes_str = ', '.join(f"'{code}'" for code in CONFLICT_CODES)
    
    query = f"""
    SELECT
        e.GLOBALEVENTID as event_id,
        e.SQLDATE as event_date,
        e.ActionGeo_Lat as latitude,
        e.ActionGeo_Long as longitude,
        e.ActionGeo_FeatureID as geo_feature_id,
        e.ActionGeo_CountryCode as country_code,
        e.ActionGeo_ADM1Code as admin1_code,
        e.EventRootCode as root_code,
        e.EventBaseCode as base_code,
        e.EventCode as event_code,
        e.Actor1Code as actor1_code,
        e.Actor1Name as actor1_name,
        e.Actor1CountryCode as actor1_country_code,
        e.Actor1Type1Code as actor1_type_code,
        e.Actor2Code as actor2_code,
        e.Actor2Name as actor2_name,
        e.Actor2CountryCode as actor2_country_code,
        e.Actor2Type1Code as actor2_type_code,
        e.GoldsteinScale as goldstein_scale,
        e.QuadClass as quad_class,
        e.NumMentions as num_mentions,
        e.NumSources as num_sources,
        e.NumArticles as num_articles,
        e.SOURCEURL as source_url,
        m.AvgTone as tone_score,
        m.PositiveScore as positive_score,
        m.NegativeScore as negative_score,
        m.Polarity as polarity,
        m.ActivityReferenceDensity as activity_ref_density,
        m.SelfGroupReferenceDensity as self_group_ref_density,
        m.WordCount as word_count
    FROM `gdelt-bq.gdeltv2.events` e
    LEFT JOIN (
        SELECT 
            GLOBALEVENTID,
            AVG(AvgTone) as AvgTone,
            AVG(PositiveScore) as PositiveScore,
            AVG(NegativeScore) as NegativeScore,
            AVG(Polarity) as Polarity,
            AVG(ActivityReferenceDensity) as ActivityReferenceDensity,
            AVG(SelfGroupReferenceDensity) as SelfGroupReferenceDensity,
            AVG(WordCount) as WordCount
        FROM `gdelt-bq.gdeltv2.eventmentions`
        WHERE MentionTimeDate >= '{date_str}'
        GROUP BY GLOBALEVENTID
    ) m ON e.GLOBALEVENTID = m.GLOBALEVENTID
    WHERE e.SQLDATE >= {date_str}
        AND e.ActionGeo_Lat IS NOT NULL
        AND e.ActionGeo_Long IS NOT NULL
        AND ({chokepoint_clause})
        AND e.EventRootCode IN ({conflict_codes_str})
    ORDER BY e.SQLDATE DESC, e.GLOBALEVENTID DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    try:
        query_job = bq_client.query(query)
        for row in query_job.result():
            yield dict(row.items())
    except GoogleAPIError as e:
        logger.error(f"BigQuery error: {e}")
        raise


def classify_chokepoint(lat: float, lon: float) -> Optional[str]:
    """
    Determine which chokepoint region coordinates belong to.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Chokepoint name or None if outside all regions
    """
    for name, bounds in CHOKEPOINTS.items():
        if (bounds['lat_min'] <= lat <= bounds['lat_max'] and
            bounds['lon_min'] <= lon <= bounds['lon_max']):
            return name
    return None


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from source URL."""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '') if parsed.netloc else None
    except Exception:
        return None


def calculate_confidence(event: Dict[str, Any]) -> float:
    """
    Calculate confidence score based on source diversity, mentions, and tone.
    
    Scoring weights:
    - Source diversity: 40%
    - Mention volume: 30%
    - Tone variance: 20%
    - Goldstein scale alignment: 10%
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    mentions = event.get('num_mentions') or 0
    sources = event.get('num_sources') or 0
    articles = event.get('num_articles') or 0
    tone = event.get('tone_score') or 0
    goldstein = event.get('goldstein_scale') or 0
    
    mentions_score = min(mentions / 10, 1.0)
    sources_score = min(sources / 3, 1.0)
    articles_score = min(articles / 5, 1.0)
    diversity_score = (sources_score * 0.6 + articles_score * 0.4)
    
    tone_variance = min(abs(tone) / 10, 1.0)
    
    goldstein_score = 0.5
    if goldstein < -5:
        goldstein_score = 0.8
    elif goldstein < 0:
        goldstein_score = 0.6
    elif goldstein > 0:
        goldstein_score = 0.4
    
    confidence = (
        diversity_score * 0.40 +
        mentions_score * 0.30 +
        tone_variance * 0.20 +
        goldstein_score * 0.10
    )
    
    return round(min(max(confidence, 0.0), 1.0), 3)


def determine_verification_status(confidence: float) -> str:
    """Map confidence score to verification status."""
    if confidence >= 0.8:
        return 'verified'
    elif confidence >= 0.5:
        return 'likely'
    elif confidence >= 0.3:
        return 'unverified'
    else:
        return 'false_positive'


def transform_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transform BigQuery row into Supabase record format.
    
    Args:
        event: Raw GDELT event from BigQuery
    
    Returns:
        Transformed record or None if outside chokepoints
    """
    lat = event.get('latitude')
    lon = event.get('longitude')
    
    if lat is None or lon is None:
        return None
    
    chokepoint = classify_chokepoint(lat, lon)
    if not chokepoint:
        return None
    
    confidence = calculate_confidence(event)
    event_date = event.get('event_date')
    
    if isinstance(event_date, int):
        event_date = datetime.strptime(str(event_date), '%Y%m%d').date()
    elif isinstance(event_date, str):
        event_date = datetime.strptime(event_date, '%Y%m%d').date()
    
    return {
        'gdelt_event_id': event.get('event_id'),
        'event_date': event_date.isoformat() if event_date else None,
        'latitude': lat,
        'longitude': lon,
        'geo_precision': event.get('geo_precision'),
        'country_code': event.get('country_code'),
        'admin1_code': event.get('admin1_code'),
        'event_root_code': event.get('root_code'),
        'event_base_code': event.get('base_code'),
        'event_code': event.get('event_code'),
        'actor1_code': event.get('actor1_code'),
        'actor1_name': event.get('actor1_name'),
        'actor1_country_code': event.get('actor1_country_code'),
        'actor1_type_code': event.get('actor1_type_code'),
        'actor2_code': event.get('actor2_code'),
        'actor2_name': event.get('actor2_name'),
        'actor2_country_code': event.get('actor2_country_code'),
        'actor2_type_code': event.get('actor2_type_code'),
        'tone_score': event.get('tone_score'),
        'positive_score': event.get('positive_score'),
        'negative_score': event.get('negative_score'),
        'polarity': event.get('polarity'),
        'activity_reference_density': event.get('activity_ref_density'),
        'self_group_reference_density': event.get('self_group_ref_density'),
        'word_count': event.get('word_count'),
        'source_url': event.get('source_url'),
        'source_domain': extract_domain(event.get('source_url')),
        'num_mentions': event.get('num_mentions') or 0,
        'num_sources': event.get('num_sources') or 0,
        'num_articles': event.get('num_articles') or 0,
        'verification_status': determine_verification_status(confidence),
        'confidence_score': confidence,
        'chokepoint_region': chokepoint,
        'is_maritime': chokepoint in ['bab_al_mandeb', 'hormuz', 'malacca'],
        'goldstein_scale': event.get('goldstein_scale'),
        'quad_class': event.get('quad_class'),
        'raw_gdelt_data': event
    }


def ingest_to_supabase(
    supabase: Client,
    events: List[Dict[str, Any]],
    batch_size: int = 100
) -> int:
    """
    Upsert events to Supabase in batches.
    
    Args:
        supabase: Initialized Supabase client
        events: List of transformed event records
        batch_size: Number of records per batch
    
    Returns:
        Number of records ingested
    """
    if not events:
        return 0
    
    ingested = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        
        try:
            response = supabase.table('gdelt_events').upsert(
                batch,
                on_conflict='gdelt_event_id'
            ).execute()
            
            if response.data:
                ingested += len(response.data)
                logger.info(f"Upserted batch of {len(response.data)} events")
            
        except Exception as e:
            logger.error(f"Supabase upsert error: {e}")
            raise
    
    return ingested


def get_last_fetch_time(supabase: Client) -> datetime:
    """
    Get the timestamp of the most recent event in the database.
    Returns a default of 24 hours ago if no events exist.
    """
    try:
        response = supabase.table('gdelt_events')\
            .select('event_date')\
            .order('event_date', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data:
            last_date = response.data[0]['event_date']
            if isinstance(last_date, str):
                return datetime.fromisoformat(last_date.replace('Z', '+00:00'))
            return last_date
    except Exception as e:
        logger.warning(f"Could not get last fetch time: {e}")
    
    return datetime.utcnow() - timedelta(hours=24)


def main(
    backfill_days: Optional[int] = None,
    realtime: bool = False,
    limit: Optional[int] = None
) -> int:
    """
    Main ingestion orchestrator.
    
    Args:
        backfill_days: Number of days to backfill (for initial load)
        realtime: If True, only fetch since last event
        limit: Maximum events to fetch (for testing)
    
    Returns:
        Number of events ingested
    """
    logger.info("Initializing GDELT ingestion pipeline")
    
    bq_client = get_bigquery_client()
    supabase = _get_client()
    
    if backfill_days:
        since = datetime.utcnow() - timedelta(days=backfill_days)
        logger.info(f"Backfilling {backfill_days} days from {since}")
    elif realtime:
        since = get_last_fetch_time(supabase)
        logger.info(f"Realtime mode: fetching since {since}")
    else:
        since = datetime.utcnow() - timedelta(hours=24)
        logger.info(f"Default mode: fetching last 24 hours from {since}")
    
    logger.info("Fetching events from BigQuery...")
    events_iter = fetch_gdelt_events(bq_client, since, limit)
    
    records = []
    for event in events_iter:
        transformed = transform_event(event)
        if transformed:
            records.append(transformed)
    
    logger.info(f"Transformed {len(records)} events for ingestion")
    



    #Testing output
    print(records)
    return records



    #UNCOMMENT FOR SUPABSE UPLOAD

    # if records:
    #     count = ingest_to_supabase(supabase, records)
    #     logger.info(f"Successfully ingested {count} events")
    #     return count
    
    # logger.info("No events to ingest")
    # return 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='GDELT to Supabase ingestion')
    parser.add_argument('--backfill-days', type=int, help='Days to backfill')
    parser.add_argument('--realtime', action='store_true', help='Realtime mode')
    parser.add_argument('--limit', type=int, help='Limit events (for testing)')
    
    args = parser.parse_args()
    main(
        backfill_days=args.backfill_days,
        realtime=args.realtime,
        limit=args.limit
    )
