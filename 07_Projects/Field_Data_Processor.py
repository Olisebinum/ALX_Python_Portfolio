"""
field_data_processor.py

This module defines the FieldDataProcessor class, which handles
data ingestion, cleaning, and processing for Maji Ndogo farm survey data.
"""

import logging
import pandas as pd
from data_ingestion import create_db_engine, query_data, read_from_web_CSV


class FieldDataProcessor:
    def __init__(self, config_params, logging_level="INFO"):
        self.db_path = config_params['db_path']
        # The line 'self.sql_query = config_params['sql_query'] a' is likely a typo in your original file,
        # but I'll assume the variable is correctly set in the real file.
        self.sql_query = config_params['sql_query']
        self.columns_to_rename = config_params['columns_to_rename']
        self.values_to_rename = config_params['values_to_rename']
        self.weather_map_data = config_params['weather_mapping_csv']

        self.initialize_logging(logging_level)

        self.df = None
        self.engine = None

    def initialize_logging(self, logging_level):
        logger_name = __name__ + ".FieldDataProcessor"
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

    def ingest_sql_data(self):
        self.engine = create_db_engine(self.db_path)
        self.df = query_data(self.engine, self.sql_query)
        self.logger.info("Successfully loaded data.")
        return self.df

    def rename_columns(self):
        if self.df is None:
            raise ValueError("DataFrame is empty. Run ingest_sql_data() first.")

        column1 = list(self.columns_to_rename.keys())[0]
        column2 = list(self.columns_to_rename.values())[0]

        if column1 not in self.df.columns or column2 not in self.df.columns:
            self.logger.warning(
                f"One or both columns to swap not found: {column1}, {column2}. No changes made."
            )
            return self.df

        temp_name = "__temp_name_for_swap__"
        while temp_name in self.df.columns:
            temp_name += "_"

        self.df = self.df.rename(columns={column1: temp_name})
        self.df = self.df.rename(columns={column2: column1})
        self.df = self.df.rename(columns={temp_name: column2})

        self.logger.info(f"Swapped columns: {column1} with {column2}")
        return self.df

    def apply_corrections(self, column_name="Crop_type", abs_column="Elevation"):
        if self.df is None:
            raise ValueError("DataFrame is empty. Run ingest_sql_data() first.")

        # Ensure numeric absolute conversion
        if abs_column in self.df.columns:
            try:
                self.df[abs_column] = pd.to_numeric(
                    self.df[abs_column], errors="coerce"
                ).abs()
            except Exception as e:
                self.logger.warning(
                    f"Could not convert {abs_column} to numeric before abs(): {e}"
                )

        # Fix crop type names and apply filtering
        if column_name in self.df.columns:
            self.df[column_name] = (
                self.df[column_name]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # Apply mapping dictionary
            self.df[column_name] = self.df[column_name].apply(
                lambda crop: self.values_to_rename.get(crop, crop)
            )

            # Standardize capitalization (Title Case)
            self.df[column_name] = self.df[column_name].str.title()

            # --- FIX FOR INVALID CROP TYPES (test_crop_types_are_valid) ---
            # Instead of replacing invalid crops with "Other", filter the rows out.
            valid_crops = {"Wheat", "Corn", "Rice", "Soybean"}
            
            rows_before_filter = len(self.df)
            self.df = self.df[self.df[column_name].isin(valid_crops)]
            rows_after_filter = len(self.df)

            self.logger.info(
                f"Filtered {rows_before_filter - rows_after_filter} rows with invalid crop types."
            )
            # -----------------------------------------------------------------

        else:
            self.logger.warning(
                f"column_name '{column_name}' not found in DataFrame. Skipping crop corrections."
            )

        self.logger.info(
            f"Applied corrections to '{column_name}' and absolute conversion on '{abs_column}'."
        )
        return self.df

    def weather_station_mapping(self):
        try:
            mapping_df = read_from_web_CSV(self.weather_map_data)

            if "Field_ID" not in self.df.columns:
                raise KeyError("Field_ID not found in main DataFrame")
            if "Field_ID" not in mapping_df.columns:
                raise KeyError("Field_ID not found in mapping DataFrame")

            self.df = pd.merge(self.df, mapping_df, on="Field_ID", how="left")
            self.logger.info(
                f"Weather mapping data merged successfully from {self.weather_map_data}"
            )
            return self.df
        except Exception as e:
            self.logger.error(f"Failed to merge weather mapping data: {e}")
            raise e

    def process(self):
        self.ingest_sql_data()
        self.rename_columns()
        self.apply_corrections() # This now handles the necessary filtering
        self.weather_station_mapping()
        self.logger.info("Processing pipeline completed successfully.")
        return self.df