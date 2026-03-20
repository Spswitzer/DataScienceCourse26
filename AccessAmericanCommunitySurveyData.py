
from census import Census
import pandas as pd

# Initialize client and fetch data
c = Census('YOUR_API_KEY', year=2025)
data = c.acs1.get(('NAME', 'B01003_001E'), {'for': 'state:*'})

# Convert to DataFrame
df = pd.DataFrame(data)
print(df.head())