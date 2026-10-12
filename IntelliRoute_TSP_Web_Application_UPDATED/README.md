# IntelliRoute — Intelligent Optimal Route Planning

A Flask web application for the DSA project **Intelligent Optimal Route Planning Using Bitmask Dynamic Programming for the Travelling Salesman Problem**.

## Features
- Starting city and destination selection
- Optimization by overall score, distance, time, cost, safety, or emissions
- Exact Bitmask Dynamic Programming TSP solver
- Route totals and individual route attributes
- Recent DP state transition visualization
- Uses the included `data/routes.csv` dataset

## Requirements
- Python 3.10 or newer
- Packages listed in `requirements.txt`

## Run in VS Code (Windows)
Open this extracted project folder in VS Code, then choose **Terminal → New Terminal** and run:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, switch the terminal profile to Command Prompt and run:

```cmd
py -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser. Keep the terminal open while using the app; press `Ctrl+C` to stop it.

## Algorithm
The solver uses `dp[mask][current_city]` and has time complexity `O(n² × 2ⁿ)`. The interface supports up to 10 cities total, including the starting city, because this is an exact exponential-time algorithm.

## Dataset note
The included route dataset is synthetic/illustrative. It is intended for academic demonstration, not real-world navigation. Where duplicate directional route records exist, the application uses the first matching record.
