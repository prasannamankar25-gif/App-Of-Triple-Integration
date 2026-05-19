from flask import Flask, render_template, request, jsonify, session
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)
import random
import time
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # needed for session storage

# ─── SymPy symbol definitions ──────────────────────────────────────────────
x, y, z = sp.symbols('x y z')
TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
LOCAL_DICT = {
    'x': x, 'y': y, 'z': z,
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'exp': sp.exp, 'log': sp.log, 'ln': sp.log,
    'sqrt': sp.sqrt, 'pi': sp.pi, 'e': sp.E,
    'abs': sp.Abs,
}

# ─── Pre-built question bank with difficulty levels ────────────────────────
QUESTION_BANK = {
    "easy": [
        {
            "function": "1",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "1",
            "description": "Volume of a unit cube",
        },
        {
            "function": "x + y + z",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "1",
            "description": "Sum of coordinates over unit cube",
        },
        {
            "function": "xyz",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "2",
            "z_lower": "0", "z_upper": "3",
            "description": "Product of coordinates",
        },
        {
            "function": "x**2",
            "x_lower": "0", "x_upper": "2",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "1",
            "description": "x² over a box",
        },
        {
            "function": "2*x + 3*y",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "2",
            "description": "Linear function",
        },
    ],
    "medium": [
        {
            "function": "x**2 * y * z",
            "x_lower": "0", "x_upper": "2",
            "y_lower": "0", "y_upper": "3",
            "z_lower": "0", "z_upper": "1",
            "description": "Polynomial integrand",
        },
        {
            "function": "sin(x) * cos(y)",
            "x_lower": "0", "x_upper": "pi",
            "y_lower": "0", "y_upper": "pi/2",
            "z_lower": "0", "z_upper": "1",
            "description": "Trigonometric integrand",
        },
        {
            "function": "x**2 + y**2 + z**2",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "1",
            "description": "Sum of squares",
        },
        {
            "function": "exp(x) * y",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "2",
            "z_lower": "0", "z_upper": "1",
            "description": "Exponential × linear",
        },
        {
            "function": "x * y**2 * z**3",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "2",
            "description": "Mixed powers",
        },
    ],
    "hard": [
        {
            "function": "sin(x*y) * z",
            "x_lower": "0", "x_upper": "pi",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "2",
            "description": "Product argument trig",
        },
        {
            "function": "exp(x+y+z)",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "1",
            "description": "Exponential of sum",
        },
        {
            "function": "x**3 * sin(y) * cos(z)",
            "x_lower": "0", "x_upper": "2",
            "y_lower": "0", "y_upper": "pi",
            "z_lower": "0", "z_upper": "pi/2",
            "description": "Polynomial × trig product",
        },
        {
            "function": "sqrt(x) * y * exp(-z)",
            "x_lower": "0", "x_upper": "4",
            "y_lower": "0", "y_upper": "1",
            "z_lower": "0", "z_upper": "2",
            "description": "Square root × exponential decay",
        },
        {
            "function": "log(1+x) * y**2 * z",
            "x_lower": "0", "x_upper": "1",
            "y_lower": "0", "y_upper": "2",
            "z_lower": "0", "z_upper": "1",
            "description": "Logarithmic integrand",
        },
    ],
}


def parse_expression(expr_str: str):
    """
    Safely parse a string into a SymPy expression.
    Returns (expression, error_message).
    """
    try:
        expr = parse_expr(
            expr_str.strip(),
            local_dict=LOCAL_DICT,
            transformations=TRANSFORMATIONS,
        )
        return expr, None
    except Exception as e:
        return None, f"Could not parse '{expr_str}': {str(e)}"


def solve_triple_integral(func_str, x_lo, x_hi, y_lo, y_hi, z_lo, z_hi):
    """
    Solve ∫∫∫ f(x,y,z) dx dy dz over the given rectangular limits.
    Integrates in order: x first, then y, then z.

    Returns a dict with:
        result      – exact SymPy result
        numeric     – float approximation
        steps       – list of intermediate step strings
        error       – error string (or None)
    """
    # Parse all expressions
    f, err = parse_expression(func_str)
    if err:
        return {"error": f"Function: {err}"}

    limits = {"x_lower": x_lo, "x_upper": x_hi,
              "y_lower": y_lo, "y_upper": y_hi,
              "z_lower": z_lo, "z_upper": z_hi}
    parsed = {}
    for name, val in limits.items():
        expr, err = parse_expression(val)
        if err:
            return {"error": f"Limit '{name}': {err}"}
        parsed[name] = expr

    steps = []
    try:
        # Step 1 – integrate over x
        step1 = sp.integrate(f, (x, parsed["x_lower"], parsed["x_upper"]))
        step1_simplified = sp.simplify(step1)
        steps.append({
            "label": "Step 1 — Integrate over x",
            "expression": f"∫ ({func_str}) dx  from x={x_lo} to x={x_hi}",
            "result": str(step1_simplified),
        })

        # Step 2 – integrate over y
        step2 = sp.integrate(step1_simplified, (y, parsed["y_lower"], parsed["y_upper"]))
        step2_simplified = sp.simplify(step2)
        steps.append({
            "label": "Step 2 — Integrate over y",
            "expression": f"∫ (result) dy  from y={y_lo} to y={y_hi}",
            "result": str(step2_simplified),
        })

        # Step 3 – integrate over z
        step3 = sp.integrate(step2_simplified, (z, parsed["z_lower"], parsed["z_upper"]))
        final = sp.simplify(step3)
        steps.append({
            "label": "Step 3 — Integrate over z",
            "expression": f"∫ (result) dz  from z={z_lo} to z={z_hi}",
            "result": str(final),
        })

        numeric = float(final.evalf())
        return {
            "error": None,
            "result": str(final),
            "numeric": numeric,
            "steps": steps,
        }

    except Exception as e:
        return {"error": f"Integration failed: {str(e)}"}


# ─── Flask routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main page."""
    # Initialise session score tracking
    if "score" not in session:
        session["score"] = {"correct": 0, "total": 0}
    return render_template("index.html")


@app.route("/api/solve", methods=["POST"])
def api_solve():
    """
    Receive the problem from the browser, solve it, store the answer in
    the session, and return only a confirmation (not the answer yet).
    """
    data = request.get_json()
    required = ["function", "x_lower", "x_upper", "y_lower", "y_upper", "z_lower", "z_upper"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"Missing field: {field}"}), 400

    result = solve_triple_integral(
        data["function"],
        data["x_lower"], data["x_upper"],
        data["y_lower"], data["y_upper"],
        data["z_lower"], data["z_upper"],
    )

    if result["error"]:
        return jsonify({"error": result["error"]}), 400

    # Store answer in session so the client cannot see it
    session["current_answer"] = result["numeric"]
    session["current_steps"] = result["steps"]
    session["current_exact"] = result["result"]
    session.modified = True

    return jsonify({"status": "ok", "message": "Problem accepted. Start solving!"})


@app.route("/api/submit", methods=["POST"])
def api_submit():
    """
    Compare the user's answer with the stored answer.
    Returns verdict, correct answer, steps, and updated score.
    """
    if "current_answer" not in session:
        return jsonify({"error": "No active problem. Please start a problem first."}), 400

    data = request.get_json()
    user_answer_str = data.get("user_answer", "").strip()
    time_taken = data.get("time_taken", 0)

    if not user_answer_str:
        return jsonify({"error": "Please enter your answer before submitting."}), 400

    try:
        user_answer = float(user_answer_str)
    except ValueError:
        # Try parsing as a sympy expression
        try:
            user_answer = float(sp.sympify(user_answer_str).evalf())
        except Exception:
            return jsonify({"error": f"Cannot parse answer: '{user_answer_str}'"}), 400

    correct_answer = session["current_answer"]
    tolerance = 0.001
    is_correct = abs(user_answer - correct_answer) < tolerance

    # Update score
    score = session.get("score", {"correct": 0, "total": 0})
    score["total"] += 1
    if is_correct:
        score["correct"] += 1
    session["score"] = score
    session.modified = True

    return jsonify({
        "correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "exact_answer": session.get("current_exact", ""),
        "steps": session.get("current_steps", []),
        "time_taken": time_taken,
        "score": score,
    })


@app.route("/api/random_question", methods=["GET"])
def api_random_question():
    """Return a random question from the question bank."""
    difficulty = request.args.get("difficulty", "easy")
    if difficulty not in QUESTION_BANK:
        difficulty = "easy"
    question = random.choice(QUESTION_BANK[difficulty])
    return jsonify(question)


@app.route("/api/score", methods=["GET"])
def api_score():
    """Return the current session score."""
    return jsonify(session.get("score", {"correct": 0, "total": 0}))


@app.route("/api/reset_score", methods=["POST"])
def api_reset_score():
    """Reset the session score."""
    session["score"] = {"correct": 0, "total": 0}
    session.modified = True
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 55)
    print("  Triple Integration Practice App")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 55)
    app.run(debug=True, port=5000)
