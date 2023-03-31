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
        # Receive Single File
        file = request.files['file']
        files_left = int(request.form['filesLeft']) - 1
        app.logger.warning(files_left)
        filename = file.filename
        image = Image.open(file)

        p = Path('./ImagesToRun/' + filename)
        image.save(p)
        # Run Nemo Model Once all Images Have Arrived
        if files_left < 1:
            run_nemo()
            path = os.path.abspath('results.zip')
            # app.logger.warning(path)
            # app.logger.warning(os.path.getsize(path))
            return send_file(path, mimetype='application/zip')
        return 'null'


# Run Nemo
def run_nemo():
    print("Running Nemo")
    print("In Testing Nemo")
    subprocess.Popen(["python3", "./NemoModel/detr/test.py", 
                    "--data_path", "./ImagesToRun/", 
                    "--resume", "./NemoModel/Nemo-DETR-dg.pth", 
                    "--output_dir", "./ProcessedImages/", 
                    "--device" , "cpu", "--disp" ,"1"]).wait()
    zipFile = GetProcessedImages()
    CleanUpNemoRun()
    return zipFile
    

def GetProcessedImages():
    """ Function to append processed Nemo files to an array. """
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

def CleanUpNemoRun():
    """Function to clean up files for Nemo to run again. """
    print("Cleaning up Nemo Run")
    processedImagesDir = './ProcessedImages/Inferences-ImagesToRun'
    for file in os.listdir(processedImagesDir):
        os.remove(os.path.join(processedImagesDir, file))
    imagesToRunDir = './ImagesToRun'
    for file in os.listdir(imagesToRunDir):
        os.remove(os.path.join(imagesToRunDir, file))

if __name__ == "__main__":
    app.run(debug=True)
