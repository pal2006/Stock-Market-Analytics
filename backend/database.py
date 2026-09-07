import os
import mysql.connector


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": "stock_market_analytics"
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    password = os.getenv("MYSQL_PASSWORD")

    if not password:
        raise RuntimeError(
            "MYSQL_PASSWORD environment variable is not set."
        )

    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=password,
        database=DB_CONFIG["database"]
    )


# =========================================================
# GET ALL STOCKS
# =========================================================

def get_stocks():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                ticker,
                company_name,
                sector,
                market_cap,
                pe_ratio,
                dividend_yield,
                quarterly_dividend
            FROM stocks
            ORDER BY ticker
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET STOCK ANALYSIS
# =========================================================

def get_stock_analysis(ticker):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
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
                a.average_volume,

                a.market_cap,
                a.pe_ratio,
                a.dividend_yield,
                a.quarterly_dividend

            FROM stocks s

            LEFT JOIN stock_analysis_summary a
                ON s.ticker = a.ticker

            WHERE s.ticker = %s
        """, (ticker.upper(),))

        return cursor.fetchone()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET HISTORICAL PRICE DATA
# =========================================================

def get_price_history(ticker):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                trade_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM price_history
            WHERE ticker = %s
            ORDER BY trade_date
        """, (ticker.upper(),))

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET CLEANED HISTORICAL PRICE DATA
# =========================================================

def get_clean_price_history(ticker):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                trade_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM price_history_cleaned
            WHERE ticker = %s
            ORDER BY trade_date
        """, (ticker.upper(),))

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# CHECK WHETHER STOCK EXISTS
# =========================================================

def stock_exists(ticker):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM stocks
            WHERE ticker = %s
        """, (ticker.upper(),))

        result = cursor.fetchone()

        return result[0] > 0

    finally:

        cursor.close()
        connection.close()


# =========================================================
# INSERT NEW STOCK
# =========================================================

def insert_stock(
    ticker,
    company_name,
    sector,
    market_cap=None,
    pe_ratio=None,
    dividend_yield=None,
    quarterly_dividend=None
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO stocks
            (
                ticker,
                company_name,
                sector,
                market_cap,
                pe_ratio,
                dividend_yield,
                quarterly_dividend
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            ticker.upper(),
            company_name,
            sector,
            market_cap,
            pe_ratio,
            dividend_yield,
            quarterly_dividend
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# UPDATE STOCK FUNDAMENTALS
# =========================================================

def update_stock_fundamentals(
    ticker,
    company_name,
    sector,
    market_cap=None,
    pe_ratio=None,
    dividend_yield=None,
    quarterly_dividend=None
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE stocks
            SET
                company_name = %s,
                sector = %s,
                market_cap = %s,
                pe_ratio = %s,
                dividend_yield = %s,
                quarterly_dividend = %s
            WHERE ticker = %s
        """, (
            company_name,
            sector,
            market_cap,
            pe_ratio,
            dividend_yield,
            quarterly_dividend,
            ticker.upper()
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# INSERT OR UPDATE PRICE HISTORY
# =========================================================

def upsert_price_history(
    ticker,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM price_history
            WHERE ticker = %s
            AND trade_date = %s
        """, (
            ticker.upper(),
            trade_date
        ))

        exists = cursor.fetchone()[0]

        if exists:

            cursor.execute("""
                UPDATE price_history
                SET
                    open_price = %s,
                    high_price = %s,
                    low_price = %s,
                    close_price = %s,
                    volume = %s
                WHERE ticker = %s
                AND trade_date = %s
            """, (
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                ticker.upper(),
                trade_date
            ))

        else:

            cursor.execute("""
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
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                ticker.upper(),
                trade_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# UPDATE ANALYSIS SUMMARY
#
# IMPORTANT:
# sector is NOT stored in stock_analysis_summary.
# sector belongs to stocks.
# =========================================================

def update_analysis_summary(
    ticker,
    sector,
    latest_price,
    highest_price,
    lowest_price,
    daily_volatility,
    annualized_volatility,
    annualized_return,
    maximum_drawdown,
    sharpe_ratio,
    average_volume,
    market_cap=None,
    pe_ratio=None,
    dividend_yield=None,
    quarterly_dividend=None
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM stock_analysis_summary
            WHERE ticker = %s
        """, (ticker.upper(),))

        exists = cursor.fetchone()[0]

        if exists:

            cursor.execute("""
                UPDATE stock_analysis_summary
                SET
                    latest_price = %s,
                    highest_price = %s,
                    lowest_price = %s,
                    daily_volatility = %s,
                    annualized_volatility = %s,
                    annualized_return = %s,
                    maximum_drawdown = %s,
                    sharpe_ratio = %s,
                    average_volume = %s,
                    market_cap = %s,
                    pe_ratio = %s,
                    dividend_yield = %s,
                    quarterly_dividend = %s
                WHERE ticker = %s
            """, (
                latest_price,
                highest_price,
                lowest_price,
                daily_volatility,
                annualized_volatility,
                annualized_return,
                maximum_drawdown,
                sharpe_ratio,
                average_volume,
                market_cap,
                pe_ratio,
                dividend_yield,
                quarterly_dividend,
                ticker.upper()
            ))

        else:

            cursor.execute("""
                INSERT INTO stock_analysis_summary
                (
                    ticker,
                    latest_price,
                    highest_price,
                    lowest_price,
                    daily_volatility,
                    annualized_volatility,
                    annualized_return,
                    maximum_drawdown,
                    sharpe_ratio,
                    average_volume,
                    market_cap,
                    pe_ratio,
                    dividend_yield,
                    quarterly_dividend
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                ticker.upper(),
                latest_price,
                highest_price,
                lowest_price,
                daily_volatility,
                annualized_volatility,
                annualized_return,
                maximum_drawdown,
                sharpe_ratio,
                average_volume,
                market_cap,
                pe_ratio,
                dividend_yield,
                quarterly_dividend
            ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET SECTOR SUMMARY
#
# sector comes from stocks table.
# analytics come from stock_analysis_summary.
# =========================================================

def get_sector_summary():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                s.sector,

                COUNT(*) AS number_of_stocks,

                AVG(a.annualized_return)
                    AS avg_return,

                AVG(a.annualized_volatility)
                    AS avg_volatility,

                AVG(a.maximum_drawdown)
                    AS avg_drawdown,

                AVG(a.sharpe_ratio)
                    AS avg_sharpe,

                AVG(a.average_volume)
                    AS avg_volume

            FROM stocks s

            INNER JOIN stock_analysis_summary a
                ON s.ticker = a.ticker

            GROUP BY s.sector

            ORDER BY avg_return DESC
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()