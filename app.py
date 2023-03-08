from flask import Flask, request
from flask_cors import CORS
import base64
import subprocess
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
        # print("In Testing Nemo")
        # subprocess.Popen(["python3", "./NemoModel/detr/test.py", 
        #                 "--data_path", "./NemoModel/Images/ImagesToRun/", 
        #                 "--resume", "./NemoModel/Nemo-DETR-dg.pth", 
        #                 "--output_dir", "./NemoModel/Images/ProcessedImages/", 
        #                 "--device" , "cpu", "--disp" ,"1"]).wait()
        return "Data Recieved"

if __name__ == "__main__":
    app.run(debug=True)
