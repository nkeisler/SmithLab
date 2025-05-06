import pandas as pd
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog

# Create and hide the tkinter root window
root = tk.Tk()
root.withdraw()

# Open dialog to select directory
directory = filedialog.askdirectory(title='Select Directory Containing CSV Files')

# Change working directory to selected path
os.chdir(directory)

# Step 1: Get a list of all CSV files in the current directory
csv_files = [f for f in os.listdir() if f.endswith('.csv')]

# Step 2: Create a dictionary to store cumulative data for each behavior
cumulative_data = {}

# Function to split behavior across time bins
def split_behavior_duration(start_time, duration, bins):
    split_durations = []
    
    end_time = start_time + duration
    for i in range(len(bins) - 1):
        bin_start = bins[i]
        bin_end = bins[i + 1]
        
        # Check if behavior overlaps with the current bin
        if start_time < bin_end and end_time > bin_start:
            # Find the overlap between the behavior and the current bin
            overlap_start = max(start_time, bin_start)
            overlap_end = min(end_time, bin_end)
            overlap_duration = overlap_end - overlap_start
            
            # Add the duration for the current bin if there is an overlap
            if overlap_duration > 0:
                split_durations.append((i, overlap_duration))
    
    return split_durations

# Step 3: Iterate through each CSV file
for file in csv_files:
    # Load the CSV file without headers (header=None)
    df = pd.read_csv(file, header=None)
    
    # Extract the video name from the file name (without the .csv extension)
    video_name = os.path.splitext(file)[0]
    
    # Access columns by index (behavior, start_time, duration)
    df['behavior'] = df[0].str.lower()  # Normalize behavior to lowercase
    df['start_time'] = pd.to_numeric(df[2], errors='coerce')  # 3rd column for start time
    df['duration'] = pd.to_numeric(df[4], errors='coerce')    # 5th column for duration

    # Define the time bins (30 minutes split into 5-minute intervals)
    bins = np.arange(0, 1800 + 300, 300)  # Bins for 0-5, 5-10, ..., 25-30 minutes (30*60=1800 seconds)
    bin_labels = [f'{int(b/60)}-{int(b/60 + 5)} min' for b in bins[:-1]]
    
    # Create a dictionary to hold behavior and time-bin cumulative data
    cumulative_times = {behavior: np.zeros(len(bin_labels)) for behavior in df['behavior'].unique()}
    
    # Step 4: Iterate through each row and split behavior durations into bins
    for index, row in df.iterrows():
        behavior = row['behavior']
        start_time = row['start_time']
        duration = row['duration']
        
        if pd.notnull(start_time) and pd.notnull(duration):
            # Get split behavior durations across bins
            split_durations = split_behavior_duration(start_time, duration, bins)
            
            # Add the split durations to the corresponding time bins
            for bin_index, bin_duration in split_durations:
                cumulative_times[behavior][bin_index] += bin_duration
    
    # Step 5: Create a DataFrame to store the cumulative times for this file
    cumulative_df = pd.DataFrame(cumulative_times, index=bin_labels).T

    # Step 6: Apply cumulative sum across time bins **for each behavior individually**
    cumulative_df = cumulative_df.cumsum(axis=1)

    # Step 7: Add the video name as the first column
    cumulative_df.insert(0, 'video_name', video_name)
    
    # Step 8: Append cumulative data for each behavior
    for behavior in cumulative_df.index:
        # Normalize behavior name to avoid case-sensitive conflicts
        normalized_behavior = behavior.lower()

        # If the behavior doesn't exist in the dictionary, initialize it
        if normalized_behavior not in cumulative_data:
            cumulative_data[normalized_behavior] = []
        
        # Append the row (as a DataFrame) for the current behavior
        cumulative_data[normalized_behavior].append(cumulative_df.loc[[behavior]])

# Step 9: Write one CSV per behavior, combining data across all videos
for behavior, data_list in cumulative_data.items():
    # Concatenate all data frames for this behavior into one
    behavior_df = pd.concat(data_list)
    
    # Create a file name based on the normalized behavior
    output_file = f'cumulative_{behavior}_times.csv'

    # Check if the file already exists
    if os.path.exists(output_file):
        # If the file exists, append the data without writing the header
        behavior_df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        # If the file doesn't exist, write the data with the header
        behavior_df.to_csv(output_file, index=False)
    
    # Notify user that the file has been saved or appended
    print(f"Saved cumulative durations for {behavior} to {output_file}")
