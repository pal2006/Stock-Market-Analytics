from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import mysql.connector
import os
import getpass
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Stock Market Analytics API",
    description="Backend API for the Stock Market Analytics project",
    version="2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_NAME = "stock_market_analytics"

DB_PASSWORD = os.getenv("MYSQL_PASSWORD")

if not DB_PASSWORD:
    DB_PASSWORD = getpass.getpass(
        "Enter MySQL password: "
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_number(value):
    """
    Convert Yahoo / NumPy / pandas values
    into normal Python numbers.
    """

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    try:
        return float(value)

    except Exception:
        return None


def safe_fast_info_value(fast_info, key):
    """
    Safely read a value from yfinance fast_info.

    yfinance versions can expose fast_info as either
    a dictionary-like object or an object with attributes.
    """

    try:

        if hasattr(fast_info, "get"):

            value = fast_info.get(key)

            if value is not None:
                return value

    except Exception:
        pass

    try:

        return getattr(
            fast_info,
            key,
            None
        )

    except Exception:
        return None


def json_safe(value):
    """
    Convert values into JSON-safe Python values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            np.integer,
            np.int64,
            np.int32
        )
    ):
        return int(value)

    if isinstance(
        value,
        (
            np.floating,
            np.float64,
            np.float32
        )
    ):
        return float(value)

    if isinstance(
        value,
        (
            datetime,
        )
    ):
        return value.isoformat()

    if isinstance(
        value,
        pd.Timestamp
    ):
        return value.strftime(
            "%Y-%m-%d"
        )

    return value


# ============================================================
# FETCH CURRENT YAHOO FUNDAMENTALS
# ============================================================

def fetch_current_fundamentals(
    ticker,
    latest_history_price=None
):
    """
    Fetch the latest available Yahoo Finance quote
    and fundamental information.

    IMPORTANT:
    Current market-cap data is refreshed here instead
    of trusting an old value stored in MySQL.
    """

    yahoo_ticker = f"{ticker}.NS"

    print(
        f"Refreshing current Yahoo data for {ticker}..."
    )

    try:

        stock = yf.Ticker(
            yahoo_ticker
        )

        # ----------------------------------------------------
        # fast_info
        #
        # This is preferred for current quote fields such as
        # latest price, market cap and 52-week range.
        # ----------------------------------------------------

        try:

            fast_info = stock.fast_info

        except Exception as error:

            print(
                "fast_info unavailable:",
                error
            )

            fast_info = {}

        # ----------------------------------------------------
        # Standard Yahoo information
        # ----------------------------------------------------

        try:

            info = stock.info

        except Exception as error:

            print(
                "Yahoo info unavailable:",
                error
            )

            info = {}

        # ----------------------------------------------------
        # COMPANY
        # ----------------------------------------------------

        company_name = (
            info.get("longName")
            or info.get("shortName")
            or ticker
        )

        sector = (
            info.get("sector")
            or "Unknown"
        )

        industry = (
            info.get("industry")
            or "Unknown"
        )

        # ----------------------------------------------------
        # LATEST PRICE
        #
        # fast_info is preferred.
        # Historical price is fallback.
        # ----------------------------------------------------

        latest_price = safe_number(
            safe_fast_info_value(
                fast_info,
                "last_price"
            )
        )

        if latest_price is None:

            latest_price = safe_number(
                info.get("currentPrice")
            )

        if latest_price is None:

            latest_price = safe_number(
                latest_history_price
            )

        # ----------------------------------------------------
        # MARKET CAP
        #
        # THIS IS THE IMPORTANT FIX.
        #
        # Prefer current fast_info market cap.
        # Fall back to Yahoo info marketCap.
        # Final fallback:
        # shares outstanding × latest price.
        # ----------------------------------------------------

        market_cap = safe_number(
            info.get("marketCap")
        )

        if market_cap is None:

            market_cap = safe_number(
                safe_fast_info_value(
                    fast_info,
                    "market_cap"
                )
            )
        
    

        # ----------------------------------------------------
        # Fallback market-cap calculation
        # ----------------------------------------------------

        if (
            market_cap is None
            and latest_price is not None
        ):

            shares_outstanding = (
                safe_number(
                    info.get(
                        "sharesOutstanding"
                    )
                )
            )

            if shares_outstanding is not None:

                market_cap = (
                    shares_outstanding *
                    latest_price
                )

        # ----------------------------------------------------
        # P/E
        # ----------------------------------------------------

        pe_ratio = safe_number(
            info.get("trailingPE")
        )

        if pe_ratio is None:

            pe_ratio = safe_number(
                info.get("forwardPE")
            )

        # ----------------------------------------------------
        # 52-WEEK HIGH / LOW
        # ----------------------------------------------------

        fifty_two_week_high = safe_number(
            safe_fast_info_value(
                fast_info,
                "year_high"
            )
        )

        if fifty_two_week_high is None:

            fifty_two_week_high = safe_number(
                info.get("fiftyTwoWeekHigh")
            )

        fifty_two_week_low = safe_number(
            safe_fast_info_value(
                fast_info,
                "year_low"
            )
        )

        if fifty_two_week_low is None:

            fifty_two_week_low = safe_number(
                info.get("fiftyTwoWeekLow")
            )

        # ----------------------------------------------------
        # DIVIDEND DATA
        # ----------------------------------------------------

        dividend_yield = safe_number(
            info.get(
                "trailingAnnualDividendYield"
            )
        )

        if dividend_yield is None:

            dividend_yield = safe_number(
                info.get("dividendYield")
            )

        # Yahoo may return dividend yield as decimal.
        # Convert to percentage for our database/UI.
        if (
            dividend_yield is not None
            and dividend_yield < 1
        ):

            dividend_yield *= 100

        # ----------------------------------------------------
        # FETCH DIVIDEND HISTORY
        # ----------------------------------------------------

        annual_dividend = None
        latest_dividend = None
        quarterly_dividend = None

        try:

            dividends = stock.dividends

            if (
                dividends is not None
                and len(dividends) > 0
            ):

                dividends = dividends.dropna()

                if len(dividends) > 0:

                    latest_dividend = safe_number(
                        dividends.iloc[-1]
                    )

                    # Last 365 days of dividend payments
                    cutoff = (
                        pd.Timestamp.now(
                            tz=dividends.index.tz
                        )
                        - pd.Timedelta(
                            days=365
                        )
                        if getattr(
                            dividends.index,
                            "tz",
                            None
                        )
                        else
                        pd.Timestamp.now()
                        - pd.Timedelta(
                            days=365
                        )
                    )

                    recent_dividends = (
                        dividends[
                            dividends.index >= cutoff
                        ]
                    )

                    if len(
                        recent_dividends
                    ) > 0:

                        annual_dividend = safe_number(
                            recent_dividends.sum()
                        )

        except Exception as error:

            print(
                "Dividend history warning:",
                error
            )

        # ----------------------------------------------------
        # If dividend history was unavailable,
        # use Yahoo's annual dividend.
        # ----------------------------------------------------

        if annual_dividend is None:

            annual_dividend = safe_number(
                info.get(
                    "trailingAnnualDividendRate"
                )
            )

        # ----------------------------------------------------
        # Normalized quarterly dividend
        #
        # This is annual TTM dividend / 4.
        # ----------------------------------------------------

        if annual_dividend is not None:

            quarterly_dividend = (
                annual_dividend / 4
            )

        # ----------------------------------------------------
        # If dividend yield was missing,
        # calculate it from annual dividend / price.
        # ----------------------------------------------------

        if (
            dividend_yield is None
            and annual_dividend is not None
            and latest_price is not None
            and latest_price != 0
        ):

            dividend_yield = (
                annual_dividend /
                latest_price
            ) * 100

        # ----------------------------------------------------
        # CURRENT VOLUME
        # ----------------------------------------------------

        current_volume = safe_number(
            safe_fast_info_value(
                fast_info,
                "last_volume"
            )
        )

        if current_volume is None:

            current_volume = safe_number(
                info.get("volume")
            )

        # ----------------------------------------------------
        # RETURN FUNDAMENTALS
        # ----------------------------------------------------

        return {

            "ticker":
                ticker,

            "company_name":
                company_name,

            "sector":
                sector,

            "industry":
                industry,

            "latest_price":
                latest_price,

            "market_cap":
                market_cap,

            "pe_ratio":
                pe_ratio,

            "dividend_yield":
                dividend_yield,

            "annual_dividend":
                annual_dividend,

            "latest_dividend":
                latest_dividend,

            "quarterly_dividend":
                quarterly_dividend,

            "fifty_two_week_high":
                fifty_two_week_high,

            "fifty_two_week_low":
                fifty_two_week_low,

            "current_volume":
                current_volume,

            "data_source":
                "Yahoo Finance",

            "data_refreshed_at":
                datetime.now().isoformat(),

        }

    except Exception as error:

        print(
            "Fundamental data error:",
            error
        )

        raise HTTPException(
            status_code=404,
            detail=(
                f"Unable to retrieve "
                f"Yahoo Finance data for {ticker}"
            )
        )
        # ============================================================
# FETCH TODAY'S INTRADAY MARKET DATA
# ============================================================

def fetch_latest_intraday_data(
    ticker
):

    yahoo_ticker = f"{ticker}.NS"

    print(
        f"Fetching today's intraday data for {ticker}..."
    )

    try:

        stock = yf.Ticker(
            yahoo_ticker
        )

        intraday = stock.history(
            period="1d",
            interval="1m",
            auto_adjust=False
        )

        if (
            intraday is None
            or intraday.empty
        ):

            print(
                f"No intraday data available for {ticker}"
            )

            return None

        intraday = intraday.dropna(
            subset=["Close"]
        )

        if intraday.empty:

            return None

        latest_row = intraday.iloc[-1]

        latest_timestamp = (
            intraday.index[-1]
        )

        latest_price = safe_number(
            latest_row["Close"]
        )

        latest_volume = safe_number(
            latest_row.get("Volume")
        )

        if latest_price is None:

            return None

        if isinstance(
            latest_timestamp,
            pd.Timestamp
        ):

            if latest_timestamp.tzinfo:

                latest_timestamp = (
                    latest_timestamp
                    .tz_convert("Asia/Kolkata")
                )

            latest_trade_date = (
                latest_timestamp
                .strftime("%Y-%m-%d")
            )

            latest_trade_time = (
                latest_timestamp
                .strftime("%H:%M:%S")
            )

        else:

            latest_trade_date = str(
                latest_timestamp
            )[:10]

            latest_trade_time = None

        print(
            f"Intraday data for {ticker}: "
            f"{latest_price} "
            f"on {latest_trade_date}"
        )

        return {

            "latest_price":
                latest_price,

            "latest_volume":
                latest_volume,

            "latest_trade_date":
                latest_trade_date,

            "latest_trade_time":
                latest_trade_time,

        }

    except Exception as error:

        print(
            "Intraday Yahoo data error:",
            error
        )

        return None


# ============================================================
# ENSURE STOCK EXISTS
# ============================================================

def ensure_stock_exists(
    ticker,
    fundamentals
):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT ticker
            FROM stocks
            WHERE ticker = %s
            """,
            (ticker,)
        )

        existing = cursor.fetchone()

        if existing:

            # Update company / sector in case
            # Yahoo has newer information.

            cursor.execute(
                """
                UPDATE stocks
                SET
                    company_name = %s,
                    sector = %s
                WHERE ticker = %s
                """,
                (
                    fundamentals.get(
                        "company_name"
                    ),
                    fundamentals.get(
                        "sector"
                    ),
                    ticker
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO stocks
                (
                    ticker,
                    company_name,
                    sector
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    ticker,
                    fundamentals.get(
                        "company_name"
                    ),
                    fundamentals.get(
                        "sector"
                    )
                )
            )

        connection.commit()

    except mysql.connector.Error as error:

        if connection:
            connection.rollback()

        print(
            "Stock database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save stock information"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET HISTORY FROM MYSQL
# ============================================================

def get_history_from_database(
    ticker
):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # ====================================================
        # FIRST: TRY CLEANED HISTORY
        # ====================================================

        try:

            cursor.execute(
                """
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
                """,
                (ticker,)
            )

            rows = cursor.fetchall()

        except mysql.connector.Error as error:

            print(
                "Cleaned history query warning:",
                error
            )

            rows = []

        # ====================================================
        # IMPORTANT:
        # If cleaned table returns ZERO rows,
        # check the original price_history table.
        # ====================================================

        if not rows:

            print(
                f"No cleaned history found for {ticker}. "
                f"Checking price_history..."
            )

            try:

                cursor.execute(
                    """
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
                    """,
                    (ticker,)
                )

                rows = cursor.fetchall()

            except mysql.connector.Error as error:

                print(
                    "Original history query error:",
                    error
                )

                rows = []

        print(
            f"History rows found for {ticker}: "
            f"{len(rows)}"
        )

        return rows

    except mysql.connector.Error as error:

        print(
            "History database error:",
            error
        )

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# ============================================================
# SAVE YAHOO HISTORY
# ============================================================

def save_yahoo_history(
    ticker,
    history_df
):

    if (
        history_df is None
        or history_df.empty
    ):

        return

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        for index, row in history_df.iterrows():

            trade_date = index

            if isinstance(
                trade_date,
                pd.Timestamp
            ):

                trade_date = (
                    trade_date
                    .tz_localize(None)
                    if trade_date.tzinfo
                    else trade_date
                )

                trade_date = (
                    trade_date
                    .strftime("%Y-%m-%d")
                )

            else:

                trade_date = str(
                    trade_date
                )[:10]

            open_price = safe_number(
                row.get("Open")
            )

            high_price = safe_number(
                row.get("High")
            )

            low_price = safe_number(
                row.get("Low")
            )

            close_price = safe_number(
                row.get("Close")
            )

            volume = safe_number(
                row.get("Volume")
            )

            if close_price is None:
                continue

            # ------------------------------------------------
            # Update existing record / insert new record
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT ticker
                FROM price_history
                WHERE ticker = %s
                AND trade_date = %s
                """,
                (
                    ticker,
                    trade_date
                )
            )

            exists = cursor.fetchone()

            if exists:

                cursor.execute(
                    """
                    UPDATE price_history
                    SET
                        open_price = %s,
                        high_price = %s,
                        low_price = %s,
                        close_price = %s,
                        volume = %s
                    WHERE ticker = %s
                    AND trade_date = %s
                    """,
                    (
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                        ticker,
                        trade_date
                    )
                )

            else:

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

    except mysql.connector.Error as error:

        if connection:
            connection.rollback()

        print(
            "History save error:",
            error
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# FETCH / REFRESH ONE-YEAR HISTORY
# ============================================================

def fetch_and_store_history(
    ticker
):

    yahoo_ticker = f"{ticker}.NS"

    print(
        f"Fetching one-year history for {ticker}..."
    )

    try:

        stock = yf.Ticker(
            yahoo_ticker
        )

        history_df = stock.history(
            period="1y",
            interval="1d",
            auto_adjust=False
        )

        if (
            history_df is None
            or history_df.empty
        ):

            return pd.DataFrame()

        history_df = history_df[
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        ].copy()

        history_df = history_df.dropna(
            subset=["Close"]
        )

        save_yahoo_history(
            ticker,
            history_df
        )

        return history_df

    except Exception as error:

        print(
            "Yahoo history error:",
            error
        )

        return pd.DataFrame()


# ============================================================
# CALCULATE ANALYTICS
# ============================================================

def calculate_analytics(
    ticker
):

    fetch_and_store_history(ticker)

    rows = get_history_from_database(
        ticker
    )

    # --------------------------------------------------------
    # If no database history exists,
    # fetch from Yahoo.
    # --------------------------------------------------------

    if not rows:

        fetch_and_store_history(
            ticker
        )

        rows = get_history_from_database(
            ticker
        )

    if not rows:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No price history "
                f"available for {ticker}"
            )
        )

    df = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # Normalize columns
    # --------------------------------------------------------

    df["trade_date"] = pd.to_datetime(
        df["trade_date"]
    )

    df["close_price"] = pd.to_numeric(
        df["close_price"],
        errors="coerce"
    )

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["close_price"]
    )

    df = df.sort_values(
        "trade_date"
    )

    # --------------------------------------------------------
    # Daily return
    # --------------------------------------------------------

    df["daily_return"] = (
        df["close_price"]
        .pct_change()
    )

    returns = (
        df["daily_return"]
        .dropna()
    )

    # --------------------------------------------------------
    # Latest price
    # --------------------------------------------------------

    latest_price = safe_number(
        df["close_price"].iloc[-1]
    )

    # --------------------------------------------------------
    # Highest / lowest historical price
    # --------------------------------------------------------

    highest_price = safe_number(
        df["close_price"].max()
    )

    lowest_price = safe_number(
        df["close_price"].min()
    )

    # --------------------------------------------------------
    # Daily volatility
    # --------------------------------------------------------

    daily_volatility = None

    if len(returns) > 1:

        daily_volatility = safe_number(
            returns.std()
        )

    # --------------------------------------------------------
    # Annualized volatility
    # --------------------------------------------------------

    annualized_volatility = None

    if daily_volatility is not None:

        annualized_volatility = (
            daily_volatility *
            np.sqrt(252)
        )

    # --------------------------------------------------------
    # Annualized compounded return
    # --------------------------------------------------------

    annualized_return = None

    if (
        len(df) > 1
        and df["close_price"].iloc[0] > 0
        and df["close_price"].iloc[-1] > 0
    ):

        years = (
            len(df) - 1
        ) / 252

        if years > 0:

            annualized_return = (
                (
                    df["close_price"].iloc[-1]
                    /
                    df["close_price"].iloc[0]
                )
                ** (1 / years)
            ) - 1

    # --------------------------------------------------------
    # Running maximum
    # --------------------------------------------------------

    df["running_max"] = (
        df["close_price"]
        .cummax()
    )

    df["drawdown"] = (
        df["close_price"]
        /
        df["running_max"]
    ) - 1

    maximum_drawdown = safe_number(
        df["drawdown"].min()
    )

    # --------------------------------------------------------
    # Sharpe ratio
    #
    # Risk-free rate = 0 for this project.
    # --------------------------------------------------------

    sharpe_ratio = None

    if (
        annualized_return is not None
        and annualized_volatility is not None
        and annualized_volatility != 0
    ):

        sharpe_ratio = (
            annualized_return /
            annualized_volatility
        )

    # --------------------------------------------------------
    # Average volume
    # --------------------------------------------------------

    average_volume = None

    if (
        "volume" in df.columns
        and df["volume"].notna().any()
    ):

        average_volume = safe_number(
            df["volume"].mean()
        )

    # --------------------------------------------------------
    # Latest trade date
    # --------------------------------------------------------

    latest_trade_date = (
        df["trade_date"].iloc[-1]
    )

    if isinstance(
        latest_trade_date,
        pd.Timestamp
    ):

        latest_trade_date = (
            latest_trade_date
            .strftime("%Y-%m-%d")
        )

    else:

        latest_trade_date = str(
            latest_trade_date
        )

    return {

        "ticker":
            ticker,

        "latest_price":
            latest_price,

        "highest_price":
            highest_price,

        "lowest_price":
            lowest_price,

        "daily_volatility":
            daily_volatility,

        "annualized_volatility":
            annualized_volatility,

        "annualized_return":
            annualized_return,

        "maximum_drawdown":
            maximum_drawdown,

        "sharpe_ratio":
            sharpe_ratio,

        "average_volume":
            average_volume,

        "latest_trade_date":
            latest_trade_date,

        "history":
            df,

    }


# ============================================================
# UPDATE ANALYSIS SUMMARY
# ============================================================

def update_analysis_summary(
    ticker,
    sector,
    analytics,
    fundamentals
):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        values = (
            ticker,
            analytics.get("latest_price"),
            analytics.get("highest_price"),
            analytics.get("lowest_price"),
            analytics.get("daily_volatility"),
            analytics.get("annualized_volatility"),
            analytics.get("annualized_return"),
            analytics.get("maximum_drawdown"),
            analytics.get("sharpe_ratio"),
            analytics.get("average_volume"),
            fundamentals.get("market_cap"),
            fundamentals.get("pe_ratio"),
            fundamentals.get("dividend_yield"),
            fundamentals.get("quarterly_dividend"),
        )

        cursor.execute(
            """
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
            ON DUPLICATE KEY UPDATE
                latest_price = VALUES(latest_price),
                highest_price = VALUES(highest_price),
                lowest_price = VALUES(lowest_price),
                daily_volatility = VALUES(daily_volatility),
                annualized_volatility = VALUES(annualized_volatility),
                annualized_return = VALUES(annualized_return),
                maximum_drawdown = VALUES(maximum_drawdown),
                sharpe_ratio = VALUES(sharpe_ratio),
                average_volume = VALUES(average_volume),
                market_cap = VALUES(market_cap),
                pe_ratio = VALUES(pe_ratio),
                dividend_yield = VALUES(dividend_yield),
                quarterly_dividend = VALUES(quarterly_dividend)
            """,
            values
        )

        connection.commit()

        print(
            f"Analysis summary updated successfully for {ticker}"
        )

    except mysql.connector.Error as error:

        if connection:
            connection.rollback()

        print(
            "Analysis summary database error:",
            error
        )

        raise

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message":
            "Stock Market Analytics API is running",

        "status":
            "success",

        "data_source":
            "Yahoo Finance",

        "data_policy":
            "Latest available Yahoo Finance data"
    }


# ============================================================
# GET ALL STOCKS
# ============================================================

@app.get("/stocks")
def get_stocks():

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                ticker,
                company_name,
                sector
            FROM stocks
            ORDER BY ticker
            """
        )

        return cursor.fetchall()

    except mysql.connector.Error as error:

        print(
            "Database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve stocks"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET / REFRESH ANALYSIS FOR ONE STOCK
# ============================================================

@app.get("/stocks/{ticker}")
def get_stock_analysis(
    ticker: str
):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    if not ticker:

        raise HTTPException(
            status_code=400,
            detail="Ticker cannot be empty"
        )

    # --------------------------------------------------------
    # FIRST:
    # Fetch current Yahoo fundamentals.
    #
    # This is the key change.
    # --------------------------------------------------------

    fundamentals = (
        fetch_current_fundamentals(
            ticker
        )
    )

    # --------------------------------------------------------
    # Ensure stock exists in MySQL.
    # --------------------------------------------------------

    ensure_stock_exists(
        ticker,
        fundamentals
    )

    # --------------------------------------------------------
    # Get / calculate historical analytics.
    # --------------------------------------------------------

    analytics = calculate_analytics(
        ticker
    )
        # --------------------------------------------------------
    # Get today's latest available intraday market price.
    # --------------------------------------------------------

    intraday_data = fetch_latest_intraday_data(
        ticker
    )

    if intraday_data:

        analytics["latest_price"] = (
            intraday_data.get(
                "latest_price"
            )
        )

        analytics["latest_trade_date"] = (
            intraday_data.get(
                "latest_trade_date"
            )
        )

        analytics["latest_trade_time"] = (
            intraday_data.get(
                "latest_trade_time"
            )
        )

        analytics["latest_volume"] = (
            intraday_data.get(
                "latest_volume"
            )
        )

    # --------------------------------------------------------
    # Update MySQL summary with the NEW fundamentals.
    # --------------------------------------------------------

    update_analysis_summary(
        ticker,
        fundamentals.get("sector"),
        analytics,
        fundamentals
    )

    # --------------------------------------------------------
    # Build history response.
    # --------------------------------------------------------

    history_df = analytics.get(
        "history"
    )

    history = []

    if (
        history_df is not None
        and not history_df.empty
    ):

        for _, row in history_df.iterrows():

            trade_date = row[
                "trade_date"
            ]

            if isinstance(
                trade_date,
                pd.Timestamp
            ):

                trade_date = (
                    trade_date
                    .strftime("%Y-%m-%d")
                )

            else:

                trade_date = str(
                    trade_date
                )

            close_price = safe_number(
                row["close_price"]
            )

            if close_price is not None:

                history.append(
                    {
                        "trade_date":
                            trade_date,

                        "close_price":
                            close_price
                    }
                )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    result = {

        "ticker":
            ticker,

        "company_name":
            fundamentals.get(
                "company_name"
            ),

        "sector":
            fundamentals.get(
                "sector"
            ),

        "industry":
            fundamentals.get(
                "industry"
            ),

        # Current Yahoo fundamentals
        "market_cap":
            fundamentals.get(
                "market_cap"
            ),

        "pe_ratio":
            fundamentals.get(
                "pe_ratio"
            ),

        "dividend_yield":
            fundamentals.get(
                "dividend_yield"
            ),

        "annual_dividend":
            fundamentals.get(
                "annual_dividend"
            ),

        "latest_dividend":
            fundamentals.get(
                "latest_dividend"
            ),

        "quarterly_dividend":
            fundamentals.get(
                "quarterly_dividend"
            ),

        "fifty_two_week_high":
            fundamentals.get(
                "fifty_two_week_high"
            ),

        "fifty_two_week_low":
            fundamentals.get(
                "fifty_two_week_low"
            ),

        # Analytics
        "latest_price":
            analytics.get(
                "latest_price"
            ),

        "highest_price":
            analytics.get(
                "highest_price"
            ),

        "lowest_price":
            analytics.get(
                "lowest_price"
            ),

        "daily_volatility":
            analytics.get(
                "daily_volatility"
            ),

        "annualized_volatility":
            analytics.get(
                "annualized_volatility"
            ),

        "annualized_return":
            analytics.get(
                "annualized_return"
            ),

        "maximum_drawdown":
            analytics.get(
                "maximum_drawdown"
            ),

        "sharpe_ratio":
            analytics.get(
                "sharpe_ratio"
            ),

        "average_volume":
            analytics.get(
                "average_volume"
            ),

        "latest_trade_date":
            analytics.get(
                "latest_trade_date"
            ),

        "data_source":
            fundamentals.get(
                "data_source"
            ),

        "data_refreshed_at":
            fundamentals.get(
                "data_refreshed_at"
            ),

        "history":
            history,

    }

    return {
        key: json_safe(value)
        if key != "history"
        else value
        for key, value in result.items()
    }


# ============================================================
# GET PRICE HISTORY
# ============================================================

# ============================================================
# GET PRICE HISTORY
# ============================================================

@app.get("/stocks/{ticker}/history")
def get_stock_history(ticker: str):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    rows = get_history_from_database(
        ticker
    )

    # --------------------------------------------------------
    # If database has no history, fetch from Yahoo
    # --------------------------------------------------------

    if not rows:

        fetch_and_store_history(
            ticker
        )

        rows = get_history_from_database(
            ticker
        )

    if not rows:

        raise HTTPException(
            status_code=404,
            detail="Price history not found"
        )

    result = []

    # --------------------------------------------------------
    # Convert database rows into JSON-friendly data
    # --------------------------------------------------------

    for row in rows:

        trade_date = row.get(
            "trade_date"
        )

        if hasattr(
            trade_date,
            "strftime"
        ):

            trade_date = (
                trade_date.strftime(
                    "%Y-%m-%d"
                )
            )

        else:

            trade_date = str(
                trade_date
            )

        close_price = safe_number(
            row.get(
                "close_price"
            )
        )

        volume = safe_number(
            row.get(
                "volume"
            )
        )

        open_price = safe_number(
            row.get(
                "open_price"
            )
        )

        high_price = safe_number(
            row.get(
                "high_price"
            )
        )

        low_price = safe_number(
            row.get(
                "low_price"
            )
        )

        if close_price is None:
            continue

        result.append(
            {
                "date":
                    trade_date,

                "open":
                    open_price,

                "high":
                    high_price,

                "low":
                    low_price,

                "close":
                    close_price,

                "volume":
                    volume,
            }
        )

    return result
# ============================================================
# SEARCH
# ============================================================

@app.get("/search/{ticker}")
def search_stock(
    ticker: str
):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                ticker,
                company_name,
                sector
            FROM stocks
            WHERE ticker = %s
            """,
            (ticker,)
        )

        row = cursor.fetchone()

        if row:

            return {
                "found":
                    True,

                "stock":
                    row
            }

        return {
            "found":
                False,

            "ticker":
                ticker
        }

    except mysql.connector.Error as error:

        print(
            "Search database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Search failed"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# DYNAMIC STOCK FETCH
# ============================================================

@app.post("/stocks/{ticker}/fetch")
def fetch_new_stock(
    ticker: str
):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    if not ticker:

        raise HTTPException(
            status_code=400,
            detail="Ticker cannot be empty"
        )

    # --------------------------------------------------------
    # Fetch current Yahoo data.
    # --------------------------------------------------------

    fundamentals = (
        fetch_current_fundamentals(
            ticker
        )
    )

    # --------------------------------------------------------
    # Save / update stock.
    # --------------------------------------------------------

    ensure_stock_exists(
        ticker,
        fundamentals
    )

    # --------------------------------------------------------
    # Fetch history.
    # --------------------------------------------------------

    history_df = fetch_and_store_history(
        ticker
    )

    # --------------------------------------------------------
    # Calculate analytics.
    # --------------------------------------------------------

    analytics = calculate_analytics(
        ticker
    )

    # --------------------------------------------------------
    # Update summary.
    # --------------------------------------------------------

    update_analysis_summary(
        ticker,
        fundamentals.get("sector"),
        analytics,
        fundamentals
    )

    return {

        "message":
            "Stock fetched and refreshed successfully",

        "ticker":
            ticker,

        "company_name":
            fundamentals.get(
                "company_name"
            ),

        "sector":
            fundamentals.get(
                "sector"
            ),

        "market_cap":
            fundamentals.get(
                "market_cap"
            ),

        "pe_ratio":
            fundamentals.get(
                "pe_ratio"
            ),

        "dividend_yield":
            fundamentals.get(
                "dividend_yield"
            ),

        "quarterly_dividend":
            fundamentals.get(
                "quarterly_dividend"
            ),

        "latest_price":
            fundamentals.get(
                "latest_price"
            ),

        "data_source":
            "Yahoo Finance",

    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    connection = None

    try:

        connection = get_connection()

        if connection.is_connected():

            return {

                "status":
                    "healthy",

                "database":
                    "connected"

            }

    except Exception as error:

        print(
            "Health check error:",
            error
        )

    finally:

        if connection:
            connection.close()

    return {

        "status":
            "unhealthy",

        "database":
            "disconnected"

    }


# ============================================================
# RUN WITH:
#
# uvicorn main:app --reload
#
# ============================================================