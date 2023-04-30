from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
import subprocess
import os
from pathlib import Path
import zipfile
import cv2
import shutil
import glob

app = Flask(__name__)
CORS(app)

files_to_send_back = []
cur_mp4_folders = []


@app.route("/", methods=['POST'])
def process_image():
    if request.method == "POST":
        # set 1 to plot encoder-decoder attention weights---default values
        disp_attention = 0
        disp_attention_bool = False
        # apply non-max suppression to bounding boxes---default values
        nmsup = .25
        # threshold for non-max suppression---default valuesw
        iou_threshold = .2

        # Receive Single File
        file = request.files['file']
        files_left = int(request.form['filesLeft']) - 1
        run_type = request.form['runType']
        disp_attention_bool = request.form['attention_weights']
        if (disp_attention_bool == "true"):
            disp_attention = 1
        filename = file.filename

        runFolder = "./ImagesToRun/"

        if (CheckFileType(filename)):
            print ("VIDEO FILE DETECTED")
            print("RUN TYPE = ", run_type)
            file.save(filename)
            
            outputDir = "F" + filename[:-4]
            get_frames(filename, outputDir, 1, 30)
            p = Path(runFolder + filename)
            for fileN in os.listdir(outputDir):
                shutil.copy(os.path.join(outputDir, fileN), os.path.join(runFolder, fileN))
            cur_mp4_folders.append(outputDir)
            # Run Nemo Model Once all Images Have Arrived
            if (files_left < 1):
                if (run_type == True):
                    print("SINGLE CLASS RUN")
                    run_nemo_single(disp_attention, nmsup, iou_threshold, runFolder)

                else:
                    print("DENSITY CLASS RUN")
                    run_nemo_density(disp_attention, nmsup, iou_threshold, runFolder)

                path = os.path.abspath('results.zip')
                # app.logger.warning(path)
                # app.logger.warning(os.path.getsize(path))
                cur_mp4_folders.clear()
                return send_file(path, mimetype='application/zip')
            else:
                return "none"
        else:
            image = Image.open(file)

            p = Path(runFolder + filename)
            image.save(p)

            print("RUN TYPE = ", run_type)
            # Run Nemo Model Once all Images Have Arrived
            if (files_left < 1):
                #get_frames('20160604-FIRE-smer-tcs3-mobo-c.mp4', 'mp4split', 1, 30)
                if (run_type == True):
                    print("SINGLE CLASS RUN")
                    run_nemo_single(disp_attention, nmsup, iou_threshold, runFolder)

                else:
                    print("DENSITY CLASS RUN")
                    run_nemo_density(disp_attention, nmsup, iou_threshold, runFolder)

                path = os.path.abspath('results.zip')
                # app.logger.warning(path)
                # app.logger.warning(os.path.getsize(path))
                cur_mp4_folders.clear()
                return send_file(path, mimetype='application/zip')
            else:
                return "none"


# Run Nemo
def run_nemo_density(disp_attention, nmsup, iou_threshold, imagesToRun):
    print("Running Nemo")
    subprocess.call(["python3", "./NemoModel/detr/test.py",
                     "--data_path", imagesToRun,
                     "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                     "--output_dir", "./ProcessedImages/",
                     "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention),
                     "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)])  # .wait()
    get_processed_images(disp_attention, nmsup, iou_threshold)
    clean_up_nemo_run(disp_attention, nmsup, iou_threshold)


def run_nemo_single(disp_attention, nmsup, iou_threshold, imagesToRun):
    print("Running Nemo")
    subprocess.call(["python3", "./NemoModel/detr/test.py",
                     "--data_path", imagesToRun,
                     "--resume", "./NemoModel/Nemo-DETR-dg.pth",
                     "--output_dir", "./ProcessedImages/",
                     "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention),
                     "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)])  # .wait()
    get_processed_images(disp_attention, nmsup, iou_threshold)
    clean_up_nemo_run(disp_attention, nmsup, iou_threshold)


def get_processed_images(disp_attention, nmsup, iou_threshold):
    """ Function to append processed Nemo files to an array. """
    files_to_send_back.clear()

    #If any video files were processed
    if (len(cur_mp4_folders) > 0):
        print("Creating GIF")
        processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
        smokeDetectedOnes = []
        for file in os.listdir(processed_images_dir):
            x = 0
            while (x < len(cur_mp4_folders)):
                # print(cur_mp4_folders[x])
                # print(type(cur_mp4_folders[x]))
                # print(file)
                # print(type(file))
                detectedCommonName = cur_mp4_folders[x][1:] in file
                # print(detectedCommonName)
                if (detectedCommonName):
                    # print("SMOKE DETECTED")
                    smokeDetectedOnes.append(file)
                x = x + 1
        print("Formatting GIF Folder")
        for dir in cur_mp4_folders:
            print(dir)
            beforeNemoFiles = os.listdir(dir)
            for file in beforeNemoFiles:
                #print(file)
                for detectFile in smokeDetectedOnes:
                    #print(detectFile)
                    if (file in detectFile):
                        #print("Replace file: ", os.path.join(dir, file))
                        #print("With detected file: ", os.path.join(processed_images_dir[2:], detectFile))
                        os.replace(os.path.join(processed_images_dir[2:], detectFile), os.path.join(dir, file))
            CreateGIF(dir)


    for name in files_to_send_back:
        print(name)
    print("Getting Nemo Results")
    if (disp_attention == 0):
        processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
        index = 0
        for file in os.listdir(processed_images_dir):
            files_to_send_back.append(os.path.join(processed_images_dir, file))
            index = index + 1

    else:
        attention_dir = './ProcessedImages/Attn_viz'
        for file in os.listdir(attention_dir):
            files_to_send_back.append(os.path.join(attention_dir, file))
        # Sorting of Files
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
        # print(os.path.basename(fileName))
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
    for dir in cur_mp4_folders:
        shutil.rmtree(dir)
        #print(dir)

def get_frames(input_file, output_folder, step, count):
    '''
    Input:
      inputFile - name of the input file with directory
      outputFolder - name and path of the folder to save the results
      step - time-lapse between each step (in seconds)
      count - number of screenshots
    Output:
      'count' number of screenshots that are 'step' seconds apart created from video 'inputFile' and stored
      in folder 'outputFolder'
    Function Call:
        get_frames("test.mp4", 'data', 10, 10)
    '''

    frames_captured = 0
    current_frame = 0

    # creating a folder
    try:
        os.makedirs(output_folder, exist_ok=True)
    except OSError:
        print('Error! Could not create a directory')

    # reading the video from specified path
    cap = cv2.VideoCapture(input_file)

    # reading the number of frames at that particular second
    fps = cap.get(cv2.CAP_PROP_FPS)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    videoLengthSeconds = length / fps
    if (videoLengthSeconds > 60):
        print("Long: ", videoLengthSeconds)
    else:
        print("Short: ", videoLengthSeconds)
        # count = 30
        # step = videoLengthSeconds / count


    while True:
        ret, frame = cap.read()
        if ret:
            if current_frame > (step * fps):
                current_frame = 0

                # saving the frames (screenshots)
                name = f"{output_folder}/{os.path.splitext(os.path.basename(input_file))[0]}_{frames_captured}.png"
                # print(f'Creating {name}')

                cv2.imwrite(name, frame)
                frames_captured += 1

                # breaking the loop when count achieved
                if frames_captured > count - 1:
                    break

            current_frame += 1
        else:
            break

    # Releasing all space and windows once done
    cap.release()
    cv2.destroyAllWindows()
    os.remove(input_file)

def CheckFileType(filename):
    splitType = filename.split(".")
    type = splitType[1]
    #print(type)
    if (type == "mp4"):
        return True
    else:
        return False

def CreateGIF(dir):
    print("MAKING GIF")
    # specify the file path of the directory containing the images
    image_directory = dir#'path/to/directory'

    # use glob to get a list of all image file names in the directory
    image_file_names = glob.glob(f"{image_directory}/*.png")

    # sort the file names in numerical order
    image_file_names.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))

    # create a list to store the images
    image_list = []
    width, height = 1333, 1000
    # loop through the file names and open each image using Pillow
    for file_name in image_file_names:
        image = Image.open(file_name)
        image = image.resize((width, height))
        image_list.append(image)
        #print(image.size)
    #print(image_file_names)
    # specify the name and file format of the output GIF
    output_file_name = dir + ".gif"

    # specify the duration of each frame in milliseconds
    duration = 300

    # use Pillow to save the list of images as a GIF
    image_list[0].save(os.path.join("./ProcessedImages/Inferences-ImagesToRun/", output_file_name), save_all=True, append_images=image_list[1:], duration=duration, loop=0)

if __name__ == "__main__":
    app.run(debug=True)
