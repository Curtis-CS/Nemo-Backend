from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
import subprocess
import os
from pathlib import Path
import zipfile

app = Flask(__name__)
CORS(app)

#set 1 to plot encoder-decoder attention weights---default values
disp_attention = 0
#apply non-max suppression to bounding boxes---default values
nmsup = .25
#threshold for non-max suppression---default valuesw
iou_threshold = .2

@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        # Receive Single File
        file = request.files['file']
        files_left = int(request.form['filesLeft']) - 1
        run_type = request.form['runType']
        app.logger.warning(files_left)
        filename = file.filename
        image = Image.open(file)

        p = Path('./ImagesToRun/' + filename)
        image.save(p)

        print("RUN TYPE= ", run_type)

        # Run Nemo Model Once all Images Have Arrived
        if files_left < 1:
            if (run_type == True):
                print("SINGLE CLASS RUN")
                run_nemo_single()

            else:
                print("DENSITY CLASS RUN")
                run_nemo_density()

            path = os.path.abspath('results.zip')
            # app.logger.warning(path)
            # app.logger.warning(os.path.getsize(path))
            return send_file(path, mimetype='application/zip')
        return 'null'


# Run Nemo
def run_nemo_density():
    print("Running Nemo")
    print(disp_attention)
    subprocess.Popen(["python3", "./NemoModel/detr/test.py",
                      "--data_path", "./ImagesToRun/",
                      "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                      "--output_dir", "./ProcessedImages/",
                      "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention), 
                      "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)]).wait()
    get_processed_images()
    clean_up_nemo_run()


def run_nemo_single():
    print("Running Nemo")
    subprocess.Popen(["python3", "./NemoModel/detr/test.py",
                      "--data_path", "./ImagesToRun/",
                      "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                      "--output_dir", "./ProcessedImages/",
                      "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention), 
                      "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)]).wait()
    get_processed_images()
    clean_up_nemo_run()


def get_processed_images():
    """ Function to append processed Nemo files to an array. """
    print("Getting Nemo Results")
    processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
    files_to_send_back = []
    for file in os.listdir(processed_images_dir):
        files_to_send_back.append(os.path.join(processed_images_dir, file))
    zip_file_to_send = zipfile.ZipFile('results.zip', 'w')
    for fileName in files_to_send_back:
        zip_file_to_send.write(fileName)
        # app.logger.warning(fileName)
    zip_file_to_send.close()


def clean_up_nemo_run():
    """ Function to clean up files for Nemo to run again. """
    print("Cleaning up Nemo Run")
    processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
    for file in os.listdir(processed_images_dir):
        os.remove(os.path.join(processed_images_dir, file))
    images_to_run_dir = './ImagesToRun'
    for file in os.listdir(images_to_run_dir):
        os.remove(os.path.join(images_to_run_dir, file))


if __name__ == "__main__":
    app.run(debug=True)
