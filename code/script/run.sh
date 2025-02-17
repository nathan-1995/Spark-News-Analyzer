# Stop on error
set -e

# Conda setup
CONDA_BASE="/opt/conda"
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

# Set path for Docker environment
BASE_DIR="/app"  
SCRIPT_DIR="$BASE_DIR/src"
CONFIG_FILE="$BASE_DIR/config/config.yaml"
OUTPUT_DIR="$BASE_DIR/ztmp/data/"
DATASET="news"

# Set PySpark Python paths 
export PYSPARK_PYTHON="$CONDA_BASE/envs/$ENV_NAME/bin/python"
export PYSPARK_DRIVER_PYTHON="$CONDA_BASE/envs/$ENV_NAME/bin/python"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Call and run the Python script with the required arguments
for process in "process_data" "process_data_all"; do
    echo "Running $process..."
    "$PYTHON_EXEC" "$SCRIPT_DIR/run.py" "$process" --cfg "$CONFIG_FILE" --dataset "$DATASET" --dirout "$OUTPUT_DIR"
done

echo "All processing completed successfully."