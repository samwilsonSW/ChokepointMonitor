# GDELT Ingestion Pipeline

Real-time data ingestion pipeline for GDELT (Global Database of Events, Language, and Tone) conflict events targeting maritime chokepoints.

## Overview

This pipeline fetches conflict event data from Google BigQuery's GDELT 2.0 dataset and stores it in Supabase for the Chokepoint Monitor application. It includes cross-verification with ACLED data for improved accuracy.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ GDELT 2.0   │────▶│ Ingestion    │────▶│ Supabase    │
│ BigQuery    │     │ Pipeline     │     │ PostgreSQL  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                              ┌─────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ ACLED Data      │
                    │ (Cross-verify)  │
                    └─────────────────┘
```

## Setup

### Prerequisites

- Python 3.10+
- Google Cloud service account with BigQuery access
- Supabase project with schema applied

### Installation

```bash
cd pipeline
pip install -r requirements.txt
```

### Environment Variables

Copy the backend `.env` file or create one in the pipeline directory:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# Google Cloud (for BigQuery)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Variable Descriptions:**

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon key or service role key | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | Yes |

## Database Schema

Apply the schema before running the pipeline:

```bash
# Via Supabase SQL Editor or psql
psql $DATABASE_URL -f supabase/schema/gdelt_events.sql
```

Schema includes:
- `gdelt_events` table with spatial/temporal indexes
- `acled_gdelt_links` table for cross-references
- Views for confirmed events and daily summaries

## Usage

### Initial Backfill

Populate historical data (e.g., last 30 days):

```bash
python ingest_gdelt.py --backfill-days 30
```

### Real-time Monitoring

Run every 15 minutes to fetch new events:

```bash
python ingest_gdelt.py --realtime
```

### Cross-Verification

Match GDELT events to ACLED for accuracy:

```bash
python cross_verify.py --days 7 --threshold 0.6
```

### Testing (Limited Events)

```bash
python ingest_gdelt.py --backfill-days 7 --limit 100
```

## Cron Configuration

Example crontab for production:

```bash
# GDELT ingestion every 15 minutes
*/15 * * * * cd /path/to/ChokepointMonitor/pipeline && python ingest_gdelt.py --realtime >> /var/log/gdelt-ingest.log 2>&1

# Daily cross-verification at 2 AM
0 2 * * * cd /path/to/ChokepointMonitor/pipeline && python cross_verify.py --days 1 >> /var/log/gdelt-verify.log 2>&1
```

## Pipeline Components

### `ingest_gdelt.py`

Main ingestion script. Fetches events from BigQuery, transforms them, and upserts to Supabase.

**Features:**
- Bounding box filtering for three chokepoints
- Confidence scoring based on source diversity
- CAMEO conflict code filtering
- Batch upsert for performance

### `cross_verify.py`

Matches GDELT events to ACLED for verification.

**Matching Criteria:**
- Spatial: Within 50km (weight: 35%)
- Temporal: Within 7 days (weight: 30%)
- Actor similarity (weight: 20%)
- Event type mapping (weight: 15%)

### `config.py`

Configuration and client initialization.

**Chokepoints Monitored:**
- Bab al-Mandeb (Yemen/Djibouti/Eritrea)
- Strait of Hormuz (Iran/Oman/UAE)
- Strait of Malacca (Malaysia/Indonesia/Singapore)

## Monitoring

Check ingestion status via Supabase:

```sql
-- Daily event counts by chokepoint
SELECT * FROM v_gdelt_daily_summary;

-- Unverified events needing review
SELECT * FROM gdelt_events 
WHERE verification_status = 'unverified' 
ORDER BY confidence_score DESC;

-- Verification rates
SELECT 
    verification_status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM gdelt_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY verification_status;
```

## Troubleshooting

### BigQuery Access Denied

```bash
# Verify credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
gcloud auth list
```

### Supabase Connection Failed

- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Verify schema has been applied
- Check IP allowlist in Supabase dashboard

### No Events Ingested

- Verify chokepoint bounding boxes in `config.py`
- Check CAMEO codes cover desired event types
- Ensure BigQuery has data for the time range

## Data Retention

Default schema supports rolling retention. To clean old data:

```sql
-- Remove events older than 2 years
DELETE FROM gdelt_events 
WHERE event_date < CURRENT_DATE - INTERVAL '2 years';
```

## Cost Considerations

| Component | Estimated Monthly Cost |
|-----------|----------------------|
| BigQuery (1TB free tier) | $0 (targeted queries) |
| Supabase Pro tier | $25 |
| Compute (small VPS) | $5-10 |
| **Total** | **~$35** |

## License

Same as Chokepoint Monitor project.
