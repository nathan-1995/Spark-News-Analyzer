"""
run.py processes the AG News dataset and counts the occurrences of specific words or all words in the dataset. 
The script reads the dataset, cleans the text, and extracts words from the description column. 
It then counts the occurrences of specific words or all words and saves the results to a specified output format.
"""

import os
import logging
import yaml
import argparse
import datetime
from typing import Dict, List, Any
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, regexp_replace, split, explode, count
from datasets import load_dataset, Dataset

# for local testing
# os.environ["PYSPARK_PYTHON"] = r"C:\Users\ndeli\miniconda3\envs\news_processing\python.exe"
# os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\ndeli\miniconda3\envs\news_processing\python.exe"

def setup_logging(config_path: str) -> Dict[str, Any]:
    """Set up logging based on config file"""
    with open(config_path, "r") as f:
        config: Dict[str, Any] = yaml.safe_load(f)

    # Get project root (two levels up from script location)
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Set up log file path and create directory
    log_file: str = os.path.join(PROJECT_ROOT, config["log_file"].lstrip("./").lstrip("../"))
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    return config


def main() -> None:
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Process AG News Dataset")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common arguments that will be used for both subparsers
    common_args: Dict[str, Dict[str, Any]] = {
        "--cfg": {"required": True, "help": "Path to config file"},
        "--dataset": {"required": True, "help": "Dataset name"},
        "--dirout": {"required": True, "help": "Output directory"}
    }

    # Add subparsers with common arguments
    parser_data = subparsers.add_parser("process_data", help="Process dataset for specific words") # Can be called by python src/run.py process_data --cfg config/cfg.yaml --dataset news --dirout "ztmp/data/"

    parser_all = subparsers.add_parser("process_data_all", help="Process dataset for all unique words") # Can be called by python src/run.py process_data_all --cfg config/cfg.yaml --dataset news --dirout "ztmp/data/"
    
    # Loop through subparsers and add common arguments
    for parser_sub in [parser_data, parser_all]:
        for arg, options in common_args.items():
            parser_sub.add_argument(arg, **options)

    args: argparse.Namespace = parser.parse_args()

    # Get absolute path of config file relative to code directory
    CODE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path: str = os.path.join(CODE_DIR, args.cfg)

    # Set up logging and get config
    config: Dict[str, Any] = setup_logging(config_path)

    # Validate config fields
    required_keys: List[str] = ["specific_words", "log_file", "dataset_split", "output_format", "spark_settings"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key in config: {key}")

    dataset_split: str = config["dataset_split"]
    output_format: str = config["output_format"]
    spark_settings: Dict[str, str] = config["spark_settings"]

    if "driver_memory" not in spark_settings or "executor_memory" not in spark_settings:
        raise ValueError("'spark_settings' in config.yaml must contain 'driver_memory' and 'executor_memory'.")

    # Initialize Spark session
    spark: SparkSession = SparkSession.builder.appName("NewsProcessing") \
        .config("spark.driver.memory", spark_settings["driver_memory"]) \
        .config("spark.executor.memory", spark_settings["executor_memory"]) \
        .config("spark.driver.cores", spark_settings["cores"]) \
        .config("spark.executor.cores", spark_settings["cores"]) \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .getOrCreate()

    logging.info("Spark session initialized")

    try:
        dataset: Dataset = load_dataset("sh0416/ag_news", split=dataset_split) # Only using test split
        logging.info("Dataset loaded successfully")

        # Call the function process_data or process_data_all based on the command
        if args.command == "process_data":
            specific_words: List[str] = config["specific_words"]
            if not specific_words or not isinstance(specific_words, list):
                raise ValueError("'specific_words' in config.yaml must be a non-empty list.")
            process_data(spark, dataset, args.dirout, specific_words, output_format)

        elif args.command == "process_data_all":
            process_data_all(spark, dataset, args.dirout, output_format)

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise
    finally:
        spark.stop()
        logging.info("Spark session stopped")
        print("Spark session stopped")



def process_data(spark: SparkSession, dataset: Dataset, output_dir: str, specific_words: List[str], output_format: str) -> None:
    """Process the dataset and count occurrences of specific words (case-sensitive)"""
    df_words: DataFrame = process_text(spark, dataset)

    # Only filter for words in the config.yaml
    df_filtered: DataFrame = df_words.filter(col("word").isin(specific_words))

    # Save results
    save_word_counts(df_filtered, output_dir, "word_count", output_format)


def process_data_all(spark: SparkSession, dataset: Dataset, output_dir: str, output_format: str) -> None:
    """Process the dataset and count occurrences of all words"""
    df_words: DataFrame = process_text(spark, dataset)  # No filtering, includes all words

    # Save results
    save_word_counts(df_words, output_dir, "word_count_all", output_format)


def process_text(spark: SparkSession, dataset: Dataset) -> DataFrame:
    """Extract words from the dataset description column after cleaning the text"""
    pdf = dataset.to_pandas()
    df: DataFrame = spark.createDataFrame(pdf) # Convert to Spark DataFrame

    # Clean and process text while keeping case sensitivity
    df_clean: DataFrame = df.withColumn("description_clean", regexp_replace(col("description"), r"[^\w\s]", " "))

    # Explode words into separate rows
    return df_clean.withColumn("word", explode(split(col("description_clean"), r"\s+"))).filter(col("word") != "")


def save_word_counts(df_words: DataFrame, output_dir: str, filename_prefix: str, output_format: str) -> None:
    """Count occurrences of words and save results to specified format"""
    # Count occurrences of each word
    word_count_df: DataFrame = df_words.groupBy("word").agg(count("*").alias("word_count")) \
        .orderBy(col("word_count").desc())  # Sort in descending order

    logging.info(f"Word count results for {filename_prefix} before saving:")
    word_count_df.show(n=5, truncate=False)  

    # Generate output path
    date_str: str = datetime.datetime.now().strftime("%Y%m%d")
    output_path: str = os.path.join(output_dir, f"{filename_prefix}_{date_str}.{output_format}")

    word_count_df.write.mode("overwrite").parquet(output_path)  # Save results
    logging.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
    