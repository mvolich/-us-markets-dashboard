# US Markets Dashboard

Streamlit dashboard for US Treasury yield curve visualization.

## Stack (all free tier)

- Supabase: PostgreSQL database for daily yield curve observations
- Streamlit Community Cloud: Hosts the dashboard
- FRED API: Auto-fetches new observations on each app load

## Setup

### 1. Supabase

1. Create a free project at supabase.com
2. Go to SQL Editor and run supabase_schema.sql
3. Note your Project URL and anon key from Settings > API

### 2. Seed the database

    pip install pandas supabase openpyxl
    export SUPABASE_URL=https://your-project.supabase.co
    export SUPABASE_KEY=your-anon-key
    python load_initial_data.py US_Yeild_Curve.xlsx

### 3. FRED API key

Register at fred.stlouisfed.org and get a free API key.

### 4. Deploy to Streamlit Community Cloud

1. Push repo to GitHub
2. Connect at share.streamlit.io
3. Set secrets: SUPABASE_URL, SUPABASE_KEY, FRED_API_KEY
4. Set main file to app.py

### 5. Local dev

    pip install -r requirements.txt
    streamlit run app.py

## Data flow

On each load: check latest date in Supabase, fetch missing from FRED, upsert, render.

## FRED Series

| Col | Series  | Description     |
|-----|---------|----------------|
| 3M  | DGS3MO  | 3-Month Treasury |
| 6M  | DGS6MO  | 6-Month Treasury |
| 1Y  | DGS1    | 1-Year Treasury  |
| 2Y  | DGS2    | 2-Year Treasury  |
| 3Y  | DGS3    | 3-Year Treasury  |
| 5Y  | DGS5    | 5-Year Treasury  |
| 10Y | DGS10   | 10-Year Treasury |
| 30Y | DGS30   | 30-Year Treasury |
