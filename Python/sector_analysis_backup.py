import pandas as pd

# Load stock summary
df = pd.read_csv("Data/Processed/stock_summary.csv")

# Calculate sector-level averages
sector_summary = (
    df.groupby("Sector")
    .agg({
        "Annualized_Return": "mean",
        "Annualized_Volatility": "mean",
        "Maximum_Drawdown": "mean",
        "Sharpe_Ratio": "mean"
    })
    .reset_index()
)

# Display sector summary
print("Sector Summary:")
print(sector_summary)

# Save sector summary
sector_summary.to_csv(
    "Data/Processed/sector_summary.csv",
    index=False
)

print("\nSector summary saved successfully!")