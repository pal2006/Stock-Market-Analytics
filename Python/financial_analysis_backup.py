import pandas as pd
import os

# List of companies
companies = [
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "RELIANCE",
    "SUNPHARMA"
]

# Risk-free rate assumption
risk_free_rate = 0.06

# Process each company
for company in companies:

    print(f"\n{'=' * 50}")
    print(f"Analyzing {company}")
    print(f"{'=' * 50}")

    # Load cleaned data
    file_path = f"Data/Processed/{company}_cleaned.csv"
    df = pd.read_csv(file_path)

    # Convert Date to datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Calculate daily return
    df["Daily_Return"] = df["Close"].pct_change()

    # Calculate moving averages
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()

    # Calculate daily volatility
    daily_volatility = df["Daily_Return"].std()

    # Calculate annualized volatility
    annualized_volatility = daily_volatility * (252 ** 0.5)

    # Calculate 20-day rolling volatility
    df["Rolling_Volatility_20D"] = (
        df["Daily_Return"].rolling(window=20).std()
    )

    # Calculate running maximum
    df["Running_Max"] = df["Close"].cummax()

    # Calculate drawdown
    df["Drawdown"] = (
        (df["Close"] - df["Running_Max"])
        / df["Running_Max"]
    )

    # Calculate maximum drawdown
    maximum_drawdown = df["Drawdown"].min()

    # Calculate annualized return
    annualized_return = df["Daily_Return"].mean() * 252

    # Calculate Sharpe Ratio
    sharpe_ratio = (
        (annualized_return - risk_free_rate)
        / annualized_volatility
    )

    # Display results
    print(f"Daily Volatility: {daily_volatility * 100:.2f}%")
    print(f"Annualized Volatility: {annualized_volatility * 100:.2f}%")
    print(f"Annualized Return: {annualized_return * 100:.2f}%")
    print(f"Maximum Drawdown: {maximum_drawdown * 100:.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

    # Save analytical dataset
    output_path = f"Data/Processed/{company}_analysis.csv"
    df.to_csv(output_path, index=False)

    print(f"{company} analysis saved successfully!")

print("\nAll stock analysis completed successfully!")