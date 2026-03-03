-- Run this in the Supabase SQL Editor to create the table.

CREATE TABLE IF NOT EXISTS yield_curve (
    observation_date DATE PRIMARY KEY,
    m3  REAL,   -- 3-month
    m6  REAL,   -- 6-month
    y1  REAL,   -- 1-year
    y2  REAL,   -- 2-year
    y3  REAL,   -- 3-year
    y5  REAL,   -- 5-year
    y10 REAL,   -- 10-year
    y30 REAL    -- 30-year
);

-- Index for fast date-range queries
CREATE INDEX IF NOT EXISTS idx_yield_curve_date
    ON yield_curve (observation_date DESC);

-- Enable Row Level Security (required by Supabase)
ALTER TABLE yield_curve ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access (for the Streamlit app)
CREATE POLICY "Allow anonymous read" ON yield_curve
    FOR SELECT USING (true);

-- Allow authenticated inserts/updates (for the data loader and FRED updater)
CREATE POLICY "Allow service role write" ON yield_curve
    FOR ALL USING (true) WITH CHECK (true);
