# Stop on error
set -e

# Conda setup
CONDA_BASE=$(conda info --base)
ENV_NAME="news_processing"

# Check Conda installation
if [ ! -d "$CONDA_BASE" ]; then
    echo "Error: Conda not found at $CONDA_BASE"
    exit 1
fi

# Activate Conda environment   
echo "Activating Conda environment '$ENV_NAME'..."
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$ENV_NAME" || { echo "Error: Failed to activate Conda environment '$ENV_NAME'"; exit 1; }

echo "Conda environment '$ENV_NAME' activated."

# Check Python executable
PYTHON_EXEC=$(command -v python) || { echo "Error: Python not found in Conda environment."; exit 1; }
echo "Using Python executable: $PYTHON_EXEC"

# Get the base directory
CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$(dirname "$CODE_DIR")"

# Set path for Docker environment
SRC_DIR="$CODE_DIR/src"
CONFIG_FILE="$CODE_DIR/config/config.yaml"
DATASET="news"
LOCAL_OUTPUT_DIR="$APP_DIR/ztmp/data"
OUTPUT_DIR="file://$LOCAL_OUTPUT_DIR"
LOGS_DIR="$APP_DIR/logs"

# Create output/logs directories if they don't exist
mkdir -p "$LOCAL_OUTPUT_DIR"
mkdir -p "$LOGS_DIR"

# Set PySpark Python paths 
export PYSPARK_PYTHON="$CONDA_BASE/envs/$ENV_NAME/bin/python"
export PYSPARK_DRIVER_PYTHON="$CONDA_BASE/envs/$ENV_NAME/bin/python"

# Call and run the Python script with the required arguments
echo "Running process_data..."
"$PYTHON_EXEC" "$SRC_DIR/run.py" process_data \
    --cfg "$CONFIG_FILE" \
    --dataset "$DATASET" \
    --dirout "$OUTPUT_DIR" \
    2>&1 | tee "$LOGS_DIR/Data_processed.txt"

echo "Running process_data_all..."
"$PYTHON_EXEC" "$SRC_DIR/run.py" process_data_all \
    --cfg "$CONFIG_FILE" \
    --dataset "$DATASET" \
    --dirout "$OUTPUT_DIR" \
    2>&1 | tee "$LOGS_DIR/Data_processed_all.txt"

echo "All processing completed successfully."