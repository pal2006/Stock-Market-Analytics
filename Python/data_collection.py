import yfinance as yf
import pandas as pd

# List of stocks we want to collect
stocks = {
    "TCS.NS": "TCS",
    "INFY.NS": "INFY",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
    "RELIANCE.NS": "RELIANCE",
    "SUNPHARMA.NS": "SUNPHARMA"
}

# Download data for each stock
for ticker, company_name in stocks.items():

    print(f"\nDownloading {company_name}...")

    data = yf.download(
        ticker,
        start="2024-01-01",
        end="2026-01-01",
        auto_adjust=False
    )

    # Remove multi-level column headers
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Convert the date index into a normal column
    data.reset_index(inplace=True)

    # Save the raw data
    file_path = f"Data/Raw/{company_name}.csv"
    data.to_csv(file_path, index=False)

    print(f"{company_name} data saved successfully!")

print("\nAll stock data downloaded successfully!")