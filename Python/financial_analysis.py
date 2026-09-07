import mysql.connector
from getpass import getpass
import pandas as pd
import numpy as np


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
# 2. LOAD CLEANED DATA FROM MYSQL
# ============================================================

query = """
SELECT
    p.ticker,
    s.sector,
    p.trade_date,
    p.open_price,
    p.high_price,
    p.low_price,
    p.close_price,
    p.volume
FROM price_history_cleaned p
JOIN stocks s
    ON p.ticker = s.ticker
ORDER BY p.ticker, p.trade_date
"""

df = pd.read_sql(query, connection)

print(f"Total records loaded: {len(df)}")
print(f"Stocks found: {df['ticker'].nunique()}")


# ============================================================
# 3. PREPARE DATA
# ============================================================

df["trade_date"] = pd.to_datetime(df["trade_date"])

df = df.sort_values(
    ["ticker", "trade_date"]
).reset_index(drop=True)


# ============================================================
# 4. CALCULATE DAILY RETURN
# ============================================================

df["Daily_Return"] = (
    df.groupby("ticker")["close_price"]
    .pct_change()
)


# ============================================================
# 5. CALCULATE MOVING AVERAGES
# ============================================================

df["MA20"] = (
    df.groupby("ticker")["close_price"]
    .transform(lambda x: x.rolling(20).mean())
)

df["MA50"] = (
    df.groupby("ticker")["close_price"]
    .transform(lambda x: x.rolling(50).mean())
)

df["MA200"] = (
    df.groupby("ticker")["close_price"]
    .transform(lambda x: x.rolling(200).mean())
)


# ============================================================
# 6. CALCULATE 20-DAY ROLLING VOLATILITY
# ============================================================

df["Rolling_Volatility_20D"] = (
    df.groupby("ticker")["Daily_Return"]
    .transform(lambda x: x.rolling(20).std())
)


# ============================================================
# 7. CALCULATE RUNNING MAXIMUM
# ============================================================

df["Running_Max"] = (
    df.groupby("ticker")["close_price"]
    .cummax()
)


# ============================================================
# 8. CALCULATE DRAWDOWN
# ============================================================

df["Drawdown"] = (
    (df["close_price"] - df["Running_Max"])
    / df["Running_Max"]
)


# ============================================================
# 9. RISK-FREE RATE
# ============================================================

risk_free_rate = 0.06


# ============================================================
# 10. CALCULATE STOCK-LEVEL METRICS
# ============================================================

results = []


for ticker, stock_data in df.groupby("ticker"):

    stock_data = stock_data.copy()

    # Remove NaN returns for calculations
    returns = stock_data["Daily_Return"].dropna()

    # --------------------------------------------------------
    # Daily volatility
    # --------------------------------------------------------

    daily_volatility = returns.std()

    # --------------------------------------------------------
    # Annualized volatility
    # --------------------------------------------------------

    annualized_volatility = (
        daily_volatility * np.sqrt(252)
    )

    # --------------------------------------------------------
    # Annualized return
    # --------------------------------------------------------

    start_price = stock_data["close_price"].iloc[0]
    end_price = stock_data["close_price"].iloc[-1]

    number_of_days = (
        stock_data["trade_date"].iloc[-1]
        - stock_data["trade_date"].iloc[0]
    ).days

    if number_of_days > 0:

        years = number_of_days / 365

        annualized_return = (
            (end_price / start_price) ** (1 / years)
        ) - 1

    else:

        annualized_return = np.nan


    # --------------------------------------------------------
    # Maximum drawdown
    # --------------------------------------------------------

    maximum_drawdown = stock_data["Drawdown"].min()


    # --------------------------------------------------------
    # Sharpe Ratio
    # --------------------------------------------------------

    if annualized_volatility != 0:

        sharpe_ratio = (
            annualized_return - risk_free_rate
        ) / annualized_volatility

    else:

        sharpe_ratio = np.nan


    # --------------------------------------------------------
    # Additional useful information
    # --------------------------------------------------------

    latest_price = stock_data["close_price"].iloc[-1]

    highest_price = stock_data["high_price"].max()

    lowest_price = stock_data["low_price"].min()

    average_volume = stock_data["volume"].mean()


    results.append(
        {
            "Ticker": ticker,
            "Sector": stock_data["sector"].iloc[0],
            "Latest_Price": latest_price,
            "Highest_Price": highest_price,
            "Lowest_Price": lowest_price,
            "Daily_Volatility": daily_volatility,
            "Annualized_Volatility": annualized_volatility,
            "Annualized_Return": annualized_return,
            "Maximum_Drawdown": maximum_drawdown,
            "Sharpe_Ratio": sharpe_ratio,
            "Average_Volume": average_volume
        }
    )


# ============================================================
# 11. CREATE SUMMARY DATAFRAME
# ============================================================

summary_df = pd.DataFrame(results)

summary_df = summary_df.rename(
    columns={"Ticker": "Stock"}
)

summary_df = summary_df.sort_values(
    "Sharpe_Ratio",
    ascending=False
).reset_index(drop=True)


# ============================================================
# 12. DISPLAY RESULTS
# ============================================================

print("\n==============================================")
print("        FINANCIAL ANALYSIS RESULTS")
print("==============================================")

print(
    summary_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# 13. SAVE ANALYTICAL DATA TO CSV
# ============================================================

df.to_csv(
    "Data/Processed/stock_analysis_data.csv",
    index=False
)

summary_df.to_csv(
    "Data/Processed/stock_analysis_summary.csv",
    index=False
)


# ============================================================
# 14. SAVE STOCK SUMMARY TO MYSQL
# ============================================================

print("\nSaving stock summary to MySQL...")

cursor = connection.cursor()

# Create table if it does not already exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_analysis_summary (
        ticker VARCHAR(20) PRIMARY KEY,
        latest_price DECIMAL(15,4),
        highest_price DECIMAL(15,4),
        lowest_price DECIMAL(15,4),
        daily_volatility DECIMAL(15,8),
        annualized_volatility DECIMAL(15,8),
        annualized_return DECIMAL(15,8),
        maximum_drawdown DECIMAL(15,8),
        sharpe_ratio DECIMAL(15,8),
        average_volume DECIMAL(20,4)
    )
""")


# Remove previous analysis results
cursor.execute("TRUNCATE TABLE stock_analysis_summary")


# Insert latest analysis results
insert_query = """
    INSERT INTO stock_analysis_summary (
        ticker,
        latest_price,
        highest_price,
        lowest_price,
        daily_volatility,
        annualized_volatility,
        annualized_return,
        maximum_drawdown,
        sharpe_ratio,
        average_volume
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


for _, row in summary_df.iterrows():

    cursor.execute(
        insert_query,
        (
            row["Stock"],
            float(row["Latest_Price"]),
            float(row["Highest_Price"]),
            float(row["Lowest_Price"]),
            float(row["Daily_Volatility"]),
            float(row["Annualized_Volatility"]),
            float(row["Annualized_Return"]),
            float(row["Maximum_Drawdown"]),
            float(row["Sharpe_Ratio"]),
            float(row["Average_Volume"])
        )
    )


connection.commit()

print("Stock analysis summary saved to MySQL successfully!")


# ============================================================
# 15. CLOSE MYSQL CONNECTION
# ============================================================

cursor.close()
connection.close()

print("\nDetailed analysis saved successfully!")
print("Summary analysis saved successfully!")
print("MySQL connection closed.")