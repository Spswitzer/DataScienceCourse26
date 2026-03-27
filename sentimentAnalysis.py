#%pip install transformers
#%pip install torch
#%pip install textblob

import pandas as pd
from textblob import TextBlob


# Use cp1252 (Windows-1252) to handle 0xA0 bytes
csv_path = r"G:/Shared drives/Research & Assessment Design (RAD)/L1 Projects/Budget Reduction Blueprint Surveys/District Survey 25-26/data/comments.csv"
df = pd.read_csv(csv_path, encoding="cp1252")
print(df.columns.tolist())

df['clean_comment'] = df['comments'].notna()


df = df.query('clean_comment == True')

df['sentiment'] = df['comments'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)

# Identify positive vs negative comments
positive_comments = df[df['sentiment'] > 0.1]
negative_comments = df[df['sentiment'] < -0.1]
