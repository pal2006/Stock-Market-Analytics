import mysql.connector
from getpass import getpass
import pandas as pd


# ============================================================
# 1. CONNECT TO MYSQL
# ============================================================

password = getpass("Enter MySQL password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=password,
    database="stock_market_analytics"
)

print("\nSuccessfully connected to MySQL!")


# ============================================================
# 2. LOAD STOCK METRICS
# ============================================================

print("\nLoading stock metrics...")

query = """
SELECT
    s.ticker,
    s.company_name,
    s.sector,
    a.latest_price,
    a.highest_price,
    a.lowest_price,
    a.daily_volatility,
    a.annualized_volatility,
    a.annualized_return,
    a.maximum_drawdown,
    a.sharpe_ratio,
    a.average_volume
FROM stock_analysis_summary a
JOIN stocks s
    ON a.ticker = s.ticker
ORDER BY s.sector, s.ticker
"""

try:
    df = pd.read_sql(query, connection)

except Exception as e:

    print("\nError loading stock metrics:")
    print(e)

    connection.close()
    exit()


print(f"Stocks loaded: {len(df)}")


# ============================================================
# 3. CHECK SECTOR DATA
# ============================================================

print("\nSectors found:")

for sector in df["sector"].dropna().unique():

    print(f"- {sector}")


# ============================================================
# 4. CALCULATE SECTOR SUMMARY
# ============================================================

sector_summary = (
    df.groupby("sector")
    .agg(
        Number_of_Stocks=("ticker", "count"),
        Average_Return=("annualized_return", "mean"),
        Average_Volatility=("annualized_volatility", "mean"),
        Average_Drawdown=("maximum_drawdown", "mean"),
        Average_Sharpe=("sharpe_ratio", "mean"),
        Average_Volume=("average_volume", "mean")
    )
    .reset_index()
)


# ============================================================
# 5. SORT BY SHARPE RATIO
# ============================================================

sector_summary = sector_summary.sort_values(
    "Average_Sharpe",
    ascending=False
).reset_index(drop=True)


# ============================================================
# 6. DISPLAY SECTOR ANALYSIS
# ============================================================

print("\n==============================================")
print("             SECTOR ANALYSIS")
print("==============================================")

print(
    sector_summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# 7. BEST PERFORMING SECTOR
# ============================================================

best_sector = sector_summary.iloc[0]

print("\n----------------------------------------------")
print("Best Risk-Adjusted Sector")
print("----------------------------------------------")

print(
    f"Sector: {best_sector['sector']}"
)

print(
    f"Average Sharpe Ratio: "
    f"{best_sector['Average_Sharpe']:.2f}"
)

print(
    f"Average Annualized Return: "
    f"{best_sector['Average_Return'] * 100:.2f}%"
)


# ============================================================
# 8. SAVE SECTOR SUMMARY
# ============================================================

sector_summary.to_csv(
    "Data/Processed/sector_summary.csv",
    index=False
)

print("\nSector summary saved successfully!")


# ============================================================
# 9. CLOSE MYSQL CONNECTION
# ============================================================

connection.close()

print("MySQL connection closed.")