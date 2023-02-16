from flask import Flask, request, jsonify              # Print to App Logger (Console)
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
	return "<h1>Nemo Backend</h1>"

@app.route("/", methods=['POST'])
def process_image():
	app.logger.info("This is a test, before checking for post")
	if request.method == "POST":
		app.logger.info("This is a test, after checking for post")
		form_data = request.get_data()
		app.logger.info(form_data)
		return "Hello World!"



if __name__ == "__main__":
    app.run()