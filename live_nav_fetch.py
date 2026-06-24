import requests
import pandas as pd

url = "https://api.mfapi.in/mf/125497"

response = requests.get(url)

data = response.json()

nav_df = pd.DataFrame(data["data"])

nav_df.to_csv("data/raw/hdfc_top100_nav.csv", index=False)

print("NAV data saved successfully!")
print(nav_df.head())