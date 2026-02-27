from locale import currency
from pandas.io.formats.style import jinja2
from sympy-stubs.physics.units import Unit
import pandas as pd
# Load the college fact table
collegesFact = pd. read_csv('hd2024.csv')
collegesFactLookup = pd. read_excel(
    'hd_dict_2024.xlsx', 
    sheet_name='Varlist')

print(collegesFact.columns)

collegeFactDf = collegesFact[['UNITID', 'INSTNM', 'STABBR',
     'WEBADDR', 'SECTOR', 'ICLEVEL','CONTROL', 'HLOFFER',
       'UGOFFER', 'OPENPUBL', 'LATITUDE', 'LONGITUD']]

collegeCo =  collegeFactDf[collegeFactDf['STABBR'] == 'CO']

# Load the college dimension table
collegeDim = pd.read_csv('cost_2024.csv')
collegesDimLookup = pd. read_excel(
    'cost_dict_2024.xlsx', 
    sheet_name='Varlist')

# Sccess column names in quoted format to add to subsetting of columns
#print(collegeDim.columns.tolist())

collegeDimDF = collegeDim[['UNITID', 'APPLFEEU',
'PRMPGM', 'TUITPL1', 'TUITPL2', 'TUITPL3', 
'TUITION1',
'CHG2AY0', 'CHG2AY1', 'CHG2AY2', 'CHG2AY3',
'CHG4AY0',  'CHG4AY1','CHG4AY2', 'CHG4AY3']]

#Join the fact and dimension tables
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

import matplotlib.pyplot as plt

# Years for the x-axis
years = ['2021-22', '2022-23', '2023-24', '2024-25']

# Average tuition costs for the y-axis
average_costs = [7738.21, 7928.92, 8343.08, 8548.54]

# Create a line plot
plt.figure(figsize=(10, 6))
plt.plot(years, average_costs, marker='o')
plt.title('Average College Tuition Costs Over Time')
plt.xlabel('Academic Year')
plt.ylabel('Average Tuition Cost ($)')
plt.grid(True)
plt.xticks(years)
plt.tight_layout()
plt.show()


#Raptor Output

df = collegeDf.copy()
# melt tuition columns
cols = [c for c in df.columns if c.startswith("Tuition and fees for")]
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

# let's create polars DataFrame equivalent
pl_df = pl.from_pandas(long)
pl_overall = pl.from_pandas(overall)

joined = (
    pl_df.join(pl_overall, on="year", how="left")
    .with_columns(
        (pl.col("tuition") - pl.col("mean_tuition_all")).alias("diff_from_overall")
    )
)

# we might plot using pandas for simplicity





frontRange = collegeDf.query('-105.5 <= LONGITUDE <= -104.5').query("Name.str.contains('Community College')")['Unit Id'].tolist()

joinedFiltered = joined.filter(pl.col("Unit Id").is_in(frontRange))


# then convert to pandas dataframe
pandas_joined = joinedFiltered.to_pandas()

pandas_joined["Name"] = pandas_joined["Name"].str.replace(r"\s*Community College\s*$", "", regex=True)
pandas_joined["Name"] = pandas_joined["Name"].str.replace(r" Community College of ", "", regex=True)
pandas_joined["Name"] = pandas_joined["Name"].str.replace(r"of ", "", regex=True)

# Format the 'Price' column for display
pandas_joined.style.format({"tuition": "${x/1000:.0f}K"})


pandasNames = pandas_joined.query("year == '2024-25'")

p = (
    ggplot(data = pandas_joined,
    mapping = aes(x="year", 
    y= "tuition", 
    group="Name")) +
    geom_line(
        color="grey"
        , alpha=0.5) +
    geom_text(data = pandasNames, 
    mapping =  aes(label = 'Name', 
    y="tuition" + 500,
    ), 
    size = 6) + 
    labs(
        title="Tuition over time for Red Rocks Community College and peers",
        x="Academic Year",
        y="Mean Tuition",
    )
    + theme(axis_text_x=element_text(rotation=45, hjust=1), 
    legend_position = "none")
)

p

per_school.head(10)

cols = [c for c in df.columns if c.startswith("Tuition and fees for")]
long = (
    df.loc[:, ["Unit Id", "Name"] + cols]
      .melt(id_vars=["Unit Id", "Name"],
            value_vars=cols,
            var_name="year",
            value_name="tuition")
)
long["year"] = long["year"].str.replace("Tuition and fees for ", "")

overall = long.groupby("year")["tuition"] \
              .mean().reset_index(name="mean_tuition_all")

per_school = (
    long.groupby(["Name","year"])["tuition"]
        .mean()
        .reset_index(name="mean_tuition_school")
)


# compute change from first to last year per school
import pandas as pd

# pivot so years are columns
pivot = per_school.pivot(index="Name", columns="year", values="mean_tuition_school")

# sort years to ensure first and last
years = sorted(pivot.columns)
start, end = years[0], years[-1]
pivot = pivot.dropna(subset=[start, end])  # drop schools missing either

pivot["abs_change"] = pivot[end] - pivot[start]
pivot["pct_change"] = pivot["abs_change"] / pivot[start] * 100

# find extremes
max_abs = pivot["abs_change"].idxmax(), pivot["abs_change"].max()
min_abs = pivot["abs_change"].idxmin(), pivot["abs_change"].min()
max_pct = pivot["pct_change"].idxmax(), pivot["pct_change"].max()
min_pct = pivot["pct_change"].idxmin(), pivot["pct_change"].min()

max_abs, min_abs, max_pct, min_pct

# start from the per_school pandas DataFrame
pivot = per_school.pivot(index="Name", columns="year",
                         values="mean_tuition_school")

years = sorted(pivot.columns)
start, end = years[0], years[-1]

# drop any school missing either endpoint
pivot = pivot.dropna(subset=[start, end])

pivot["abs_change"] = pivot[end] - pivot[start]
pivot["pct_change"] = pivot["abs_change"] / pivot[start] * 100

# extremes
max_abs = pivot["abs_change"].idxmax(), pivot["abs_change"].max()
min_abs = pivot["abs_change"].idxmin(), pivot["abs_change"].min()
max_pct = pivot["pct_change"].idxmax(), pivot["pct_change"].max()
min_pct = pivot["pct_change"].idxmin(), pivot["pct_change"].min()
max_abs, min_abs, max_pct, min_pct

pivot.sort_values("abs_change", ascending=False).head()
pivot.sort_values("abs_change").head()
pivot.sort_values("pct_change", ascending=False).head()
pivot.sort_values("pct_change").head()

# Seaborn example

import matplotlib.pyplot as plt
import numpy as np
# %pip install seaborn
import seaborn as sns
sns.set_style("whitegrid")
plt.figure(figsize=(12, 8))
# Initialize a grid of plots with an Axes for each walk
sns.lineplot(
    x="year", 
    y="Name",
    hue="tuition",
    data=pandas_joined)
plt.title("Tuition over time for Colorado community colleges")


# Set up the figure size (optional, but helps with readability)
plt.figure(figsize=(10, 6))

# 1. Base Plot & geom_line equivalent
# Using units='Name' and estimator=None is the exact equivalent of group="Name"
ax = sns.lineplot(
    data=pandas_joined, 
    x='year', 
    y='tuition', 
    units='Name', 
    estimator=None, 
    color='grey', 
    alpha=0.5,
    legend=False # theme(legend_position = "none")
)

# 2. geom_text equivalent
# We loop through the pandasNames dataframe to place the text

latest_years_idx = pandasNames.groupby('Name')['year'].idxmax()
end_points = pandasNames.loc[latest_years_idx]

for index, row in end_points.iterrows():
    ax.text(
        x=row['year'], 
        y=row['tuition'] + 10, 
        s=row['Name'],          
        fontsize=12,            
        ha='left' # 'left' alignment looks better when labels are at the end of the line            
    )

# 3. labs equivalent
ax.set_title("Tuition over time for Red Rocks Community College and peers")
ax.set_xlabel("Academic Year")
ax.set_ylabel("Mean Tuition")

# 4. theme equivalent (axis_text_x rotation and alignment)
# ha='right' maps to hjust=1
plt.xticks(rotation=45, ha='right')

# Automatically adjust padding so labels don't get cut off
plt.tight_layout()

# Display the plot
plt.show()

## Seaborn with ggrepel equivalent
from adjust_text import adjust_text

# 1. Standard Plotting
plt.figure(figsize=(10, 6))
ax = sns.lineplot(data=pandas_joined, x='year', y='tuition', units='Name', 
                  estimator=None, color='grey', alpha=0.5)

# 2. Prepare the labels
# We'll use the "latest year" logic from the previous step
latest_years_idx = pandasNames.groupby('Name')['year'].idxmax()
end_points = pandasNames.loc[latest_years_idx]

texts = []
for index, row in end_points.iterrows():
    # Create the text objects but don't worry about overlap yet
    texts.append(plt.text(row['year'], row['tuition'] + 10, row['Name'], fontsize=10))

# 3. The Magic Step: Adjust all labels simultaneously
# 'expand_points' and 'expand_text' control how far labels stay from data/each other
adjust_text(texts, 
            arrowprops=dict(arrowstyle='->', color='red', lw=0.5),
            expand_points=(1.5, 1.5), 
            expand_text=(1.2, 1.2))

# 4. Final Touches
ax.set_title("Tuition over time (Auto-adjusted Labels)")
plt.xticks(rotation=0, ha='right')
plt.tight_layout()
plt.show()


#Highlight Red Rocks Community College
import seaborn as sns
import matplotlib.pyplot as plt
from adjust_text import adjust_text

# 1. Define your target and colors
target_name = "Red Rocks"
# Create a dictionary: { 'School Name': 'color' }
# We set the target to a bold color and everyone else to 'black'
palette = {name: "crimson" if name == target_name else "black" for name in pandas_joined['Name'].unique()}
# We also want the target line to be thicker
size_map = {name: 3 if name == target_name else 1 for name in pandas_joined['Name'].unique()}

plt.figure(figsize=(10, 6))

# 2. Plot with 'hue' and 'size'
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

# 3. Handle Labels with adjust_text
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
        fontsize=12 if is_target else 9,
        weight='bold' if is_target else 'normal',
        color='crimson' if is_target else 'gray'
    ))

adjust_text(texts, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

# 4. Final Styling
ax.set_title(f"Tuition Trends: {target_name} vs. Peers", fontsize=14, pad=20)
plt.xticks(rotation=0, ha='right')
sns.despine() # Removes the top and right borders for a cleaner look
plt.tight_layout()
plt.show()
