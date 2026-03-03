"""
One-time script to seed Supabase from Excel.
"""
import sys, os
import pandas as pd
from supabase import create_client

DB_COLS = {
    "3M": "m3", "6M": "m6", "1Y": "y1", "2Y": "y2",
    "3Y": "y3", "5Y": "y5", "10Y": "y10", "30Y": "y30",
}
TENORS = list(DB_COLS.keys())

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "US_Yeild_Curve.xlsx"
    df = pd.read_excel(filepath, sheet_name="Daily")
    df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.date
    df = df.dropna(subset=TENORS, how="all")
    print(f"Loaded {len(df)} rows")
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    records = []
    for _, row in df.iterrows():
        record = {"observation_date": row["observation_date"].isoformat()}
        for tenor in TENORS:
            val = row.get(tenor)
            record[DB_COLS[tenor]] = None if pd.isna(val) else round(float(val), 4)
        records.append(record)
    batch_size = 500
    total = len(records)
    for i in range(0, total, batch_size):
        batch = records[i : i + batch_size]
        supabase.table("yield_curve").upsert(batch).execute()
        pct = min(i + batch_size, total)
        print(f"  Upserted {pct}/{total}")
    print("Done!")

if __name__ == "__main__":
    main()
