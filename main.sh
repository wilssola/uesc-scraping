#!bin/sh

pip install -r requirements.txt
python -m playwright install firefox
python main.py