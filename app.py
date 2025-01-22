from flask import Flask, jsonify, request

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

# Endpoint do aktualizacji danych
@app.route('/api/update', methods=['POST'])
def update_data():
    global marker_name, steps, direction
    new_data = request.json
    marker_name = new_data.get('marker_name', marker_name)
    steps = new_data.get('steps', steps)
    direction = new_data.get('direction', direction)

    print(f'Updated data: marker_name = {marker_name}, steps = {steps}, direction = {direction}')
    return jsonify({"status": "success", "message": "Data updated successfully"})

if __name__ == '__main__':
    app.run(debug=True)