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

cursor = connection.cursor()

print("\nSuccessfully connected to MySQL!")


# ============================================================
# 2. LOAD DATA FROM PRICE_HISTORY
# ============================================================

print("\nLoading price data from MySQL...")

query = """
SELECT
    ticker,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM price_history
ORDER BY ticker, trade_date
"""

df = pd.read_sql(query, connection)

print(f"Total records loaded: {len(df)}")


# ============================================================
# 3. CONVERT DATA TYPES
# ============================================================

print("\nConverting data types...")

df["trade_date"] = pd.to_datetime(df["trade_date"])

numeric_columns = [
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")


# ============================================================
# 4. CHECK FOR MISSING VALUES
# ============================================================

print("\nChecking for missing values...")

missing_before = df.isnull().sum()

print(missing_before)


# ============================================================
# 5. REMOVE INVALID / MISSING RECORDS
# ============================================================

print("\nRemoving invalid records...")

df = df.dropna(
    subset=[
        "ticker",
        "trade_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume"
    ]
)


# ============================================================
# 6. REMOVE DUPLICATE STOCK/DATE RECORDS
# ============================================================

print("\nChecking for duplicate records...")

duplicates = df.duplicated(
    subset=["ticker", "trade_date"]
).sum()

print(f"Duplicate records found: {duplicates}")

df = df.drop_duplicates(
    subset=["ticker", "trade_date"],
    keep="last"
)


# ============================================================
# 7. SORT DATA
# ============================================================

df = df.sort_values(
    by=["ticker", "trade_date"]
).reset_index(drop=True)


# ============================================================
# 8. BASIC PRICE VALIDATION
# ============================================================

print("\nChecking price validity...")

invalid_prices = (
    (df["open_price"] <= 0) |
    (df["high_price"] <= 0) |
    (df["low_price"] <= 0) |
    (df["close_price"] <= 0) |
    (df["volume"] < 0)
).sum()

print(f"Invalid price/volume records: {invalid_prices}")

df = df[
    (df["open_price"] > 0) &
    (df["high_price"] > 0) &
    (df["low_price"] > 0) &
    (df["close_price"] > 0) &
    (df["volume"] >= 0)
]


# ============================================================
# 9. CREATE CLEANED TABLE IN MYSQL
# ============================================================

print("\nCreating cleaned data table...")

create_table_query = """
CREATE TABLE IF NOT EXISTS price_history_cleaned (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    close_price DECIMAL(15,4),
    volume BIGINT,
    UNIQUE KEY unique_stock_date (ticker, trade_date)
)
"""

cursor.execute(create_table_query)


# ============================================================
# 10. CLEAR PREVIOUS CLEANED DATA
# ============================================================

cursor.execute("TRUNCATE TABLE price_history_cleaned")


# ============================================================
# 11. INSERT CLEANED DATA
# ============================================================

print("\nInserting cleaned data into MySQL...")

insert_query = """
INSERT INTO price_history_cleaned
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
"""

records = []

for _, row in df.iterrows():

    records.append(
        (
            row["ticker"],
            row["trade_date"].date(),
            float(row["open_price"]),
            float(row["high_price"]),
            float(row["low_price"]),
            float(row["close_price"]),
            int(row["volume"])
        )
    )

cursor.executemany(insert_query, records)

connection.commit()


# ============================================================
# 12. FINAL SUMMARY
# ============================================================

print("\n========================================")
print("DATA CLEANING COMPLETED SUCCESSFULLY!")
print("========================================")

print(f"Records after cleaning: {len(df)}")
print(f"Stocks processed: {df['ticker'].nunique()}")
print(
    f"Date range: "
    f"{df['trade_date'].min().date()} "
    f"to "
    f"{df['trade_date'].max().date()}"
)


# ============================================================
# 13. CLOSE CONNECTION
# ============================================================

cursor.close()
connection.close()

print("\nMySQL connection closed.")