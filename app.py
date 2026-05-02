from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Server çalışıyor"

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
