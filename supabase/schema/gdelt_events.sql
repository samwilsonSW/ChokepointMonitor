-- GDELT Events Table for Chokepoint Monitor
-- Stores real-time conflict events from GDELT BigQuery dataset

CREATE TABLE IF NOT EXISTS gdelt_events (
    id BIGSERIAL PRIMARY KEY,
    gdelt_event_id BIGINT UNIQUE NOT NULL,
    
    -- Temporal fields
    event_date DATE NOT NULL,
    event_timestamp TIMESTAMP,
    
    -- Spatial fields (chokepoint focus)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    geo_precision INTEGER,
    country_code CHAR(2),
    admin1_code VARCHAR(10),
    
    -- Event classification (CAMEO codes)
    event_root_code VARCHAR(2),
    event_base_code VARCHAR(3),
    event_code VARCHAR(4),
    event_description TEXT,
    
    -- Actors
    actor1_code VARCHAR(50),
    actor1_name VARCHAR(255),
    actor1_country_code CHAR(2),
    actor1_type_code VARCHAR(3),
    actor2_code VARCHAR(50),
    actor2_name VARCHAR(255),
    actor2_country_code CHAR(2),
    actor2_type_code VARCHAR(3),
    
    -- Tone/Sentiment analysis
    tone_score DECIMAL(8, 4),
    positive_score DECIMAL(8, 4),
    negative_score DECIMAL(8, 4),
    polarity DECIMAL(8, 4),
    activity_reference_density DECIMAL(8, 4),
    self_group_reference_density DECIMAL(8, 4),
    word_count INTEGER,
    
    -- Source & verification metrics
    source_url TEXT,
    source_domain VARCHAR(255),
    num_mentions INTEGER DEFAULT 0,
    num_sources INTEGER DEFAULT 0,
    num_articles INTEGER DEFAULT 0,
    
    -- Cross-reference with ACLED
    acled_event_id BIGINT,
    verification_status VARCHAR(20) DEFAULT 'unverified',
    confidence_score DECIMAL(4, 3),
    
    -- Chokepoint specific
    chokepoint_region VARCHAR(50),
    is_maritime BOOLEAN DEFAULT FALSE,
    
    -- GDELT specific metrics
    goldstein_scale DECIMAL(5, 2),
    quad_class INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    raw_gdelt_data JSONB,
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_verification CHECK (verification_status IN ('verified', 'likely', 'unverified', 'false_positive'))
);

-- Spatial index for geographic queries
CREATE INDEX IF NOT EXISTS idx_gdelt_events_location 
ON gdelt_events USING GIST (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));

-- Date index for time-range queries
CREATE INDEX IF NOT EXISTS idx_gdelt_events_date 
ON gdelt_events(event_date);

-- Chokepoint region index
CREATE INDEX IF NOT EXISTS idx_gdelt_events_chokepoint 
ON gdelt_events(chokepoint_region);

-- Verification status index
CREATE INDEX IF NOT EXISTS idx_gdelt_events_verification 
ON gdelt_events(verification_status);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_gdelt_events_chokepoint_date 
ON gdelt_events(chokepoint_region, event_date);

-- Index for ACLED cross-reference lookups
CREATE INDEX IF NOT EXISTS idx_gdelt_events_acled 
ON gdelt_events(acled_event_id) 
WHERE acled_event_id IS NOT NULL;

-- Index for confidence scoring queries
CREATE INDEX IF NOT EXISTS idx_gdelt_events_confidence 
ON gdelt_events(confidence_score DESC) 
WHERE verification_status != 'false_positive';

-- Full-text search on actor names
CREATE INDEX IF NOT EXISTS idx_gdelt_events_actors 
ON gdelt_events USING gin(to_tsvector('english', COALESCE(actor1_name, '') || ' ' || COALESCE(actor2_name, '')));

-- ACLED Cross-Reference Table
-- Links GDELT events to verified ACLED events

CREATE TABLE IF NOT EXISTS acled_gdelt_links (
    id SERIAL PRIMARY KEY,
    gdelt_event_id BIGINT NOT NULL REFERENCES gdelt_events(gdelt_event_id) ON DELETE CASCADE,
    acled_event_id BIGINT NOT NULL,
    match_score DECIMAL(4, 3) NOT NULL,
    match_method VARCHAR(50) NOT NULL,
    match_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure unique links
    CONSTRAINT unique_gdelt_acled_link UNIQUE(gdelt_event_id, acled_event_id),
    -- Validate score range
    CONSTRAINT valid_match_score CHECK (match_score >= 0.0 AND match_score <= 1.0)
);

-- Index for ACLED event lookups
CREATE INDEX IF NOT EXISTS idx_acled_gdelt_links_acled 
ON acled_gdelt_links(acled_event_id);

-- Index for match score queries
CREATE INDEX IF NOT EXISTS idx_acled_gdelt_links_score 
ON acled_gdelt_links(match_score DESC);

-- Index for match method filtering
CREATE INDEX IF NOT EXISTS idx_acled_gdelt_links_method 
ON acled_gdelt_links(match_method);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to gdelt_events
DROP TRIGGER IF EXISTS update_gdelt_events_updated_at ON gdelt_events;
CREATE TRIGGER update_gdelt_events_updated_at
    BEFORE UPDATE ON gdelt_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to acled_gdelt_links
DROP TRIGGER IF EXISTS update_acled_gdelt_links_updated_at ON acled_gdelt_links;
CREATE TRIGGER update_acled_gdelt_links_updated_at
    BEFORE UPDATE ON acled_gdelt_links
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for high-confidence events (suitable for heatmap display)
CREATE OR REPLACE VIEW v_gdelt_confirmed_events AS
SELECT 
    gdelt_event_id,
    event_date,
    latitude,
    longitude,
    chokepoint_region,
    event_root_code,
    event_base_code,
    event_code,
    actor1_name,
    actor2_name,
    tone_score,
    confidence_score,
    verification_status,
    source_url,
    num_mentions,
    num_sources
FROM gdelt_events
WHERE verification_status IN ('verified', 'likely')
    AND confidence_score >= 0.5
    AND latitude IS NOT NULL 
    AND longitude IS NOT NULL;

-- View for daily aggregates by chokepoint
CREATE OR REPLACE VIEW v_gdelt_daily_summary AS
SELECT 
    event_date,
    chokepoint_region,
    COUNT(*) as event_count,
    AVG(confidence_score) as avg_confidence,
    AVG(tone_score) as avg_tone,
    COUNT(CASE WHEN verification_status = 'verified' THEN 1 END) as verified_count,
    COUNT(CASE WHEN num_sources >= 3 THEN 1 END) as multi_source_count
FROM gdelt_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_date, chokepoint_region
ORDER BY event_date DESC, chokepoint_region;
