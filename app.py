from flask import Flask, render_template, jsonify, request

import pandas as pd
import json

app = Flask(__name__)

# Load token usage data
CSV_FILE = "token_usage_logs.csv"
PRICE_CONFIG_FILE = "price_config.json"

# Load CSV into DataFrame
df = pd.read_csv(CSV_FILE)

# Convert timestamps to a standard format
df["createTime"] = pd.to_datetime(df["createTime"])

# Load price config
with open(PRICE_CONFIG_FILE, "r") as f:
    price_config = json.load(f)


@app.route("/")
def index():
    return render_template("single.html")


@app.route("/api/data")
def get_data():
    # Convert DataFrame to JSON format
    data = df.to_dict(orient="records")
    return jsonify(data)


@app.route("/api/prices")
def get_prices():
    return jsonify(price_config)

@app.route("/api/update-prices", methods=["POST"])
def update_prices():
    global price_config
    new_prices = request.json
    price_config.update(new_prices)
    return jsonify({"message": "Prices updated successfully!"})


if __name__ == "__main__":
    app.run(debug=True)