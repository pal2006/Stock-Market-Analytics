import pandas as pd

# Stock and sector information
stock_sectors = {
    "TCS": "IT",
    "INFY": "IT",
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "RELIANCE": "Energy",
    "SUNPHARMA": "Healthcare"
}

summary = []

# Read each analysis file
for company, sector in stock_sectors.items():

    file_path = f"Data/Processed/{company}_analysis.csv"
    df = pd.read_csv(file_path)

    # Calculate metrics
    daily_volatility = df["Daily_Return"].std()
    annualized_volatility = daily_volatility * (252 ** 0.5)

    annualized_return = df["Daily_Return"].mean() * 252

    maximum_drawdown = df["Drawdown"].min()

    risk_free_rate = 0.06

    sharpe_ratio = (
        (annualized_return - risk_free_rate)
        / annualized_volatility
    )

    # Add results to summary
    summary.append({
        "Stock": company,
        "Sector": sector,
        "Annualized_Return": annualized_return,
        "Annualized_Volatility": annualized_volatility,
        "Maximum_Drawdown": maximum_drawdown,
        "Sharpe_Ratio": sharpe_ratio
    })

# Create summary DataFrame
summary_df = pd.DataFrame(summary)

# Save summary dataset
summary_df.to_csv(
    "Data/Processed/stock_summary.csv",
    index=False
)

print("\nStock Summary:")
print(summary_df)

print("\nStock summary saved successfully!")