"""下载A股个股近5年日K(前复权)并存入 inputs/prices/{code}.csv
用法: python notes/download_prices.py 000938
"""
import sys
from datetime import date
from pathlib import Path

import akshare as ak

symbol = sys.argv[1] if len(sys.argv) > 1 else "000938"
today = date.today()
start = today.replace(year=today.year - 5)

df = ak.stock_zh_a_hist(
    symbol=symbol,
    period="daily",
    start_date=start.strftime("%Y%m%d"),
    end_date=today.strftime("%Y%m%d"),
    adjust="qfq",  # 前复权
)
print(f"rows={len(df)}")

out_dir = Path(__file__).resolve().parents[1] / "inputs" / "prices"
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / f"{symbol}.csv"
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"saved: {out}")
