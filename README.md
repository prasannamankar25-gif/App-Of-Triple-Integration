# Triple Integral Lab 🔢∭

A browser-based practice app for triple integrals, powered by Python + SymPy.

## Quick Start

```bash
# 1. Install dependencies
pip install flask sympy

# 2. Run the app
python app.py

# 3. Open your browser
#    http://127.0.0.1:5000
```

## Features

| Feature | Details |
|---|---|
| **Dynamic solving** | SymPy performs exact symbolic triple integration |
| **Live preview** | Integral notation updates as you type |
| **Timer** | Tracks how long you take to solve each problem |
| **Answer checking** | Tolerant float comparison (±0.001) |
| **Step-by-step** | See the intermediate integrals after submitting |
| **Random questions** | 15 built-in problems across Easy / Medium / Hard |
| **Score tracking** | Persistent per-session correct/total counter |

## Input Format

**Function:** Use standard Python/SymPy math syntax:
- `xyz` → x×y×z  (implicit multiplication is on)
- `x**2 * sin(y) * exp(-z)`
- `sqrt(x) * log(1+y)`

**Limits:** Numbers or expressions:
- `0`, `1`, `2`
- `pi`, `pi/2`
- `-1`, `e`

## Project Structure

```
triple_integral_app/
├── app.py              ← Flask backend + SymPy integration logic
├── requirements.txt
├── README.md
└── templates/
    └── index.html      ← Single-page frontend (HTML/CSS/JS)
```
