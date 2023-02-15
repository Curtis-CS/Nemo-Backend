from flask import Flask, request, jsonify              # Print to App Logger (Console)
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        form_data = request.get_data()
        app.logger.info(form_data)
        return "Hello World!"


if __name__ == "__main__":
    print("This is a test")
    app.run()
