from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
import subprocess
import os
from pathlib import Path
import zipfile

app = Flask(__name__)
CORS(app)

files_to_send_back = []

@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        #set 1 to plot encoder-decoder attention weights---default values
        disp_attention = 0
        disp_attention_bool = False
        #apply non-max suppression to bounding boxes---default values
        nmsup = .25
        #threshold for non-max suppression---default valuesw
        iou_threshold = .2

        # Receive Single File
        file = request.files['file']
        files_left = int(request.form['filesLeft']) - 1
        run_type = request.form['runType']
        disp_attention_bool = request.form['attention_weights']
        if (disp_attention_bool == "true"):
            disp_attention = 1
        filename = file.filename
        image = Image.open(file)

        p = Path('./ImagesToRun/' + filename)
        image.save(p)

        print("RUN TYPE = ", run_type)

        # Run Nemo Model Once all Images Have Arrived
        if (files_left < 1):
            if (run_type == True):
                print("SINGLE CLASS RUN")
                run_nemo_single(disp_attention, nmsup, iou_threshold)

            else:
                print("DENSITY CLASS RUN")
                run_nemo_density(disp_attention, nmsup, iou_threshold)

            path = os.path.abspath('results.zip')
            # app.logger.warning(path)
            # app.logger.warning(os.path.getsize(path))
            return send_file(path, mimetype='application/zip')
        else:
            return "none"


# Run Nemo
def run_nemo_density(disp_attention, nmsup, iou_threshold):
    print("Running Nemo")
    subprocess.call(["python3", "./NemoModel/detr/test.py",
                      "--data_path", "./ImagesToRun/",
                      "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                      "--output_dir", "./ProcessedImages/",
                      "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention), 
                      "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)])#.wait()
    get_processed_images(disp_attention, nmsup, iou_threshold)
    clean_up_nemo_run(disp_attention, nmsup, iou_threshold)


def run_nemo_single(disp_attention, nmsup, iou_threshold):
    print("Running Nemo")
    subprocess.call(["python3", "./NemoModel/detr/test.py",
                      "--data_path", "./ImagesToRun/",
                      "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                      "--output_dir", "./ProcessedImages/",
                      "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention), 
                      "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)])#.wait()
    get_processed_images(disp_attention, nmsup, iou_threshold)
    clean_up_nemo_run(disp_attention, nmsup, iou_threshold)


def get_processed_images(disp_attention, nmsup, iou_threshold):
    """ Function to append processed Nemo files to an array. """
    files_to_send_back.clear()
    for name in files_to_send_back:
        print(name)
    print("Getting Nemo Results")
    if (disp_attention == 0):
        processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
        index = 0
        for file in os.listdir(processed_images_dir):
            files_to_send_back.append(os.path.join(processed_images_dir, file))
            index = index+1

    else:
        attention_dir = './ProcessedImages/Attn_viz'
        for file in os.listdir(attention_dir):
            files_to_send_back.append(os.path.join(attention_dir, file))
        #Sorting of Files
        # if (index > 1):
        #     x = 1
        #     y = index
        #     while (index < len(files_to_send_back)):
        #         files_to_send_back.insert(x, files_to_send_back[index])
        #         files_to_send_back.pop(index + 1)
        #         index = index + 1
        #         x = x + 2

    zip_file_to_send = zipfile.ZipFile('results.zip', 'w')
    for fileName in files_to_send_back:
        #print(os.path.basename(fileName))
        zip_file_to_send.write(fileName, os.path.basename(fileName))
        # app.logger.warning(fileName)
    zip_file_to_send.close()


def clean_up_nemo_run(disp_attention, nmsup, iou_threshold):
    """ Function to clean up files for Nemo to run again. """
    print("Cleaning up Nemo Run")
    processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
    for file in os.listdir(processed_images_dir):
        os.remove(os.path.join(processed_images_dir, file))
    images_to_run_dir = './ImagesToRun'
    for file in os.listdir(images_to_run_dir):
        os.remove(os.path.join(images_to_run_dir, file))
    if (disp_attention == 1):
        attention_dir = './ProcessedImages/Attn_viz'
        for file in os.listdir(attention_dir):
            os.remove(os.path.join(attention_dir, file))

if __name__ == "__main__":
    app.run(debug=True)
