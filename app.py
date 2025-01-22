from flask import Flask, jsonify

app = Flask(__name__)

marker_name = ""
steps = 0
direction = ""

@app.route('/api/data', methods=['GET'])
def get_data():
    data = {
        "marker_name": marker_name,
        "steps": steps,
        "direction": direction
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)