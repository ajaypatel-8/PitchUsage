# Imports
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Describe our app
st.title("Pitch Usage and Characteristics by Time Through The Order")

st.markdown("""
This app was designed for a simple purpose: analyze how pitchers change their arsenal usage based on times through the order in 2024. The table below 
            displays pitchers and their arsenal (pitch type, velocity, movement) by time through the order. Note that a higher run value is better 
            for pitchers.
            \nBy Ajay Patel - Reach out to me on Twitter @ajaypatel8_!
""")

# Read in data / pitch data from 2024
df1 = pd.read_parquet('data_1_2024.parquet')
df2 = pd.read_parquet('data_2_2024.parquet')
df3 = pd.read_parquet('data_3_2024.parquet')

data = pd.concat([df1, df2, df3])

# Only interested in first three times through the order
data = data[data['n_thruorder_pitcher'].isin([1, 2, 3])]

# Remove some unnecessary pitch types and NAs
data = data[data['pitch_type'] != 'None']
data = data[data['pitch_type'] != 'PO']
data = data.dropna(subset=['pitch_type'])

# Remove pitchers who didn't face an order more than one time
pitchers_with_multiple_times = data.groupby('player_name')['n_thruorder_pitcher'].nunique()
valid_pitchers = pitchers_with_multiple_times[pitchers_with_multiple_times > 1].index

data = data[data['player_name'].isin(valid_pitchers)]

data['pitch_type'] = data['pitch_type'].astype(str)
data['n_thruorder_pitcher'] = pd.to_numeric(data['n_thruorder_pitcher'], errors='coerce')

# Calculate pitch usage by pitcher, time through the order, and pitch type 
pitch_usage_raw = (
    data
    .groupby(['player_name', 'n_thruorder_pitcher', 'pitch_type'])
    .size()
    .reset_index(name='raw_pitch_count')
)

# Calculate total number of pitches per pitcher and time through the order
total_pitches_per_situation = (
    data
    .groupby(['player_name', 'n_thruorder_pitcher'])
    .size()
    .reset_index(name='total_pitches')
)

# Merge to get the total pitch count for each situation
pitch_usage_raw = pitch_usage_raw.merge(total_pitches_per_situation, 
                                        on=['player_name', 'n_thruorder_pitcher'], 
                                        how='left')

# Calculate the pitch usage percentage by dividing 
pitch_usage_raw['pitch_usage'] = (pitch_usage_raw['raw_pitch_count'] / pitch_usage_raw['total_pitches']) * 100

# Calculate averages for each pitcher and pitch type / intersted in pitch velo and movement
pitcher_avg_by_type = (
    data
    .groupby(['player_name', 'pitch_type'])
    .agg({
        'release_speed': 'mean',
        'pfx_x': 'mean',  # Horizontal break
        'pfx_z': 'mean'   # Vertical break
    })
    .rename(columns={
        'release_speed': 'avg_release_speed',
        'pfx_x': 'avg_pfx_x',
        'pfx_z': 'avg_pfx_z'
    })
    .reset_index()
)

# Group by pitcher, time through the order, and pitch type to calculate their specific averages
# Choosing run value for a descriptive measure of how their pitches did
pitch_characteristics = (
    data
    .groupby(['player_name', 'n_thruorder_pitcher', 'pitch_type'])
    .agg({
        'delta_pitcher_run_exp': 'mean',
        'release_speed': 'mean',
        'pfx_x': 'mean',
        'pfx_z': 'mean'
    })
    .reset_index()
)

# Merge the pitch averages by pitch type with the grouped data
result = pitch_characteristics.merge(pitcher_avg_by_type, on=['player_name', 'pitch_type'])

# Add difference columns
result['velocity_diff'] = result['release_speed'] - result['avg_release_speed']
result['horizontal_break_diff'] = result['pfx_x'] - result['avg_pfx_x']
result['vertical_break_diff'] = result['pfx_z'] - result['avg_pfx_z']

# Merge all of our data together
final_result = result.merge(pitch_usage_raw[['player_name', 'n_thruorder_pitcher', 'pitch_type', 'pitch_usage', 'raw_pitch_count']], 
                            on=['player_name', 'n_thruorder_pitcher', 'pitch_type'], 
                            how='left')

# Sort values by player, time through the order, and pitch type for display
final_result = final_result.sort_values(by=['player_name', 'n_thruorder_pitcher', 'pitch_type'])

# Convert pitch movement from feet to inches
final_result['pfx_x'] = final_result['pfx_x'] * 12
final_result['pfx_z'] = final_result['pfx_z'] * 12
final_result['avg_pfx_x'] = final_result['avg_pfx_x'] * 12
final_result['avg_pfx_z'] = final_result['avg_pfx_z'] * 12

# Recalculate differences in inches
final_result['horizontal_break_diff'] = final_result['pfx_x'] - final_result['avg_pfx_x']
final_result['vertical_break_diff'] = final_result['pfx_z'] - final_result['avg_pfx_z']

# Round run value to three decimal places
final_result['delta_pitcher_run_exp'] = final_result['delta_pitcher_run_exp'].apply(lambda x: f"{x:.3f}")
# Round all other columns with decimal values to 1 decimal places
final_result.loc[:, final_result.columns != 'delta_pitcher_run_exp'] = final_result.loc[:, final_result.columns != 'delta_pitcher_run_exp'].round(1)

# Format the 'pitch_usage' column as a percentage with 2 decimal places
final_result['pitch_usage_numeric'] = final_result['pitch_usage']
final_result['pitch_usage'] = final_result['pitch_usage'].apply(lambda x: f"{x:.1f}%")

# Filter options for pitchers
player_names = final_result['player_name'].unique()
selected_player = st.selectbox("Select Player", ["All"] + list(player_names))

if selected_player != "All":
    filtered_data = final_result[final_result['player_name'] == selected_player]
else:
    filtered_data = final_result

# Update the displayed pitch types for the pitcher selected
pitch_types = filtered_data['pitch_type'].dropna().unique()
selected_pitch_type = st.selectbox("Select Pitch Type", ["All"] + list(pitch_types))

if selected_pitch_type != "All":
    filtered_data = filtered_data[filtered_data['pitch_type'] == selected_pitch_type]

# Add a filter for pitch counts / helps to look at only SPs
min_pitch_count, max_pitch_count = 0, int(filtered_data['raw_pitch_count'].max())
selected_pitch_count_range = st.slider("Select Raw Pitch Count Range", min_value=min_pitch_count, 
                                       max_value=max_pitch_count, value=(min_pitch_count, max_pitch_count))

# Apply the raw pitch count filter to our dataset
filtered_data = filtered_data[(filtered_data['raw_pitch_count'] >= selected_pitch_count_range[0]) &
                               (filtered_data['raw_pitch_count'] <= selected_pitch_count_range[1])]

# Dictionary of how I wanted to rename columns
column_rename_dict = {
    'player_name': 'Pitcher',
    'n_thruorder_pitcher': 'Time Through Order',
    'pitch_type': 'Pitch Type',
    'raw_pitch_count': 'Pitch Count',
    'pitch_usage': 'Pitch Usage (%)',
    'release_speed': 'Velocity',
    'pfx_x': 'Horizontal Break (in)',
    'pfx_z': 'Vertical Break (in)',
    'avg_release_speed': 'Avg Velocity',
    'avg_pfx_x': 'Avg Horizontal Break (in)',
    'avg_pfx_z': 'Avg Vertical Break (in)',
    'velocity_diff': 'Velocity Diff (mph)',
    'horizontal_break_diff': 'Horizontal Break Diff (in)',
    'vertical_break_diff': 'Vertical Break Diff (in)',
    'delta_pitcher_run_exp': 'Avg Run Value'
}

# Rename the columns 
filtered_data = filtered_data.rename(columns=column_rename_dict)

# Reorder the columns to move usage and run value to the "front" of the table
column_order = [
    'Pitcher', 'Time Through Order', 'Pitch Type', 
    'Pitch Count', 'Pitch Usage (%)', 'Avg Run Value',
    'Velocity', 'Horizontal Break (in)', 'Vertical Break (in)',
    'Avg Velocity', 'Avg Horizontal Break (in)', 'Avg Vertical Break (in)', 
    'Velocity Diff (mph)', 'Horizontal Break Diff (in)', 'Vertical Break Diff (in)'
]

# Display the table in Streamlit
table_data = filtered_data.drop(columns=['pitch_usage_numeric'])

table_data = table_data[column_order]

st.subheader("Pitch Usage and Characteristics Table")
st.dataframe(table_data, use_container_width=True)

st.subheader("Pitch Usage by Time Through the Order")

# Create a seaborn line plot to show pitch usage by time through the order
plt.figure(figsize=(10, 6))

# Create the Seaborn line plot (using the numeric pitch_usage for plotting)
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)
sns.lineplot(data=filtered_data, x='Time Through Order', y='pitch_usage_numeric', hue='Pitch Type', marker='o')

if selected_player != "All":
    plt.title(f'{selected_player} - Pitch Usage by Time Through the Order')
else:
    plt.title('Pitch Usage by Time Through the Order (All Players)')

plt.xticks([1, 2, 3])

plt.xlabel('Time Through the Order')
plt.ylabel('Pitch Usage (%)')

plt.legend(title="Pitch Type", bbox_to_anchor=(1.025, 1), loc='upper left')

st.pyplot(plt)