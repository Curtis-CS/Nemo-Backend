from flask import Flask, request
from flask_cors import CORS
from PIL import Image
import subprocess
app = Flask(__name__)
CORS(app)


@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        file = request.files['file']
        filename = file.filename
        image = Image.open(file)
        image.save(filename)
        # print("In Testing Nemo")
        # subprocess.Popen(["python3", "./NemoModel/detr/test.py", 
        #                 "--data_path", "./NemoModel/Images/ImagesToRun/", 
        #                 "--resume", "./NemoModel/Nemo-DETR-dg.pth", 
        #                 "--output_dir", "./NemoModel/Images/ProcessedImages/", 
        #                 "--device" , "cpu", "--disp" ,"1"]).wait()
        return "Data Recieved, file Saved"

#Function to get all of the files Nemo Processed into an array
def GetProcessedImages():
    print("Getting Nemo Results")
    results = []
    return results

#Function to clean up the files so Nemo can run smoothly again
def CleanUpNemorun():
    print("Cleaning up Nemo Run")

if __name__ == "__main__":
    app.run(debug=True)
