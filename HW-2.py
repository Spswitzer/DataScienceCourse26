from unittest import installHandler
import pandas as pd
import numpy as np
#pip install matplotlib
import matplotlib.pyplot as plt

columns = [chr(65 + i) for i in range(10)]
df_grid = pd.DataFrame(np.arange(100).reshape(10,10).T, columns=columns)
#1.1 Grab all rows between 2 and 7 (inclusive)
df_grid.iloc[1:8]
#1.2 Obtain all even rows and columns C and H
specific_columns = ['C', 'H']
df_grid.iloc[::2][specific_columns]
#1.3 Get every third column
df_grid.iloc[:, ::3]
#1.4 Obtain the 6th item in column E
x = df_grid.iloc[6, 4]
print(x)
#2.4 Use the command .value_counts() on the origin column. Did we create continuous or discrete data and why?
pepDf = pd.read_csv('data/peppers.csv')
pepDf.head()
pepDf.value_counts('origin')
#2.5 Plot values
pepDf.value_counts('origin').plot(kind='bar')
#2.6 Increase the plot size
pepDf.value_counts('origin').plot(kind='bar', figsize = (8,10))
#2.7 Hottest Pepper
pepDf.loc[ pepDf["max_shu"].idxmax() ]
#2.8 Filter rows that are not peppers
pepDf.loc[pepDf[pepDf["species"].notna()]["max_shu"].idxmax()]
