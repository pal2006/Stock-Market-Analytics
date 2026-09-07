import pandas as pd
import matplotlib.pyplot as plt
import os

# Create folder for charts
os.makedirs("Data/Charts", exist_ok=True)

# Load sector summary
df = pd.read_csv("Data/Processed/sector_summary.csv")


# -------------------------------
# Chart 1: Annualized Return
# -------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    df["Sector"],
    df["Annualized_Return"] * 100
)

plt.title("Annualized Return by Sector")
plt.xlabel("Sector")
plt.ylabel("Annualized Return (%)")

plt.tight_layout()

plt.savefig(
    "Data/Charts/sector_annualized_return.png",
    dpi=300
)

plt.show()
plt.close()


# -------------------------------
# Chart 2: Annualized Volatility
# -------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    df["Sector"],
    df["Annualized_Volatility"] * 100
)

plt.title("Annualized Volatility by Sector")
plt.xlabel("Sector")
plt.ylabel("Annualized Volatility (%)")

plt.tight_layout()

plt.savefig(
    "Data/Charts/sector_annualized_volatility.png",
    dpi=300
)

plt.show()
plt.close()


# -------------------------------
# Chart 3: Maximum Drawdown
# -------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    df["Sector"],
    df["Maximum_Drawdown"] * 100
)

plt.title("Maximum Drawdown by Sector")
plt.xlabel("Sector")
plt.ylabel("Maximum Drawdown (%)")

plt.tight_layout()

plt.savefig(
    "Data/Charts/sector_maximum_drawdown.png",
    dpi=300
)

plt.show()
plt.close()


# -------------------------------
# Chart 4: Sharpe Ratio
# -------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    df["Sector"],
    df["Sharpe_Ratio"]
)

plt.title("Sharpe Ratio by Sector")
plt.xlabel("Sector")
plt.ylabel("Sharpe Ratio")

plt.tight_layout()

plt.savefig(
    "Data/Charts/sector_sharpe_ratio.png",
    dpi=300
)

plt.show()
plt.close()


print("\nAll charts saved successfully!")