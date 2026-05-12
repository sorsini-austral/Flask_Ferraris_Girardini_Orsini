import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///instance/database.db')
df = pd.read_csv('data/instagram_v3.csv')
df.to_sql('reels', engine, if_exists='replace', index=False)

print("Base de datos creada")