import pandas as pd
import json

# Load configuration settings from JSON file
with open('parameters.json', 'r') as config_file:
    config = json.load(config_file)

# Use configuration settings
filepath = config['input file']
fileoutput = config['output file']
base_price = config['base price']
min_price = config['min price']
max_price = config['max price']
αs = config['solar energy dependency']
αw = config['wind energy dependency']
αsd = config['combined solar energy dependency']
αwd = config['combined wind energy dependency']
ndays = config['number of samples [day]']

def read_weather_data(filepath):
    column_indices = [0, 1, 2, 3, 14, 21]
    column_names = ['Year', 'Month', 'Day', 'Hour', 'Global Horizontal Radiation', 'Wind Speed (m/s)']
    
    data = pd.read_csv(
        filepath,
        delimiter=',',
        skiprows=8,
        usecols=column_indices,
        names=column_names,
        header=None
    )
    
    return data

def calculate_wrapped_moving_average(data, ndays):
    wma = int(ndays * 24)
    padding = data.tail(wma)
    data_padded = pd.concat([padding, data], ignore_index=True)
    
    data['Moving Average Radiation (Wh/m²)'] = data_padded['Global Horizontal Radiation'].rolling(window=wma, min_periods=1).mean()[wma:].reset_index(drop=True)
    data['Moving Average Wind (m/s)'] = data_padded['Wind Speed (m/s)'].rolling(window=wma, min_periods=1).mean()[wma:].reset_index(drop=True)

    return data

def add_percentage_variation(data):
    data['Normalized Variation % Radiation'] = (data['Global Horizontal Radiation'] - data['Moving Average Radiation (Wh/m²)']) / data['Moving Average Radiation (Wh/m²)']
    data['Normalized Variation % Wind'] = (data['Wind Speed (m/s)'] - data['Moving Average Wind (m/s)']) / data['Moving Average Wind (m/s)']
    return data

def add_price_columns(data, base_price, αs, αw, αsd, αwd):
    data['Price Radiation'] = (base_price - αs * data['Normalized Variation % Radiation']).clip(min_price, max_price)
    data['Price Wind'] = (base_price - αw * data['Normalized Variation % Wind']).clip(min_price, max_price)
    data['Price Combined'] = (base_price - αsd * data['Normalized Variation % Radiation'] - αwd * data['Normalized Variation % Wind']).clip(min_price, max_price)
    return data

def save_selected_columns_to_csv(data):
    selected_columns = data.iloc[:, [0, 1, 2, 3, -3, -2, -1]]
    selected_columns.to_csv(fileoutput, index=False)

# Load and process data
weather_data = read_weather_data(filepath)
weather_data = calculate_wrapped_moving_average(weather_data, ndays)
weather_data = add_percentage_variation(weather_data)
weather_data = add_price_columns(weather_data, base_price, αs, αw, αsd, αwd)

# Save results and print statistics
save_selected_columns_to_csv(weather_data)
print(weather_data[['Price Radiation', 'Price Wind', 'Price Combined']].describe())
