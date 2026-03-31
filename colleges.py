
from matplotlib.pyplot import fill
from locale import currency
from pandas.io.formats.style import jinja2
from sympy-stubs.physics.units import Unit
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Load the college fact table
collegesFact = pd.read_csv('hd2024.csv')
collegesFactLookup = pd.read_excel(
    'hd_dict_2024.xlsx', 
    sheet_name='Varlist')

print(collegesFact.columns)

# Select columns used for the analysis
collegeFactDf = collegesFact[['UNITID', 'INSTNM', 'STABBR',
     'WEBADDR', 'SECTOR', 'ICLEVEL','CONTROL', 'HLOFFER',
       'UGOFFER', 'OPENPUBL', 'LATITUDE', 'LONGITUD']]

# Filter the schools in CO
collegeCo =  collegeFactDf[collegeFactDf['STABBR'] == 'CO']

# Load the college dimension table
collegeDim = pd.read_csv('cost_2024.csv')
collegesDimLookup = pd. read_excel(
    'cost_dict_2024.xlsx', 
    sheet_name='Varlist')

# Select columns used for the analysis
collegeDimDF = collegeDim[['UNITID', 'APPLFEEU',
'PRMPGM', 'TUITPL1', 'TUITPL2', 'TUITPL3', 
'TUITION1',
'CHG2AY0', 'CHG2AY1', 'CHG2AY2', 'CHG2AY3',
'CHG4AY0',  'CHG4AY1','CHG4AY2', 'CHG4AY3']]

# Merge the fact and dimension tables & Filter
collegeDf = pd.merge(collegeCo, 
collegeDimDF, 
on='UNITID', 
how='left'
).query('CONTROL == 1').query('ICLEVEL == 1').query('SECTOR == 1').query('TUITION1.notnull()').drop(columns=['STABBR', 'TUITION1', 'CONTROL', 'ICLEVEL', 'SECTOR', 'UGOFFER', 'OPENPUBL'])

#print(collegeDf.columns.tolist())
# Create dictionary for renaming columns
renameDict = ['Unit Id', 'Name', 'Web Address', 'Highest Level Offered',
'LATITUDE', 'LONGITUDE',
'Application Fee - Undergraduate', 'Promise Program',
'Tuition guarantee', 'Prepaid tuition plan', 
'Tuition payment plan', 
'Tuition and fees for 2021-22', 'Tuition and fees for 2022-23',
'Tuition and fees for 2023-24', 'Tuition and fees for 2024-25',
'Books and supplies for 2021-22', 'Books and supplies for 2022-23', 
'Books and supplies for 2023-24', 'Books and supplies for 2024-25']

colNamesDict = dict(zip(list(collegeDf.columns), renameDict))

collegeDf.columns = renameDict

# Extract relevant columns for tuition costs
tuition_columns = [c for c in df.columns if c.startswith("Tuition and fees for")]

# Calculate average tuition costs for each year
average_tuition = collegeDf[tuition_columns].mean().rename('average_tuition')
average_tuition

# Years for the x-axis
years = ['2021-22', 
        '2022-23', 
        '2023-24', 
        '2024-25']

# Average tuition costs for the y-axis
average_costs = average_tuition.tolist()

#Copy the dataframe to use the simple name df for plotting
df = collegeDf.copy()

# Identify tuition columns
cols = [c for c in df.columns if c.startswith("Tuition and fees for")]

# transform the data into a long format
long = (
    df.loc[:, ["Unit Id", "Name"] + cols]
    .melt(id_vars=["Unit Id", "Name"], value_vars=cols,
          var_name="year", value_name="tuition")
)
# extract year
long["year"] = long["year"].str.replace("Tuition and fees for ", "")
long.head()

# compute overall mean by year and per-school mean over time
overall = long.groupby("year")["tuition"].mean().reset_index(name="mean_tuition_all")
per_school = (
    long.groupby(["Name", "year"])["tuition"]
    .mean()
    .reset_index(name="mean_tuition_school")
)

overall.head(), per_school.head()

# let's check if plotnine is already installed via import attempt
#pip install polars[all]

from plotnine import *
import polars as pl
import pyarrow as pyarrow
from matplotlib.ticker import FuncFormatter
# let's create polars DataFrame equivalent to increase performance for plotting
pl_df = pl.from_pandas(long)
pl_overall = pl.from_pandas(overall)

joined = (
    pl_df.join(pl_overall, on="year", how="left")
    .with_columns(
        (pl.col("tuition") - pl.col("mean_tuition_all")).alias("diff_from_overall")
    )
)

# Filter to front range schools

frontRange = collegeDf.query('-105.5 <= LONGITUDE <= -104.5').query("Name.str.contains('Community College')")['Unit Id'].tolist()

joinedFiltered = joined.filter(pl.col("Unit Id").is_in(frontRange))


# then convert to pandas dataframe
pandas_joined = joinedFiltered.to_pandas()

pandas_joined["Name"] = pandas_joined["Name"].str.replace(r"\s*Community College\s*$", "", regex=True)
pandas_joined["Name"] = pandas_joined["Name"].str.replace(r"Community College of ", "", regex=True)

# Format the 'Price' column for display
pandasNames = pandas_joined.query("year == '2024-25'")

#  Define your target and colors
target_name = "Red Rocks"
# Create a dictionary: { 'School Name': 'color' }
## Set the target to a bold color and everyone else to 'black'
palette = {name: "crimson" if name == target_name else "black" for name in pandas_joined['Name'].unique()}
# We also want the target line to be thicker
size_map = {name: 3 if name == target_name else 1 for name in pandas_joined['Name'].unique()}

plt.figure(figsize=(10, 6))
plt.xlabel('year'.title())
plt.ylabel('tuition'.title())

#  Plot with 'hue' and 'size'
ax = sns.lineplot(
    data=pandas_joined, 
    x='year', 
    y='tuition', 
    hue='Name', 
    marker='o',  # 'o' for circles, 's' for squares, 'D' for diamonds
    markersize=6,
    palette=palette,
    size='Name',
    sizes=size_map,
    legend=False
)

#  Handle Labels with adjust_text
latest_years_idx = pandasNames.groupby('Name')['year'].idxmax()
end_points = pandasNames.loc[latest_years_idx]

texts = []
for index, row in end_points.iterrows():
    # Only label the highlight in bold/color, or label all but style the target differently
    is_target = row['Name'] == target_name
    texts.append(plt.text(
        row['year'], 
        row['tuition'], 
        row['Name'], 
        fontsize=10 if is_target else 9,
        weight='bold' if is_target else 'normal',
        color='crimson' if is_target else 'gray',
        bbox=dict(facecolor='white', alpha=0.5, pad=10)
    ))


#  Final Styling
ax.set_title(f"Tuition Trends: {target_name} vs. Peers", fontsize=14, pad=20)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x/1000:.0f}K'))
plt.xticks(rotation=0, ha='right')
sns.despine() # Removes the top and right borders for a cleaner look
plt.tight_layout()
plt.show()


# Geospatial plot
import pygris
import matplotlib.pyplot as plt

#%pip install mapclassify
#%pip install "folium>=0.12"
#importlib.util.find_spec("mapclassify")
#import importlib.util
import mapclassify as mc

# inspect location (returns the module path)
#mc.__file__
#>>> mc.__file__
#'C:\\Users\\sswitzer\\AppData\\Local\\Python\\pythoncore-3.14-64\\Lib\\site-packages\\mapclassify\\__init__.py'

# Access Colorado State Shapefile
co_state = pygris.counties(state="CO", year=2023)

# Plot the shape county shapes
coMap2 = co_state.explore(tiles="CartoDB positron", 
    style_kwds={
     'color': 'grey',
     'weight': 1,
     'fill': 'lightgrey'},
tooltip=False, 
popup=False)


gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE))

from matplotlib.ticker import StrMethodFormatter

gdf_points.explore(m=coMap2, 
    tooltip=False, 
    popup=["Name", "Tuition and fees for 2024-25"], 
    column='Tuition and fees for 2024-25',
    scheme='MaximumBreaks', 
    legend=True, 
    cmap='Reds', 
# set the legend title and format the values as currency
    legend_kwds={'title': 'Tuition (2024-25)', 
    'format': StrMethodFormatter('${x:,.0f}')}
    )



# Calculate stats ----
import pandas as pd
import numpy as np
# --- BETWEEN SCHOOLS (Current Year Analysis) ---
longDf = long.copy()

longDf['year'] = longDf['year'].str.split('-').str[-1]
longDf['year'] = pd.to_numeric(longDf['year'], errors='coerce')


df_latest = longDf[longDf['year'] == 25].copy()

## Calculate the mean and coefficient of variation (CV) for the most recent year ----
mean_price = df_latest['tuition'].mean()
cv = (df_latest['tuition'].std() / mean_price) * 100

print(f"Average Net Price: ${mean_price:,.2f}")

if cv < 16:
    interpretation = "Low variability in prices across schools"
elif 16 <= cv < 33.3:
    interpretation = "Moderate variability in prices across schools"
else:
    interpretation = "High variability in prices across schools"
print(f"Price coefficient of variation: {cv:.0f}%")
print(interpretation)
#### WITHIN ONE SCHOOL (Trend Analysis) ----
univ_a = longDf[longDf['Name'] == 'Red Rocks Community College'].sort_values('year')
univ_a['YoY_Change'] = univ_a['tuition'].pct_change() * 100

#### College Annual Growth Rate (CAGR) Calculation: ((End / Start) ^ (1/n)) - 1 ----
n_years = univ_a['year'].max() - univ_a['year'].min()
cagr = ((univ_a.iloc[-1]['tuition'] / univ_a.iloc[0]['tuition']) ** (1/n_years) - 1) * 100

print(f"Annual Growth Rate (CAGR): {cagr:.2f}%")
