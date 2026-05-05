import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database.db')
df = pd.read_csv('data/instagram data.csv')
df.to_sql('reels', engine, if_exists='replace', index=False)

print("Base de datos creada")