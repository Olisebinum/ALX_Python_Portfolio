"""
data_ingestion.py

This module provides functions for connecting to a SQLite database,
executing SQL queries, and reading CSV data from the web.  

It is designed to support data ingestion tasks such as:
    - Creating and validating a SQLAlchemy database engine.
    - Running SQL queries and returning results as pandas DataFrames.
    - Fetching external CSV data from web URLs.

Logging is used throughout to provide helpful debugging information.
"""

import logging
import pandas as pd
from sqlalchemy import create_engine, text

# Configure logger
logger = logging.getLogger("data_ingestion")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_db_engine(db_path):
    """
    Create and validate a SQLAlchemy database engine.

    Args:
        db_path (str): Path to the SQLite database, provided as a SQLAlchemy
            connection string (e.g., 'sqlite:///my_database.db').

    Returns:
        sqlalchemy.engine.Engine: A SQLAlchemy engine object that can be used
        to interact with the database.

    Raises:
        ImportError: If SQLAlchemy is not installed.
        Exception: For any errors encountered when creating the engine.
    """
    try:
        engine = create_engine(db_path)
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info("Database engine created successfully.")
        return engine
    except ImportError as e:
        logger.error(
            "SQLAlchemy is required to use this function. Please install it first."
        )
        raise e
    except Exception as e:
        logger.error(f"Failed to create database engine. Error: {e}")
        raise e


def query_data(engine, sql_query):
    """
    Execute an SQL query using a SQLAlchemy engine.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine connected to the database.
        sql_query (str): SQL query string to be executed.

    Returns:
        pd.DataFrame: A DataFrame containing the query results.

    Raises:
        ValueError: If the query returns an empty DataFrame.
        Exception: For any errors encountered during query execution.
    """
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(text(sql_query), connection)
        if df.empty:
            msg = "The query returned an empty DataFrame."
            logger.error(msg)
            raise ValueError(msg)
        logger.info("Query executed successfully.")
        return df
    except ValueError as e:
        logger.error(f"SQL query failed. Error: {e}")
        raise e
    except Exception as e:
        logger.error(f"An error occurred while querying the database. Error: {e}")
        raise e


def read_from_web_CSV(URL):
    """
    Read a CSV file directly from a web URL.

    Args:
        URL (str): A string representing the web URL of the CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing the contents of the CSV.

    Raises:
        pd.errors.EmptyDataError: If the URL does not point to a valid CSV file.
        Exception: For any other errors encountered while fetching or reading the CSV.
    """
    try:
        df = pd.read_csv(URL)
        logger.info("CSV file read successfully from the web.")
        return df
    except pd.errors.EmptyDataError as e:
        logger.error(
            "The URL does not point to a valid CSV file. Please check the URL and try again."
        )
        raise e
    except Exception as e:
        logger.error(f"Failed to read CSV from the web. Error: {e}")
        raise e
