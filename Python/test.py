import pandas as pd

data = {
    "Stock": ["TCS", "HDFC Bank", "Reliance"],
    "Price": [3500, 1750, 1400]
}

df = pd.DataFrame(data)

print(df)