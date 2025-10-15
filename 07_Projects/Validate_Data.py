import pandas as pd

# Load your sampled DataFrames
weather_df = pd.read_csv("sampled_weather_df.csv")
field_df = pd.read_csv("sampled_field_df.csv")

# ✅ Standardize weather_df columns
weather_df.rename(columns={
    "Weather_station": "Weather_station_ID"
}, inplace=True)

# ✅ Standardize field_df columns
field_df.rename(columns={
    "Crop_type": "Crop_Type",
    "Annual_yield": "Yield"
}, inplace=True)

# ------------------ Tests ------------------

def test_weather_columns():
    """Check that expected columns exist in the weather DataFrame."""
    expected_columns = ['Weather_station_ID', 'Rainfall', 'Temperature']
    missing = [col for col in expected_columns if col not in weather_df.columns]
    assert not missing, f"Missing weather columns: {missing}"

def test_weather_no_missing_values():
    """Check that there are no missing values in the weather DataFrame."""
    assert not weather_df.isnull().values.any(), "Weather DataFrame contains missing values"

def test_weather_valid_ranges():
    """Check that weather values fall within expected ranges."""
    assert weather_df['Rainfall'].ge(0).all(), "Negative rainfall values found"
    assert weather_df['Temperature'].between(-50, 60).all(), "Temperature values out of realistic range"

def test_field_columns():
    """Check that expected columns exist in the field DataFrame."""
    expected_columns = ['Field_ID', 'Crop_Type', 'Yield']
    missing = [col for col in expected_columns if col not in field_df.columns]
    assert not missing, f"Missing field columns: {missing}"

def test_field_no_missing_values():
    """Check that there are no missing values in the field DataFrame."""
    assert not field_df.isnull().values.any(), "Field DataFrame contains missing values"

def test_field_positive_yields():
    """Check that all yields are positive numbers."""
    assert field_df['Yield'].ge(0).all(), "Negative yields found"

def test_crop_types_are_valid():
    """Check that crop types are from a known valid list."""
    valid_crops = {"Wheat", "Corn", "Rice", "Soybean"}
    invalid = set(field_df['Crop_Type']) - valid_crops
    assert not invalid, f"Invalid crop types found: {invalid}"
