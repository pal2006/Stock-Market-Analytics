import mysql.connector
import yfinance as yf
from getpass import getpass


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

cursor = connection.cursor()

print("\nSuccessfully connected to MySQL!")


# ============================================================
# 2. GET STOCK TICKER FROM USER
# ============================================================

ticker = input(
    "\nEnter stock ticker (example: RELIANCE, TCS, INFY, SBIN): "
).strip().upper()

# Convert Indian NSE ticker to Yahoo Finance format
yahoo_ticker = ticker if "." in ticker else ticker + ".NS"

print(f"\nChecking stock: {ticker}...")


# ============================================================
# 3. CHECK WHETHER STOCK ALREADY EXISTS
# ============================================================

cursor.execute(
    "SELECT ticker FROM stocks WHERE ticker = %s",
    (ticker,)
)

existing_stock = cursor.fetchone()


# ============================================================
# 4. IF STOCK DOES NOT EXIST, ADD IT TO MYSQL
# ============================================================

if existing_stock is None:

    print(f"{ticker} is not in the database.")
    print("Getting company information from Yahoo Finance...")

    try:

        stock_object = yf.Ticker(yahoo_ticker)

        info = stock_object.info

        company_name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector") or "Unknown"

        cursor.execute(
            """
            INSERT INTO stocks
            (ticker, company_name, sector)
            VALUES (%s, %s, %s)
            """,
            (ticker, company_name, sector)
        )

        connection.commit()

        print(f"Successfully added {ticker} to stocks table.")
        print(f"Company: {company_name}")
        print(f"Sector: {sector}")

    except Exception as e:

        print(f"Could not add {ticker} to database: {e}")

        cursor.close()
        connection.close()

        exit()


else:

    print(f"{ticker} already exists in the database.")


# ============================================================
# 5. FETCH HISTORICAL PRICE DATA
# ============================================================

print(f"\nFetching data for {ticker}...")

try:

    data = yf.Ticker(yahoo_ticker).history(
        period="1y",
        auto_adjust=False
    )

    if data.empty:

        print(f"No price data found for {ticker}")

    else:

        print(f"Found {len(data)} trading-day records.")

        # ----------------------------------------------------
        # Insert each trading day's data
        # ----------------------------------------------------

        inserted_records = 0

        for date, row in data.iterrows():

            trade_date = date.strftime("%Y-%m-%d")

            # ------------------------------------------------
            # Check for missing values
            # ------------------------------------------------

            if (
                row["Open"] != row["Open"]
                or row["High"] != row["High"]
                or row["Low"] != row["Low"]
                or row["Close"] != row["Close"]
                or row["Volume"] != row["Volume"]
            ):
                continue

            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])
            volume = int(row["Volume"])

            # ------------------------------------------------
            # Check whether stock/date already exists
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Insert only new records
            # ------------------------------------------------

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

                inserted_records += 1

        # Save changes
        connection.commit()

        print(f"Successfully inserted {inserted_records} new records for {ticker}")


except Exception as e:

    print(f"Error while processing {ticker}: {e}")


# ============================================================
# 6. CLOSE MYSQL CONNECTION
# ============================================================

cursor.close()
connection.close()

print("\nData ingestion completed successfully!")