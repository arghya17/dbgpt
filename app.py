from flask import Flask, render_template, jsonify
import pandas as pd
import json

app = Flask(__name__)

# Load token usage data
CSV_FILE = "token_usage_logs.csv"
PRICE_CONFIG_FILE = "price_config.json"

# Load the CSV and Price Config
df = pd.read_csv("token_usage_logs.csv", parse_dates=["createTime"])
df["createTime"] = pd.to_datetime(df["createTime"], format="%Y-%m-%dT%H:%M:%S.%fZ", utc=True)

with open("price_config.json") as f:
    price_config = json.load(f)

@app.route("/api/data")
def get_data():
    # Convert DataFrame to JSON
    data = df.to_dict(orient="records")  # Converts each row to a dict (list of dicts)
    
    # Convert timestamps to string
    for row in data:
        row["createTime"] = row["createTime"].isoformat()  # Converts Timestamp to string

    return jsonify(data)


# Compute total input, output tokens, and cost
def compute_totals():
    total_input = df["promptTokenCount"].sum()
    total_output = df["candidateTokenCount"].sum()

    model_costs = {}
    for _, row in df.iterrows():
        model = row["model_ver"]
        input_tokens = row["promptTokenCount"]
        output_tokens = row["candidateTokenCount"]

        if model in price_config:
            input_cost = (input_tokens / 1_000_000) * price_config[model]["Input price$/million"]
            output_cost = (output_tokens / 1_000_000) * price_config[model]["Output price$/million"]
            model_costs[model] = model_costs.get(model, 0) + input_cost + output_cost

    total_cost = sum(model_costs.values())
    return total_input, total_output, total_cost, model_costs

@app.route("/api/prices")
def get_prices():
    return jsonify(price_config)


@app.route("/")
def index():
    return render_template("single.html")

if __name__ == "__main__":
    app.run(debug=True)