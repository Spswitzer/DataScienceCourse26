
from census import Census
import pandas as pd

#Link to download tables https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03
#https://www2.census.gov/data/api-documentation/api-user-guide.pdf


# Initialize client and fetch data
KEY = "064bbbe2c8d86ad57225b86c254bc9cf1f8de0b0"

# access the most recent year of data available, starting with 2025 and going back to 2021 if needed
for year in (2025, 2024, 2023, 2022, 2021):
    try:
        c = Census(KEY, year=year)
        data = c.acs1.get(("NAME", "DP01001A" ), {"for": "state:*"}) #"B01003_001E"
        break
    except Exception as e:
        last_err = e
else:
    raise last_err

# Convert to DataFrame
df = pd.DataFrame(data)
print(df.head())


# access 2025 data for all states
c = Census(KEY, year=2025)

# access results for multiple variables (e.g., total population and median income)
# Try recent years and use ACS table variable IDs (B01003_001E = total pop, B19013_001E = median household income)
years = (2025, 2024, 2023, 2022, 2021)
for year in years:
    try:
        c = Census(KEY, year=year)
        data = c.acs5.get(("NAME", "B01003_001E", "B19013_001E"), {"for": "state:*"})
        break
    except Exception as e:
        last_err = e
else:
    raise last_err

df = pd.DataFrame(data)
df = df.rename(columns={
    "B01003_001E": "total_population",
    "B19013_001E": "median_household_income"
})
df["total_population"] = pd.to_numeric(df["total_population"], errors="coerce")
df["median_household_income"] = pd.to_numeric(df["median_household_income"], errors="coerce")

# Return the DataFrame for interactive use
df


dataset = c.acs5

# Get all tables/variables as a pandas DataFrame
all_variables = pd.DataFrame(dataset.tables())

# Filter by keyword (e.g., 'MORTGAGE STATUS')
keyword = 'poverty status'
criteria = all_variables['description'].str.contains(keyword.title())
relevant_variables = all_variables[criteria]

# Print the resulting variable codes and descriptions
print(relevant_variables[['name', 'description']])
