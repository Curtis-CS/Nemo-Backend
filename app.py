from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
import subprocess
import os
from pathlib import Path
import zipfile
app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        file = request.files['file']
        filesLeft = int(request.form['filesLeft']) - 1
        app.logger.warning(filesLeft)
        filename = file.filename
        image = Image.open(file)

        p = Path('./ImagesToRun/' + filename)
        image.save(p)
        if (filesLeft < 1):
            RunNemo()
            path = os.path.abspath('results.zip')
            #app.logger.warning(path)
            #app.logger.warning(os.path.getsize(path))
            return send_file(path, mimetype='application/zip')
        return 'null'

# Run Nemo
def RunNemo():
    print ("Running Nemo")
    print("In Testing Nemo")
    subprocess.Popen(["python3", "./NemoModel/detr/test.py", 
                    "--data_path", "./ImagesToRun/", 
                    "--resume", "./NemoModel/Nemo-DETR-dg.pth", 
                    "--output_dir", "./ProcessedImages/", 
                    "--device" , "cpu", "--disp" ,"1"]).wait()
    zipFile = GetProcessedImages()
    CleanUpNemorun()
    return zipFile
    

#Function to get all of the files Nemo Processed into an array
def GetProcessedImages():
    print("Getting Nemo Results")
    processedImagesDir = './ProcessedImages/Inferences-ImagesToRun'
    filesToSendBack = []
    for file in os.listdir(processedImagesDir):
        filesToSendBack.append(os.path.join(processedImagesDir, file))
    zipFileToSend = zipfile.ZipFile('results.zip', 'w')
    for fileName in filesToSendBack:
        zipFileToSend.write(fileName)
        #app.logger.warning(fileName)
    zipFileToSend.close()

#Function to clean up the files so Nemo can run smoothly again
def CleanUpNemorun():
    print("Cleaning up Nemo Run")
    processedImagesDir = './ProcessedImages/Inferences-ImagesToRun'
    for file in os.listdir(processedImagesDir):
        os.remove(os.path.join(processedImagesDir, file))
    imagesToRunDir = './ImagesToRun'
    for file in os.listdir(imagesToRunDir):
        os.remove(os.path.join(imagesToRunDir, file))

if __name__ == "__main__":
    app.run(debug=True)
