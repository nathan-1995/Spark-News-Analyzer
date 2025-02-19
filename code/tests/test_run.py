import unittest
import os
import sys
from pathlib import Path
import tempfile
import shutil
from typing import List, Optional
import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from datasets import Dataset

# Import functions from run.py
from src.run import process_data, process_data_all

# Add src directory to path so we can import run.py functions
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

# Set Spark environment variables for local testing
# os.environ["PYSPARK_PYTHON"] = r"C:\Users\ndeli\miniconda3\envs\news_processing\python.exe"
# os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\ndeli\miniconda3\envs\news_processing\python.exe"

class TestSpark(unittest.TestCase):
    spark: Optional[SparkSession] = None
    
    @classmethod
    def setUpClass(cls) -> None:
        """Spark setup before running tests"""
        cls.spark = SparkSession.builder \
            .master("local[*]") \
            .appName("SparkUnitTests") \
            .getOrCreate()
        print("Created SparkSession for all tests")
        
    @classmethod
    def tearDownClass(cls) -> None:
        """Stop the SparkSession after all tests are done."""
        if hasattr(cls, 'spark') and cls.spark is not None:
            cls.spark.stop()
    
    def test_spark_session(self) -> None:
        """Test if Spark session can be created and basic operations work"""
        print("Testing Spark session...")

        # Create a simple test DataFrame
        test_data: List[tuple] = [("test", 1), ("test2", 2)]
        df: DataFrame = self.spark.createDataFrame(test_data, ["word", "count"])

        # Perform a basic operation: count rows
        result: int = df.count()

        # Check if result is as expected
        self.assertEqual(result, 2, "DataFrame should have 2 rows")
        print(f"Number of rows: {result}\n") 

    def test_process_data(self) -> None:
        """Test process_data from run.py with a small dataset and specific words"""
        print("Testing process_data...")

        # Create a temporary directory for output
        output_dir: str = tempfile.mkdtemp()

        try:
            # Create a simple test dataset
            df: pd.DataFrame = pd.DataFrame({"description": ["Hello Spark", "Spark is fast", "Hello world"]})
            dataset: Dataset = Dataset.from_pandas(df)
            specific_words: List[str] = ["Hello", "Spark"]
            output_format: str = "parquet"

            # Call process_data using self.spark
            process_data(self.spark, dataset, output_dir, specific_words, output_format)

            # Check that output files exist in the temporary directory
            files: List[str] = os.listdir(output_dir)
            self.assertTrue(len(files) > 0, "process_data should write output files")
            print(f"Output files: ", files, "\n")
        finally:
            shutil.rmtree(output_dir)

    def test_process_data_all(self) -> None:
        """Test process_data_all with a small dataset to process all words"""
        print("Testing process_data_all...")
        
        # Create a temporary directory for output
        output_dir: str = tempfile.mkdtemp()

        try:
            # Create a simple test dataset
            df: pd.DataFrame = pd.DataFrame({"description": ["Alpha Beta", "Gamma Delta", "Alpha Gamma"]})
            dataset: Dataset = Dataset.from_pandas(df)
            output_format: str = "parquet"

            # Call process_data_all using self.spark
            process_data_all(self.spark, dataset, output_dir, output_format)
            
            # Check that output files exist in the temporary directory
            files: List[str] = os.listdir(output_dir)
            self.assertTrue(len(files) > 0, "process_data_all should write output files")
            print(f"Output files: ", files, "\n")

        finally:
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    unittest.main()