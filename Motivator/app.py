from flask import Flask, render_template, request, redirect
import csv
from datetime import datetime

app = Flask(__name__)

CSV_FILE = 'submissions.csv'

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        phone = request.form.get("phone")
        time_str = request.form.get("time")

        # Basic validation
        if not phone or not time_str:
            return "Missing info", 400

        # Save to CSV
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([phone, time_str, datetime.now().isoformat()])

        return redirect("/")  # Redirect after submission

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)