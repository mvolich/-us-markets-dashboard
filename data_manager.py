"""
Data manager for US Yield Curve dashboard.
Handles Supabase persistence and FRED API updates.
"""
import os
import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from supabase import create_client, Client
from fredapi import Fred

# FRED series to column mapping
FRED_SERIES = {
    "DGS3MO": "3M",
    "DGS6MO": "6M",
    "DGS1": "1Y",
    "DGS2": "2Y",
    "DGS3": "3Y",
    "DGS5": "5Y",
    "DGS10": "10Y",
    "DGS30": "30Y",
}

TENORS = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y", "30Y"]

# DB-safe column names
DB_COLS = {
    "3M": "m3", "6M": "m6", "1Y": "y1", "2Y": "y2",
    "3Y": "y3", "5Y": "y5", "10Y": "y10", "30Y": "y30",
}
DB_COLS_REV = {v: k for k, v in DB_COLS.items()}


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"],
    )


def get_fred_client() -> Fred:
    return Fred(api_key=os.environ["FRED_API_KEY"])


def fetch_latest_date(supabase: Client) -> Optional[datetime.date]:
    result = (
        supabase.table("yield_curve")
        .select("observation_date")
        .order("observation_date", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return datetime.date.fromisoformat(result.data[0]["observation_date"])
    return None


def fetch_from_fred(start_date: datetime.date) -> pd.DataFrame:
    fred = get_fred_client()
    frames = {}
    for series_id, col_name in FRED_SERIES.items():
        try:
            s = fred.get_series(series_id, observation_start=start_date.isoformat())
            frames[col_name] = s
        except Exception as e:
            st.warning(f"Failed to fetch {series_id}: {e}")

    if not frames:
        return pd.DataFrame()

    df = pd.DataFrame(frames)
    df.index.name = "observation_date"
    df = df.reset_index()
    df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.date
    df = df.dropna(subset=TENORS, how="all")
    return df


def upsert_to_supabase(supabase: Client, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    records = []
    for _, row in df.iterrows():
        record = {"observation_date": row["observation_date"].isoformat()}
        for tenor in TENORS:
            val = row.get(tenor)
            record[DB_COLS[tenor]] = None if pd.isna(val) else round(float(val), 4)
        records.append(record)

    batch_size = 500
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        supabase.table("yield_curve").upsert(batch).execute()
        total += len(batch)
    return total


def load_full_dataset(supabase: Client) -> pd.DataFrame:
    all_data = []
    batch_size = 1000
    offset = 0

    while True:
        result = (
            supabase.table("yield_curve")
            .select("*")
            .order("observation_date")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        if not result.data:
            break
        all_data.extend(result.data)
        if len(result.data) < batch_size:
            break
        offset += batch_size

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df = df.rename(columns=DB_COLS_REV)
    df = df[["observation_date"] + TENORS]
    df = df.sort_values("observation_date").reset_index(drop=True)
    return df


def refresh_data(supabase: Client):
    """Check for new data, update from FRED if stale, return (df, status_msg)."""
    latest = fetch_latest_date(supabase)
    today = datetime.date.today()
    status = ""

    if latest is None:
        status = "Database is empty. Run load_initial_data.py first."
    elif (today - latest).days > 1:
        start = latest + datetime.timedelta(days=1)
        new_data = fetch_from_fred(start)
        if not new_data.empty:
            count = upsert_to_supabase(supabase, new_data)
            status = f"Updated {count} rows (through {new_data['observation_date'].max()})"
        else:
            status = f"No new data from FRED. Latest: {latest}"
    else:
        status = f"Data current (latest: {latest})"

    df = load_full_dataset(supabase)
    return df, status
