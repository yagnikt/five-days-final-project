from flask import Flask, request, jsonify
from flask_cors import CORS
from travel_agent import TravelAgent

app = Flask(__name__)
CORS(app) # Allow cross-origin requests from the Vite frontend

agent = TravelAgent()

@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(agent.get_state())

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    response = agent.process_chat(user_input)
    return jsonify({"response": response, "state": agent.get_state()})

@app.route("/api/monitor", methods=["POST"])
def monitor():
    result = agent.check_flights()
    return jsonify({"result": result, "state": agent.get_state()})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
