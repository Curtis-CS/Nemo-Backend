from flask import Flask, request
from flask_cors import CORS
import base64
app = Flask(__name__)
CORS(app)


@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        image_data = request.json.get('imageB64Data')
        theData = str(image_data)
        theData = theData.replace('data:image/jpeg;base64,', '')
        app.logger.warning(theData)
        image_binary = base64.b64decode(theData)
        with open('image.jpg', 'wb') as f:
            f.write(image_binary)
        return "Data Recieved"

if __name__ == "__main__":
    app.run(debug=True)
