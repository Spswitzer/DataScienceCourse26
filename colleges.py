
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
collegesFact = pd. read_csv('hd2024.csv')
collegesFactLookup = pd. read_excel(
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
tuition_columns = [
    'Tuition and fees for 2021-22',
    'Tuition and fees for 2022-23',
    'Tuition and fees for 2023-24',
    'Tuition and fees for 2024-25'
]

# Calculate average tuition costs for each year
average_tuition = collegeDf[tuition_columns].mean()
average_tuition

# Years for the x-axis
years = ['2021-22', '2022-23', '2023-24', '2024-25']

# Average tuition costs for the y-axis
average_costs = [7738.21, 7928.92, 8343.08, 8548.54]

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
pandas_joined.style.format({"tuition": "${x/1000:.0f}K"})


pandasNames = pandas_joined.query("year == '2024-25'")

# p = (
#     ggplot(data = pandas_joined,
#     mapping = aes(x="year", 
#     y= "tuition", 
#     group="Name")) +
#     geom_line(
#         color="grey"
#         , alpha=0.5) +
#     geom_text(data = pandasNames, 
#     mapping =  aes(label = 'Name', 
#     y="tuition" + 500,
#     ), 
#     size = 6) + 
#     labs(
#         title="Tuition over time for Red Rocks Community College and peers",
#         x="Academic Year",
#         y="Mean Tuition",
#     )
#     + theme(axis_text_x=element_text(rotation=45, hjust=1), 
#     legend_position = "none")
# )

# p

# select the tuition variables
# cols = [c for c in df.columns if c.startswith("Tuition and fees for")]

# # Pivot to a long format
# long = (
#     df.loc[:, ["Unit Id", "Name"] + cols]
#       .melt(id_vars=["Unit Id", "Name"],
#             value_vars=cols,
#             var_name="year",
#             value_name="tuition")
# )

# # remove the prefix from the year variable
# long["year"] = long["year"].str.replace("Tuition and fees for ", "")

# overall = long.groupby("year")["tuition"] \
#               .mean().reset_index(name="mean_tuition_all")

# per_school = (
#     long.groupby(["Name","year"])["tuition"]
#         .mean()
#         .reset_index(name="mean_tuition_school")
# )

# # pivot so years are columns
# pivot = per_school.pivot(index="Name", columns="year", values="mean_tuition_school")

# # sort years to ensure first and last
# years = sorted(pivot.columns)
# start, end = years[0], years[-1]
# pivot = pivot.dropna(subset=[start, end])  # drop schools missing either

# pivot["abs_change"] = pivot[end] - pivot[start]
# pivot["pct_change"] = pivot["abs_change"] / pivot[start] * 100

# # find extremes
# max_abs = pivot["abs_change"].idxmax(), pivot["abs_change"].max()
# min_abs = pivot["abs_change"].idxmin(), pivot["abs_change"].min()
# max_pct = pivot["pct_change"].idxmax(), pivot["pct_change"].max()
# min_pct = pivot["pct_change"].idxmin(), pivot["pct_change"].min()

# max_abs, min_abs, max_pct, min_pct

# # start from the per_school pandas DataFrame
# pivot = per_school.pivot(index="Name", columns="year",
#                          values="mean_tuition_school")

# years = sorted(pivot.columns)
# start, end = years[0], years[-1]

# # drop any school missing either endpoint
# pivot = pivot.dropna(subset=[start, end])

# pivot["abs_change"] = pivot[end] - pivot[start]
# pivot["pct_change"] = pivot["abs_change"] / pivot[start] * 100

# # extremes
# max_abs = pivot["abs_change"].idxmax(), pivot["abs_change"].max()
# min_abs = pivot["abs_change"].idxmin(), pivot["abs_change"].min()
# max_pct = pivot["pct_change"].idxmax(), pivot["pct_change"].max()
# min_pct = pivot["pct_change"].idxmin(), pivot["pct_change"].min()
# max_abs, min_abs, max_pct, min_pct

# pivot.sort_values("abs_change", ascending=False).head()
# pivot.sort_values("abs_change").head()
# pivot.sort_values("pct_change", ascending=False).head()
# pivot.sort_values("pct_change").head()

# # Seaborn example


# sns.set_style("whitegrid")


# # Set up the figure size (optional, but helps with readability)
# plt.figure(figsize=(10, 6))

# # Base Plot 
# ax = sns.lineplot(
#     data=pandas_joined, 
#     x='year', 
#     y='tuition', 
#     units='Name', 
#     estimator=None, 
#     color='grey', 
#     alpha=0.5,
#     legend=False 
# )

# # Loop through the pandasNames dataframe to place the text
# latest_years_idx = pandasNames.groupby('Name')['year'].idxmax()
# end_points = pandasNames.loc[latest_years_idx]

# for index, row in end_points.iterrows():
#     ax.text(
#         x=row['year'], 
#         y=row['tuition'] + 10, 
#         s=row['Name'],          
#         fontsize=12,            
#         ha='left'      
#     )

# # labels
# ax.set_title("Tuition over time for Red Rocks Community College and peers")
# ax.set_xlabel("Academic Year")
# ax.set_ylabel("Mean Tuition")
# plt.xticks(rotation=0, ha='right')

# # Automatically adjust padding so labels don't get cut off
# plt.tight_layout()

# # Display the plot
# plt.show()

# ## Seaborn with ggrepel equivalent
# from adjust_text import adjust_text

# # 1. Standard Plotting
# plt.figure(figsize=(10, 6))
# ax = sns.lineplot(data=pandas_joined, x='year', y='tuition', units='Name', 
#                   estimator=None, color='grey', alpha=0.5)

# # 2. Prepare the labels
# # We'll use the "latest year" logic from the previous step
# latest_years_idx = pandasNames.groupby('Name')['year'].idxmax()
# end_points = pandasNames.loc[latest_years_idx]

# texts = []
# for index, row in end_points.iterrows():
#     # Create the text objects but don't worry about overlap yet
#     texts.append(plt.text(row['year'], row['tuition'] + 10, row['Name'], fontsize=10))

# # 3. The Magic Step: Adjust all labels simultaneously
# # 'expand_points' and 'expand_text' control how far labels stay from data/each other
# adjust_text(texts, 
#             arrowprops=dict(arrowstyle='->', color='red', lw=0.5),
#             expand_points=(1.5, 1.5), 
#             expand_text=(1.2, 1.2))

# # 4. Final Touches
# ax.set_title("Tuition over time (Auto-adjusted Labels)")
# plt.xticks(rotation=0, ha='right')
# plt.tight_layout()
# plt.show()


# #Highlight Red Rocks Community College
# import seaborn as sns
# import matplotlib.pyplot as plt
# from adjust_text import adjust_text

#  Define your target and colors
target_name = "Red Rocks"
# Create a dictionary: { 'School Name': 'color' }
# We set the target to a bold color and everyone else to 'black'
palette = {name: "crimson" if name == target_name else "black" for name in pandas_joined['Name'].unique()}
# We also want the target line to be thicker
size_map = {name: 3 if name == target_name else 1 for name in pandas_joined['Name'].unique()}

plt.figure(figsize=(10, 6))

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
        fontsize=9 if is_target else 9,
        weight='bold' if is_target else 'normal',
        color='crimson' if is_target else 'gray',
        bbox=dict(facecolor='white', alpha=0.5, pad=10)
    ))


#  Final Styling
ax.set_title(f"Tuition Trends: {target_name} vs. Peers", fontsize=14, pad=20)
plt.xticks(rotation=0, ha='right')
sns.despine() # Removes the top and right borders for a cleaner look
plt.tight_layout()
plt.show()


# Geospatial plot
import pygris
import matplotlib.pyplot as plt
# Ensure installed in this kernel (run in a notebook cell)
%pip install mapclassify

# sanity check: returns a spec object if available
import importlib.util
importlib.util.find_spec("mapclassify")

# import using correct name
import mapclassify as mc

# inspect location (returns the module path)
mc.__file__
#>>> mc.__file__
#'C:\\Users\\sswitzer\\AppData\\Local\\Python\\pythoncore-3.14-64\\Lib\\site-packages\\mapclassify\\__init__.py'

# 1. Get Colorado State Shapefile
co_state = pygris.counties(state="CO", year=2023)

# 2. Plot the shape
co_state.plot()
plt.title("Colorado State Boundary")
plt.show()

# 3. Get Colorado County Shapefiles
co_counties = pygris.counties(state="CO", year=2025)
coMap = co_counties.plot()
plt.title("Colorado Counties")
plt.show()

gdf_points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE),
    crs="EPSG:4326" # Standard CRS for lat/lon
)

gdf_points.explore(m = coMap, 
    color="red",
    marker_kwds={"radius": 7}, # Style the points
    tooltip=["Name", "LATITUDE", "LONGITUDE"], # Add point-specific tooltips
    name="Cities" # Name for layer control
)