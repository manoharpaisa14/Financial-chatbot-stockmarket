from flask import Flask, request, jsonify
import google.generativeai as genai
import yfinance as yf
from flask_cors import CORS
import os
import time
from pymongo import MongoClient
from bson import ObjectId
from config import GEMINI_API_KEY, MONGO_URI

app = Flask(__name__)
CORS(app)

# Load API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not GEMINI_API_KEY or not MONGO_URI:
    raise ValueError("GEMINI_API_KEY or MONGO_URI is missing! Please check your environment variables.")

# Configure Google Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Connect to MongoDB

try:
    client = MongoClient(MONGO_URI)
    db = client["finance_chatbot"]
except Exception as e:
    raise ValueError(f"Error connecting to MongoDB: {str(e)}")

chat_collection = db["chats"]
stock_collection = db["stocks"]
watchlist_collection = db["watchlist"]

@app.route("/chatbot", methods=["GET"])
def chatbot():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Please ask a question."}), 400

    for _ in range(3):  # Retry 3 times in case of errors
        try:
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = model.generate_content(query)
            bot_reply = response.text

            # Store query and response in MongoDB
            chat_collection.insert_one({"query": query, "response": bot_reply})
            
            return jsonify({"response": bot_reply})
        
        except Exception as e:
            time.sleep(5)  # Wait 5 seconds before retrying
            return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

    return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

@app.route("/stock", methods=["GET"])
def stock():
    symbol = request.args.get("symbol", "RELIANCE.NS")  # Default to Reliance (NSE)

    try:
        stock_data = yf.Ticker(symbol)
        hist = stock_data.history(period="1d")

        if hist.empty:
            return jsonify({"error": "Invalid stock symbol or no data available"}), 404

        # Convert NumPy types to Python types before storing in MongoDB
        stock_info = {
            "symbol": symbol,
            "current_price": float(hist["Close"].iloc[-1]),
            "open": float(hist["Open"].iloc[-1]),
            "high": float(hist["High"].iloc[-1]),
            "low": float(hist["Low"].iloc[-1]),
            "volume": int(hist["Volume"].iloc[-1]),  # Convert to Python int
        }

        # Store stock queries in MongoDB
        inserted_id = stock_collection.insert_one(stock_info).inserted_id
        stock_info["_id"] = str(inserted_id)  # Convert ObjectId to string

        return jsonify(stock_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add stock to watchlist
@app.route("/add-watchlist", methods=["POST"])
def add_watchlist():
    data = request.json
    symbol = data.get("symbol")

    if not symbol:
        return jsonify({"error": "Stock symbol required"}), 400

    # Prevent duplicate entries
    if watchlist_collection.find_one({"symbol": symbol}):
        return jsonify({"message": f"{symbol} is already in the watchlist."}), 409

    watchlist_collection.insert_one({"symbol": symbol})
    return jsonify({"message": f"{symbol} added to watchlist!"})

# Retrieve watchlist
@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    watchlist = list(watchlist_collection.find({}, {"_id": 0}))
    return jsonify({"watchlist": watchlist})

if __name__ == "__main__":
    app.run(debug=False, port=8000)
