if [ -d "venv" ]; then
    echo "Venv exists"
    echo "Assuming it's fine..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing deps..."
    pip install -r requirements.txt
fi

echo "Running game!"
python main.py