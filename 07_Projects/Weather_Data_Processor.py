"""
weather_data_processor.py

This module defines the WeatherDataProcessor class, which handles:
- Loading weather station data from the web
- Extracting numeric measurements from message strings
- Calculating mean values for each weather station and measurement type
"""

import re
import pandas as pd
import logging
from data_ingestion import read_from_web_CSV


class WeatherDataProcessor:
    def __init__(self, config_params, logging_level="INFO"):
        """
        Initialize the WeatherDataProcessor with configuration parameters.
        """
        self.weather_station_data = config_params["weather_csv_path"]
        self.patterns = config_params["regex_patterns"]
        self.weather_df = None
        self.initialize_logging(logging_level)

    def initialize_logging(self, logging_level):
        logger_name = __name__ + ".WeatherDataProcessor"
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False

        if logging_level.upper() == "DEBUG":
            log_level = logging.DEBUG
        elif logging_level.upper() == "INFO":
            log_level = logging.INFO
        elif logging_level.upper() == "NONE":
            self.logger.disabled = True
            return
        else:
            log_level = logging.INFO

        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def weather_station_mapping(self):
        """Load weather station data from the web and store it in self.weather_df."""
        self.weather_df = read_from_web_CSV(self.weather_station_data)
        self.logger.info("Successfully loaded weather station data from the web.")

    def extract_measurement(self, message):
        """Extract a numeric measurement from a message string using regex patterns."""
        for key, pattern in self.patterns.items():
            match = re.search(pattern, message)
            if match:
                # FIX: Ensure we handle potential None values correctly during float conversion
                value = next((x for x in match.groups() if x is not None and x.strip() != ''), None)
                if value is not None:
                     return key, float(value)
        return None, None

    def process_messages(self):
        """
        Apply extract_measurement to all messages. 
        FIX: Drops rows where extraction failed (Measurement or Value is None/NaN).
        """
        if self.weather_df is not None:
            result = self.weather_df["Message"].apply(self.extract_measurement)
            self.weather_df["Measurement"], self.weather_df["Value"] = zip(*result)
            
            # --- FIX FOR MISSING VALUES (test_weather_no_missing_values) ---
            # Remove rows where the message couldn't be parsed (Measurement or Value is None)
            self.weather_df.dropna(subset=['Measurement', 'Value'], inplace=True)
            
            self.logger.info("Messages processed, measurements extracted, and unparsed rows removed.")
        else:
            self.logger.warning(
                "weather_df is not initialized, skipping message processing."
            )
        return self.weather_df

    def calculate_means(self):
        """
        Calculate mean value of each measurement type per weather station.
        """
        if self.weather_df is not None:
            # This step creates the required 'Temperature', 'Rainfall', etc. columns via unstack()
            means = (
                self.weather_df.groupby(["Weather_station_ID", "Measurement"])["Value"]
                .mean()
                .unstack()
                .reset_index()
            )
            self.logger.info("Mean values calculated.")
            return means
        else:
            self.logger.warning(
                "weather_df is not initialized, cannot calculate means."
            )
            return None

    def process(self):
        """
        Run the full pipeline: load data, extract measurements, and calculate means.
        FIX: Returns the final aggregated DataFrame (means).
        """
        self.weather_station_mapping()
        self.process_messages()
        
        # --- FIX FOR MISSING COLUMNS (test_weather_columns & test_weather_valid_ranges) ---
        # The final result must be the aggregated means DataFrame
        mean_df = self.calculate_means()
        
        self.logger.info("Weather data processing completed.")
        return mean_df # Return the aggregated DataFrame with correct columns