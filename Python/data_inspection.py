import mysql.connector
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
# 2. CHECK NUMBER OF STOCKS
# ============================================================

cursor.execute("SELECT COUNT(*) FROM stocks")

total_stocks = cursor.fetchone()[0]

print(f"\nTotal stocks in database: {total_stocks}")


# ============================================================
# 3. CHECK TOTAL PRICE RECORDS
# ============================================================

cursor.execute("SELECT COUNT(*) FROM price_history")

total_records = cursor.fetchone()[0]

print(f"Total price records: {total_records}")


# ============================================================
# 4. SHOW RECORDS AVAILABLE FOR EACH STOCK
# ============================================================

cursor.execute("""
    SELECT ticker, COUNT(*) AS records
    FROM price_history
    GROUP BY ticker
    ORDER BY ticker
""")

stock_records = cursor.fetchall()

print("\nRecords available for each stock:")

for ticker, records in stock_records:
    print(f"{ticker}: {records}")

# ============================================================
# 5. CHECK FOR MISSING VALUES
# ============================================================

print("\nChecking for missing values...")

cursor.execute("""
    SELECT
        COUNT(*) AS total_records,
        SUM(open_price IS NULL) AS missing_open,
        SUM(high_price IS NULL) AS missing_high,
        SUM(low_price IS NULL) AS missing_low,
        SUM(close_price IS NULL) AS missing_close,
        SUM(volume IS NULL) AS missing_volume
    FROM price_history
""")

missing_data = cursor.fetchone()

print(f"Total records: {missing_data[0]}")
print(f"Missing Open prices: {missing_data[1]}")
print(f"Missing High prices: {missing_data[2]}")
print(f"Missing Low prices: {missing_data[3]}")
print(f"Missing Close prices: {missing_data[4]}")
print(f"Missing Volume values: {missing_data[5]}")


# ============================================================
# 6. CHECK FOR DUPLICATE RECORDS
# ============================================================

print("\nChecking for duplicate stock/date records...")

cursor.execute("""
    SELECT ticker, trade_date, COUNT(*) AS duplicate_count
    FROM price_history
    GROUP BY ticker, trade_date
    HAVING COUNT(*) > 1
""")

duplicates = cursor.fetchall()

if len(duplicates) == 0:
    print("No duplicate stock/date records found.")
else:
    print(f"Found {len(duplicates)} duplicate stock/date records.")

    for ticker, trade_date, count in duplicates:
        print(f"{ticker} | {trade_date} | {count} records")


# ============================================================
# 7. CHECK DATE RANGE
# ============================================================

print("\nChecking date range...")

cursor.execute("""
    SELECT
        MIN(trade_date) AS earliest_date,
        MAX(trade_date) AS latest_date
    FROM price_history
""")

date_range = cursor.fetchone()

print(f"Earliest date: {date_range[0]}")
print(f"Latest date: {date_range[1]}")    


# ============================================================
# 5. CLOSE CONNECTION
# ============================================================

cursor.close()
connection.close()

print("\nData inspection completed successfully!")