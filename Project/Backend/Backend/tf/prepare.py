import pandas as pd
import os
from ast import literal_eval

current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, 'datasets', 'youtube.csv')
df = pd.read_csv(dataset_path)

# Seçilen sütunlar
selected_columns = ['name', 'sentiment_scores', 'favorability', 'rating', 'genre', 
                    'year',  'country', 'runtime']

df_selected = df[selected_columns].dropna()
df_selected['runtime_category'] = df_selected['runtime'].apply(lambda x: 0 if x < 50 else (1 if x <= 100 else 2))
df_selected['favorability_rounded'] = df_selected['favorability'].round(2)
df_selected.drop(columns=['favorability'], inplace=True)

# 'sentiment_scores' sütununu literal_eval ile değerlendir ve duyarlılık puanlarını ayır
df_selected['sentiment_scores'] = df_selected['sentiment_scores'].apply(literal_eval)
df_selected['positive'] = df_selected['sentiment_scores'].apply(lambda x: x['positive'])
df_selected['neutral'] = df_selected['sentiment_scores'].apply(lambda x: x['neutral'])
df_selected['negative'] = df_selected['sentiment_scores'].apply(lambda x: x['negative'])
df_selected.drop(columns=['sentiment_scores'], inplace=True)

# 'rating', 'country', 'genre' sütunlarını kategorik olarak işleyip normalize edin
for column in ['rating', 'country', 'genre']:
    unique_values = df_selected[column].unique()
    mapping = {val: idx for idx, val in enumerate(unique_values)}
    df_selected[f'{column}_normalized'] = df_selected[column].map(mapping)
    df_selected.drop(columns=[column], inplace=True)

output_csv_path = os.path.join(current_dir, 'datasets', 'processed_youtube.csv')
df_selected.to_csv(output_csv_path, index=False, header=True)