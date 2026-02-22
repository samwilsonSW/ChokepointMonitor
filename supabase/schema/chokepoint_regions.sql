-- Chokepoint Regions Table
-- Stores geospatial polygons for the three critical maritime oil chokepoints

CREATE TABLE IF NOT EXISTS chokepoint_regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    geojson_polygon JSONB NOT NULL,
    center_lat DECIMAL(10, 8) NOT NULL,
    center_lon DECIMAL(11, 8) NOT NULL,
    bounding_box JSONB NOT NULL,
    route_importance VARCHAR(20) DEFAULT 'critical',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert the three chokepoint regions with approximate bounding polygons

-- Bab el-Mandeb: Connects Red Sea to Gulf of Aden
INSERT INTO chokepoint_regions (name, display_name, geojson_polygon, center_lat, center_lon, bounding_box, route_importance)
VALUES (
    'bab-el-mandeb',
    'Bab el-Mandeb',
    '{
        "type": "Polygon",
        "coordinates": [[
            [42.8, 12.3],
            [43.5, 12.3],
            [43.5, 13.0],
            [43.0, 13.5],
            [42.5, 13.2],
            [42.3, 12.8],
            [42.8, 12.3]
        ]]
    }'::jsonb,
    12.75,
    43.0,
    '[42.3, 12.3, 43.5, 13.5]'::jsonb,
    'critical'
)
ON CONFLICT (name) DO NOTHING;

-- Strait of Hormuz: Connects Persian Gulf to Gulf of Oman
INSERT INTO chokepoint_regions (name, display_name, geojson_polygon, center_lat, center_lon, bounding_box, route_importance)
VALUES (
    'strait-of-hormuz',
    'Strait of Hormuz',
    '{
        "type": "Polygon",
        "coordinates": [[
            [56.2, 25.8],
            [56.6, 25.8],
            [56.6, 26.8],
            [56.4, 27.0],
            [56.0, 27.0],
            [55.8, 26.5],
            [56.2, 25.8]
        ]]
    }'::jsonb,
    26.4,
    56.3,
    '[55.8, 25.8, 56.6, 27.0]'::jsonb,
    'critical'
)
ON CONFLICT (name) DO NOTHING;

-- Strait of Malacca: Between Malaysia and Indonesia
INSERT INTO chokepoint_regions (name, display_name, geojson_polygon, center_lat, center_lon, bounding_box, route_importance)
VALUES (
    'strait-of-malacca',
    'Strait of Malacca',
    '{
        "type": "Polygon",
        "coordinates": [[
            [98.0, 2.5],
            [99.0, 2.5],
            [99.0, 3.8],
            [104.0, 3.8],
            [104.0, 1.2],
            [98.5, 1.2],
            [98.0, 2.5]
        ]]
    }'::jsonb,
    2.5,
    101.0,
    '[98.0, 1.2, 104.0, 3.8]'::jsonb,
    'critical'
)
ON CONFLICT (name) DO NOTHING;

-- Create spatial index for fast geospatial queries
CREATE INDEX IF NOT EXISTS idx_chokepoint_regions_geo 
ON chokepoint_regions USING GIST (
    ST_SetSRID(ST_GeomFromGeoJSON(geojson_polygon::text), 4326)
);
