from flask import Flask, jsonify, request

app = Flask(__name__)

# Global variables to store data
marker_name = ""
steps = 0
direction = ""

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Return current data in JSON format.
    :return: JSON object containing marker_name, steps, and direction.
    """
    data = {
        "marker_name": marker_name,
        "steps": steps,
        "direction": direction
    }
    return jsonify(data)

@app.route('/api/update', methods=['POST'])
def update_data():
    """
    Update data based on a POST request.
    :return: JSON object with status and message.
    """
    global marker_name, steps, direction
    new_data = request.json
    marker_name = new_data.get('marker_name', marker_name)
    steps = new_data.get('steps', steps)
    direction = new_data.get('direction', direction)

    print(f'Updated data: marker_name = {marker_name}, steps = {steps}, direction = {direction}')
    return jsonify({"status": "success", "message": "Data updated successfully"})

if __name__ == '__main__':
    app.run(debug=True)