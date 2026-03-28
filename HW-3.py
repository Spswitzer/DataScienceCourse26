import pandas as pd
import numpy as np
import lxml

#Read the data using pd.read_html()
df_raw = pd.read_html('data/planets_page.txt')

#Transpose the table
planets = df_raw[0].T

#Make sure the measurements are actually the column names.
planets.columns = planets.iloc[0]
planets.loc[1:]
planets = planets.rename(columns={np.nan: 'Planet Name'})
planets = planets.loc[1:]

print(planets.columns.tolist())

#Only grab the columns for:Name, Mass, Diamter, density, gravity, surface pressure, moons, and rings
planetsDf = planets[['Planet Name', 'Mass (1024kg)', 'Diameter (km)', 
'Density (kg/m3)', 'Gravity (m/s2)', 
'Surface Pressure (bars)', 'Number of Moons', 
'Ring System?']]

# Select columns where the name is not duplicated
planetsDf = planetsDf.loc[:, ~planetsDf.columns.duplicated()].copy()

#  Create a column heading for the names.
planetColNames = ['name', 'mass', 'diameter', 
'density', 'gravity', 'SurfacePressure', 
'Moons', 'RingSystem']

#Create a column heading for the names.
planetsDict = dict(zip(planetColNames, planetsDf.columns))

#Format the column names to be more readable
planetsDict['mass'] = 'Mass (10$^24$ kg)'
planetsDict['density'] = 'Density (kg/m$^3$)'
planetsDict['gravity'] = 'Gravity (m/s$^2$)'

planetsDf.columns = planetsDict

#Get rid of asterisks (`*`) or any other symbols in the data
planetsDf = planetsDf.replace({'\*': ''}, regex=True)

#Replace all "Unknowns" with `np.nan`
planetsDf = planetsDf.replace('Unknown', np.nan)
print(planetsDf.columns.tolist())
#Change Yes and No to `True` and `False` respectively.
planetsDf['RingSystem'] = planetsDf['RingSystem'].map({'Yes': True, 'No': False})

#Change type so everything is either `float`, `int` or `boolean`
varTypes = dict(zip(planetsDf.columns, 
[str, float, float, float, 
float, float, int, bool]))

planetsDf = planetsDf.astype(varTypes)

# create column Planet Type: Column of the type of the planet
planetsDf.insert(loc = 8, 
column = 'Planet Type', 
value = ['rocky', 'rocky', 'rocky', 
'satellite', 'rocky', 
'gas giant', 'gas giant', 'gas giant','gas giant', 'dwarf']) 

# create column Volume (10$^24$m)
planetsDf.insert(loc = 9, 
column = 'Volume (10$^24$m)',
value = planetsDf['mass'] * planetsDf['denisty'])

#Find the name of the planet with the largest diameter.
planetsDf.loc[planetsDf["diameter"].idxmax()]
# JUPITER

#Find the gravities of the planet with the highest and lowest densities
planetsDf.loc[planetsDf["density"].idxmax()]
# EARTH
planetsDf.loc[planetsDf["density"].idxmin()]
# SATURN

#Slice the data frame to only show the gas giants
planetsDf.loc[planetsDf['Planet Type'] == 'gas giant']
# Jupiter, Saturn, Uranus, Neptune

#Count how many planets have a magnetic field
magCount = planetsDf['RingSystem'].sum()
print(magCount)
# 4
#Calculate the total number of moons in the solar system 
totalMoons = planetsDf['Moons'].sum() + 1 # add 1 for the moon of Earth
print(totalMoons)
# 421
