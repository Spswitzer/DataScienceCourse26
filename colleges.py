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
