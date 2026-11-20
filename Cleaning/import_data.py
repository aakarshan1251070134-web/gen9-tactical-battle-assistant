import pandas as pd
import mysql.connector

# 1. Load your CSV file matching your dataset
csv_filename = "pokemondataset_updated.csv"
print(f"Loading data from {csv_filename}...")
df_csv = pd.read_csv(csv_filename)

# 2. Connect to your MySQL Database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Aakarshan77",
    database="pokemon_analytics"
)
cursor = conn.cursor()

print("Importing Pokémon into MySQL database...")

# 3. Loop through the CSV and insert each row into the Creatures table
id_counter = 100
for index, row in df_csv.iterrows():
    name = row['Name']
    primary_type = row['Type_1']
    secondary_type = row.get('Type_2', None)
    hp = row['HP']
    attack = row['Attack']
    defense = row['Defense']
    speed = row['Speed']
    
    # Grab special stats if they exist in your CSV columns
    sp_atk = row.get('Sp.Atk', row.get('Sp_Atk', 50))
    sp_def = row.get('Sp.Def', row.get('Sp_Def', 50))

    # Get Primary Type ID dynamically from your Types table
    cursor.execute("SELECT Type_ID FROM Types WHERE Type_Name = %s", (primary_type,))
    p_type_res = cursor.fetchone()
    p_type_id = p_type_res[0] if p_type_res else 1

    # Get Secondary Type ID dynamically if it exists
    s_type_id = None
    if pd.notna(secondary_type) and str(secondary_type).strip().lower() != 'none':
        cursor.execute("SELECT Type_ID FROM Types WHERE Type_Name = %s", (secondary_type,))
        s_type_res = cursor.fetchone()
        if s_type_res:
            s_type_id = s_type_res[0]

    # Insert including all stat columns expected by your table
    insert_query = """
        INSERT INTO Creatures (Pokemon_ID, Name, Primary_Type_ID, Secondary_Type_ID, Base_HP, Base_Attack, Base_Defense, Base_SpAttack, Base_SpDefense, Base_Speed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            Base_Attack = VALUES(Base_Attack),
            Base_Defense = VALUES(Base_Defense),
            Base_Speed = VALUES(Base_Speed)
    """
    try:
        cursor.execute(insert_query, (id_counter, name, p_type_id, s_type_id, hp, attack, defense, sp_atk, sp_def, speed))
    except Exception as e:
        # Fallback query if Pokemon_ID column isn't handled as explicit primary key
        fallback_query = """
            INSERT INTO Creatures (Name, Primary_Type_ID, Secondary_Type_ID, Base_HP, Base_Attack, Base_Defense, Base_SpAttack, Base_SpDefense, Base_Speed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                Base_Attack = VALUES(Base_Attack),
                Base_Defense = VALUES(Base_Defense),
                Base_Speed = VALUES(Base_Speed)
        """
        cursor.execute(fallback_query, (name, p_type_id, s_type_id, hp, attack, defense, sp_atk, sp_def, speed))
        
    id_counter += 1

conn.commit()
cursor.close()
conn.close()
print("Successfully imported all Pokémon from your CSV into MySQL!")