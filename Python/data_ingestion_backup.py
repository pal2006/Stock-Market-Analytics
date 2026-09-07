import mysql.connector
import yfinance as yf
from datetime import datetime


# ============================================================
# 1. CONNECT TO MYSQL
# ============================================================

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="P@rthDatabase",
    database="stock_market_analytics"
)

cursor = connection.cursor()

print("Successfully connected to MySQL!")


# ============================================================
# 2. GET ALL STOCKS FROM MYSQL
# ============================================================

cursor.execute("SELECT ticker FROM stocks")

stocks = cursor.fetchall()

print(f"Found {len(stocks)} stocks in MySQL.")


# ============================================================
# 3. FETCH AND STORE PRICE DATA
# ============================================================

for stock in stocks:

    ticker = stock[0]

    # Indian stocks on Yahoo Finance generally use .NS
    yahoo_ticker = ticker if "." in ticker else ticker + ".NS"

    print(f"\nFetching data for {ticker}...")

    try:

        # Fetch approximately 1 year of historical data
        data = yf.Ticker(yahoo_ticker).history(
            period="1y",
            auto_adjust=False
        )

        if data.empty:
            print(f"No data found for {ticker}")
            continue

        # ----------------------------------------------------
        # Insert each trading day's data into MySQL
        # ----------------------------------------------------

        for date, row in data.iterrows():

            trade_date = date.strftime("%Y-%m-%d")

            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])
            volume = int(row["Volume"])

            # Check whether this stock/date already exists
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM price_history
                WHERE ticker = %s
                AND trade_date = %s
                """,
                (ticker, trade_date)
            )

            exists = cursor.fetchone()[0]

            if exists == 0:

                cursor.execute(
                    """
                    INSERT INTO price_history
                    (
                        ticker,
                        trade_date,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ticker,
                        trade_date,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    )
                )

        connection.commit()

        print(f"Successfully inserted data for {ticker}")

    except Exception as e:

        print(f"Error while processing {ticker}: {e}")


# ============================================================
# 4. CLOSE MYSQL CONNECTION
# ============================================================

cursor.close()
connection.close()

print("\nData ingestion completed successfully!")