import pandas as pd
import mysql.connector

# Connect to MySQL (enter your MySQL root password below)
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Aakarshan77",
    database="pokemon_analytics"
)
cursor = conn.cursor()

# 1. Load Types
print("Loading Types...")
df_types = pd.read_csv('sql_ready_types.csv', header=None, names=['Type_ID', 'Type_Name'])
for _, row in df_types.iterrows():
    cursor.execute(
        "INSERT INTO Types (Type_ID, Type_Name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Type_Name=VALUES(Type_Name)",
        (int(row['Type_ID']), str(row['Type_Name']))
    )

# 2. Load Creatures
print("Loading Creatures...")
df_creatures = pd.read_csv('sql_ready_creatures.csv', header=None)
for _, row in df_creatures.iterrows():
    sec_type = int(row[3]) if pd.notnull(row[3]) and str(row[3]).strip() != '' else None
    cursor.execute("""
        INSERT INTO Creatures (
            Pokemon_ID, Name, Primary_Type_ID, Secondary_Type_ID, 
            Base_HP, Base_Attack, Base_Defense, Base_SpAttack, Base_SpDefense, Base_Speed
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE Name=VALUES(Name)
    """, (
        int(row[0]), str(row[1]), int(row[2]), sec_type,
        int(row[4]), int(row[5]), int(row[6]), int(row[7]), int(row[8]), int(row[9])
    ))

conn.commit()
cursor.close()
conn.close()
print("Success! All data loaded into MySQL.")