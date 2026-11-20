import pandas as pd

print("Starting ETL Process...")

# 1. Load the raw datasets
df_main = pd.read_csv('pokemondataset_updated.csv')
df_temp = pd.read_csv('temp20.csv')

# 2. Standardize the Main DataFrame
# Select only the columns needed for the Creatures table
main_clean = df_main[['id', 'Name', 'Type_1', 'Type_2', 'HP', 'Attack', 'Defense', 'Sp.Atk', 'Sp.Def', 'Speed']].copy()
main_clean.rename(columns={'Type_1': 'Type1', 'Type_2': 'Type2'}, inplace=True)

# 3. Standardize the Alternate Forms (temp20)
temp_clean = df_temp[['id', 'Name', 'Form', 'Regional_Variant', 'Type1', 'Type2', 'HP', 'Attack', 'Defense', 'Sp.Atk', 'Sp.Def', 'Speed']].copy()

# Function to create unique names for alternate forms
def make_form_name(row):
    name = str(row['Name']).strip()
    form = str(row['Form']).strip() if pd.notnull(row['Form']) and str(row['Form']).strip() != '' else ''
    reg = str(row['Regional_Variant']).strip() if pd.notnull(row['Regional_Variant']) and str(row['Regional_Variant']).strip() != '' else ''
    
    if form and reg:
        return f"{name} ({reg} - {form})"
    elif form:
        return f"{name} ({form})"
    elif reg:
        return f"{name} ({reg})"
    return name

# Apply the naming function and drop the extra text columns
temp_clean['Name'] = temp_clean.apply(make_form_name, axis=1)
temp_clean = temp_clean[['id', 'Name', 'Type1', 'Type2', 'HP', 'Attack', 'Defense', 'Sp.Atk', 'Sp.Def', 'Speed']]

# 4. Combine both datasets vertically
combined = pd.concat([main_clean, temp_clean], ignore_index=True)

# 5. Extract Unique Types and create the Type_Map
types_series = pd.concat([combined['Type1'], combined['Type2']]).dropna().str.strip().unique()
types_df = pd.DataFrame({'Type_Name': sorted(types_series)})
types_df['Type_ID'] = range(1, len(types_df) + 1)
types_df = types_df[['Type_ID', 'Type_Name']]

# Map the text types to the new Type_IDs
type_map = dict(zip(types_df['Type_Name'], types_df['Type_ID']))
combined['Primary_Type_ID'] = combined['Type1'].str.strip().map(type_map)
combined['Secondary_Type_ID'] = combined['Type2'].str.strip().map(type_map)

# 6. Final Formatting to match MySQL Table exactly
final_creatures = combined[['id', 'Name', 'Primary_Type_ID', 'Secondary_Type_ID', 'HP', 'Attack', 'Defense', 'Sp.Atk', 'Sp.Def', 'Speed']].copy()
# Replace NaN values with None (which translates to SQL NULL)
final_creatures = final_creatures.where(pd.notnull(final_creatures), None)

print(f"Total Creatures Processed: {final_creatures.shape[0]}")

# 7. Export to SQL-Ready CSVs
types_df.to_csv('sql_ready_types.csv', index=False, header=False)
final_creatures.to_csv('sql_ready_creatures.csv', index=False, header=False)

print("Success! 'sql_ready_types.csv' and 'sql_ready_creatures.csv' generated.")