#!/bin/bash
# Start the AI Search API server

echo "Starting AI Search API..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected"
    echo "Consider activating your venv first:"
    echo "  source venv/bin/activate"
    echo ""
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH:-.}"

# Start the server
echo "Starting server on http://0.0.0.0:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""

python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
