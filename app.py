from flask import Flask, request, jsonify              # Print to App Logger (Console)
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
	return "<h1>Nemo Backend</h1>"

@app.route("/", methods=['POST'])
def process_image():
	
	app.logger.warning("This is a test, before checking for post")
	if request.method == "POST":
		# formData = request.get_json()
		# app.logger.warning(formData)
		#print(request.form)
		image_file = request.files.get('image', '')
		app.logger.warning(image_file)
		return "The file was recieved!"
		



if __name__ == "__main__":
    app.run()