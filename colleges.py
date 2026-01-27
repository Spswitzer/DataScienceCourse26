import pandas as pd

load_colleges = pd. read_csv('hd2024.csv')
collegesLookup = pd. read_excel(
    'hd_dict_2024.xlsx', 
    sheet_name='Varlist')

print(load_colleges.columns)

college_df = load_colleges[['UNITID', 'INSTNM', 'STABBR',
    'OPEFLAG', 'WEBADDR', 'SECTOR', 'ICLEVEL','HLOFFER',
       'UGOFFER', 'OPENPUBL', 'LATITUDE', 'LONGITUD']]

college_co =  college_df[college_df['STABBR'] == 'CO']
