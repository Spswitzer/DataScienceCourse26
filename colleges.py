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