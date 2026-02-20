"""
Cross-verification module for matching GDELT events to ACLED events.
Uses temporal, spatial, and actor similarity scoring.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher

from supabase import Client

from config import get_supabase_client, CAMEO_TO_ACLED_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def haversine_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_actor_similarity(actor1: Optional[str], actor2: Optional[str]) -> float:
    """
    Calculate string similarity between actor names.
    
    Args:
        actor1: First actor name
        actor2: Second actor name
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not actor1 or not actor2:
        return 0.0
    
    a1 = actor1.lower().strip()
    a2 = actor2.lower().strip()
    
    if a1 == a2:
        return 1.0
    
    # Check for substring matches
    if a1 in a2 or a2 in a1:
        return 0.8
    
    # Token-based matching for multi-word names
    tokens1 = set(a1.split())
    tokens2 = set(a2.split())
    
    if tokens1 and tokens2:
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        jaccard = len(intersection) / len(union) if union else 0
        if jaccard > 0.5:
            return 0.7
    
    # Sequence matcher for fuzzy matching
    return SequenceMatcher(None, a1, a2).ratio()


def compare_event_types(
    cameo_code: Optional[str], 
    acled_event_type: Optional[str]
) -> float:
    """
    Compare CAMEO event code to ACLED event type.
    
    Args:
        cameo_code: GDELT CAMEO event code
        acled_event_type: ACLED event type string
    
    Returns:
        Match score between 0.0 and 1.0
    """
    if not cameo_code or not acled_event_type:
        return 0.0
    
    acled_type_lower = acled_event_type.lower()
    
    # Direct mapping lookup
    for code_range, acled_category in CAMEO_TO_ACLED_MAPPING.items():
        if '-' in code_range:
            start, end = code_range.split('-')
            if start <= cameo_code <= end:
                if acled_category.lower() in acled_type_lower:
                    return 1.0
                return 0.3
        else:
            if cameo_code.startswith(code_range):
                if acled_category.lower() in acled_type_lower:
                    return 1.0
                return 0.3
    
    return 0.0


def score_temporal_proximity(
    gdelt_date: datetime, 
    acled_date: datetime,
    max_days: int = 7
) -> float:
    """
    Score temporal proximity between two events.
    
    Args:
        gdelt_date: GDELT event date
        acled_date: ACLED event date
        max_days: Maximum days for scoring window
    
    Returns:
        Score between 0.0 and 1.0
    """
    if isinstance(gdelt_date, str):
        gdelt_date = datetime.fromisoformat(gdelt_date.replace('Z', '+00:00'))
    if isinstance(acled_date, str):
        acled_date = datetime.fromisoformat(acled_date.replace('Z', '+00:00'))
    
    date_diff = abs((gdelt_date - acled_date).days)
    
    if date_diff > max_days:
        return 0.0
    
    return 1 - (date_diff / max_days)


def score_spatial_proximity(
    gdelt_lat: float,
    gdelt_lon: float,
    acled_lat: float,
    acled_lon: float,
    max_km: float = 50.0
) -> float:
    """
    Score spatial proximity between two events.
    
    Args:
        gdelt_lat, gdelt_lon: GDELT event coordinates
        acled_lat, acled_lon: ACLED event coordinates
        max_km: Maximum distance for scoring in km
    
    Returns:
        Score between 0.0 and 1.0
    """
    distance = haversine_distance(gdelt_lat, gdelt_lon, acled_lat, acled_lon)
    
    if distance > max_km:
        return 0.0
    
    return 1 - (distance / max_km)


def calculate_match_confidence(
    temporal_score: float,
    spatial_score: float,
    actor_score: float,
    event_type_score: float
) -> float:
    """
    Calculate weighted confidence score.
    
    Weights:
    - Spatial: 35%
    - Temporal: 30%
    - Actor: 20%
    - Event type: 15%
    
    Returns:
        Weighted confidence between 0.0 and 1.0
    """
    return round(
        spatial_score * 0.35 +
        temporal_score * 0.30 +
        actor_score * 0.20 +
        event_type_score * 0.15,
        3
    )


def cross_verify_event(
    gdelt_event: Dict[str, Any],
    acled_events: List[Dict[str, Any]],
    time_window_days: int = 7,
    distance_km: float = 50.0,
    confidence_threshold: float = 0.6
) -> Tuple[bool, float, Optional[int], Optional[Dict[str, float]]]:
    """
    Match a GDELT event against ACLED events.
    
    Args:
        gdelt_event: GDELT event record
        acled_events: List of ACLED events to compare against
        time_window_days: Maximum days difference for matching
        distance_km: Maximum distance in km for matching
        confidence_threshold: Minimum confidence for a match
    
    Returns:
        Tuple of (match_found, confidence_score, acled_event_id, match_details)
    """
    gdelt_lat = gdelt_event.get('latitude')
    gdelt_lon = gdelt_event.get('longitude')
    gdelt_date = gdelt_event.get('event_date')
    gdelt_actor1 = gdelt_event.get('actor1_name')
    gdelt_actor2 = gdelt_event.get('actor2_name')
    cameo_code = gdelt_event.get('event_code') or gdelt_event.get('event_base_code')
    
    if not all([gdelt_lat, gdelt_lon, gdelt_date]):
        return False, 0.0, None, None
    
    potential_matches = []
    
    for acled in acled_events:
        acled_lat = acled.get('latitude')
        acled_lon = acled.get('longitude')
        acled_date = acled.get('event_date')
        acled_actor1 = acled.get('actor1')
        acled_actor2 = acled.get('actor2')
        acled_event_type = acled.get('event_type')
        
        if not all([acled_lat, acled_lon, acled_date]):
            continue
        
        scores = {}
        
        # Temporal scoring
        scores['temporal'] = score_temporal_proximity(
            gdelt_date, acled_date, time_window_days
        )
        if scores['temporal'] == 0:
            continue
        
        # Spatial scoring
        scores['spatial'] = score_spatial_proximity(
            gdelt_lat, gdelt_lon, acled_lat, acled_lon, distance_km
        )
        if scores['spatial'] == 0:
            continue
        
        # Actor scoring (best match between any actor combination)
        actor_scores = []
        if gdelt_actor1 and acled_actor1:
            actor_scores.append(calculate_actor_similarity(gdelt_actor1, acled_actor1))
        if gdelt_actor1 and acled_actor2:
            actor_scores.append(calculate_actor_similarity(gdelt_actor1, acled_actor2))
        if gdelt_actor2 and acled_actor1:
            actor_scores.append(calculate_actor_similarity(gdelt_actor2, acled_actor1))
        if gdelt_actor2 and acled_actor2:
            actor_scores.append(calculate_actor_similarity(gdelt_actor2, acled_actor2))
        
        scores['actor'] = max(actor_scores) if actor_scores else 0.0
        
        # Event type scoring
        scores['event_type'] = compare_event_types(cameo_code, acled_event_type)
        
        # Calculate weighted confidence
        confidence = calculate_match_confidence(
            scores['temporal'],
            scores['spatial'],
            scores['actor'],
            scores['event_type']
        )
        
        if confidence >= confidence_threshold:
            potential_matches.append({
                'acled_id': acled.get('event_id'),
                'confidence': confidence,
                'scores': scores
            })
    
    if potential_matches:
        best_match = max(potential_matches, key=lambda x: x['confidence'])
        return (
            True,
            best_match['confidence'],
            best_match['acled_id'],
            best_match['scores']
        )
    
    return False, 0.0, None, None


def fetch_unverified_gdelt_events(
    supabase: Client,
    days_back: int = 7,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetch GDELT events that haven't been cross-verified."""
    since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    
    query = supabase.table('gdelt_events')\
        .select('*')\
        .is_('acled_event_id', 'null')\
        .gte('event_date', since_date)\
        .not_.eq('verification_status', 'false_positive')\
        .order('event_date', desc=True)
    
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    return response.data or []


def fetch_acled_events_for_region(
    supabase: Client,
    chokepoint_region: str,
    days_back: int = 14
) -> List[Dict[str, Any]]:
    """Fetch ACLED events for a specific chokepoint region."""
    since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    
    response = supabase.table('acled_events')\
        .select('*')\
        .eq('chokepoint_region', chokepoint_region)\
        .gte('event_date', since_date)\
        .execute()
    
    return response.data or []


def update_gdelt_verification(
    supabase: Client,
    gdelt_event_id: int,
    acled_event_id: int,
    confidence: float,
    match_details: Dict[str, float]
) -> bool:
    """Update GDELT event with verification info and create link record."""
    try:
        # Update the GDELT event
        supabase.table('gdelt_events').update({
            'acled_event_id': acled_event_id,
            'verification_status': 'verified' if confidence >= 0.8 else 'likely',
            'confidence_score': confidence,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('gdelt_event_id', gdelt_event_id).execute()
        
        # Create link record
        supabase.table('acled_gdelt_links').upsert({
            'gdelt_event_id': gdelt_event_id,
            'acled_event_id': acled_event_id,
            'match_score': confidence,
            'match_method': 'spatial_temporal_actor',
            'match_details': match_details
        }, on_conflict='gdelt_event_id,acled_event_id').execute()
        
        return True
    except Exception as e:
        logger.error(f"Failed to update verification: {e}")
        return False


def cross_verify_events(
    supabase: Optional[Client] = None,
    days_back: int = 7,
    confidence_threshold: float = 0.6,
    batch_size: int = 100
) -> Dict[str, int]:
    """
    Run cross-verification on recent GDELT events.
    
    Args:
        supabase: Supabase client (created if not provided)
        days_back: Days of GDELT events to verify
        confidence_threshold: Minimum match confidence
        batch_size: Events to process per batch
    
    Returns:
        Stats dict with counts
    """
    if supabase is None:
        supabase = get_supabase_client()
    
    logger.info(f"Starting cross-verification for last {days_back} days")
    
    # Fetch unverified GDELT events
    gdelt_events = fetch_unverified_gdelt_events(supabase, days_back, batch_size)
    logger.info(f"Found {len(gdelt_events)} unverified events")
    
    if not gdelt_events:
        return {'processed': 0, 'matched': 0, 'failed': 0}
    
    # Group by chokepoint for efficient ACLED fetching
    events_by_region = {}
    for event in gdelt_events:
        region = event.get('chokepoint_region')
        if region:
            events_by_region.setdefault(region, []).append(event)
    
    stats = {'processed': 0, 'matched': 0, 'failed': 0}
    
    for region, events in events_by_region.items():
        logger.info(f"Processing {len(events)} events in {region}")
        
        # Fetch ACLED events for this region
        acled_events = fetch_acled_events_for_region(supabase, region, days_back + 7)
        logger.info(f"Found {len(acled_events)} ACLED events in {region}")
        
        if not acled_events:
            continue
        
        for gdelt_event in events:
            stats['processed'] += 1
            
            match_found, confidence, acled_id, details = cross_verify_event(
                gdelt_event,
                acled_events,
                confidence_threshold=confidence_threshold
            )
            
            if match_found and acled_id:
                success = update_gdelt_verification(
                    supabase,
                    gdelt_event['gdelt_event_id'],
                    acled_id,
                    confidence,
                    details
                )
                if success:
                    stats['matched'] += 1
                    logger.info(
                        f"Matched GDELT {gdelt_event['gdelt_event_id']} to "
                        f"ACLED {acled_id} (confidence: {confidence})"
                    )
                else:
                    stats['failed'] += 1
    
    logger.info(f"Verification complete: {stats}")
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Cross-verify GDELT with ACLED')
    parser.add_argument('--days', type=int, default=7, help='Days to look back')
    parser.add_argument('--threshold', type=float, default=0.6, help='Confidence threshold')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    
    args = parser.parse_args()
    
    stats = cross_verify_events(
        days_back=args.days,
        confidence_threshold=args.threshold,
        batch_size=args.batch_size
    )
    
    print(f"Results: {stats}")
