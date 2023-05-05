# Backend server running 
from flask import Flask, request, send_file
from flask_cors import CORS
# For opening and saving images
from PIL import Image
# For running nemo model
import subprocess
import os
from pathlib import Path
# Used for zipping results to send back
import zipfile
# For reading in and splitting video files
import cv2
# For copying files
import shutil
# For reading in files to convert to GIF
import glob

# For slower computers to give time to copy files
import time

app = Flask(__name__)
CORS(app)

files_to_send_back = []
cur_mp4_folders = []


@app.route("/", methods=['POST', 'GET'])
def process_image():
    
    disp_attention = 0                          # set 1 to plot encoder-decoder attention weights---default values
    file = ''
    filename = ''
    files_left = 0
    iou_threshold = .2                          # threshold for non-max suppression---default values
    nmsup = .25                                 # apply non-max suppression to bounding boxes---default values
    run_folder = "./ImagesToRun/"
    run_type = True
    
    # If test run method
    if request.method == "GET":
        filename = '1465065728_+00060.jpg'
        files_left = 0

    # Else it is uploading files
    elif request.method == "POST":
        file = request.files['file']
        files_left = int(request.form['filesLeft']) - 1
        run_type = request.form['runType']
        disp_attention_bool = request.form['attention_weights']
        iou_threshold = request.form['iou_thresh']
        nmsup = request.form['nmsup']
        if disp_attention_bool == "true":
            disp_attention = 1
        filename = file.filename

    # Handle Video File
    if check_file_type(filename):
        file.save(filename)
        
        output_dir = "F" + filename[:-4]
        get_frames(filename, output_dir)
        for fileN in os.listdir(output_dir):
            shutil.copy(os.path.join(output_dir, fileN), os.path.join(run_folder, fileN))
        cur_mp4_folders.append(output_dir)
    
    # Handle Image File
    else:
        # If test run method
        if request.method == "GET":
            shutil.copy('defaultImages/1465065728_+00060.jpg', os.path.join(run_folder, filename))

        # Else it is uploaded files from user method
        elif request.method == "POST":
            image = Image.open(file)
            p = Path(run_folder + filename)
            image.save(p)

    # Run Nemo Model Once all files Have Arrived
    if files_left < 1:
        
        # If single class run
        if run_type == "true":
            print("SINGLE CLASS RUN")
            path_to_pth = "./NemoModel/checkpoint_max_mAP.pth"
        
        # IF density class run
        else:
            print("DENSITY CLASS RUN")
            path_to_pth = "./NemoModel/Nemo-DETR-dg.pth"
        
        # Run Nemo
        run_nemo(disp_attention, nmsup, iou_threshold, run_folder, path_to_pth)

        path = os.path.abspath('results.zip')
        cur_mp4_folders.clear()
        
        # Send the results to the frontend
        return send_file(path, mimetype='application/zip')
    
    # Else, we are waiting for more files to be sent
    else:
        return "none"


# Run Nemo
def run_nemo(disp_attention, nmsup, iou_threshold, images_to_run, path_to_pth):
    time.sleep(2)
    print("Running Nemo")
    subprocess.call(["python3", "./NemoModel/detr/test.py",
                     "--data_path", images_to_run,
                     "--resume", path_to_pth,
                     "--output_dir", "./ProcessedImages/",
                     "--device", "cpu", "--disp", "1", "--disp_attn", str(disp_attention),
                     "--nmsup", str(nmsup), "--iou_thresh", str(iou_threshold)])
    get_processed_images(disp_attention)
    clean_up_nemo_run(disp_attention)


def get_processed_images(disp_attention):
    """ Function to append processed Nemo files to an array. """
    files_to_send_back.clear()
    # If any video files were processed
    if len(cur_mp4_folders) > 0:
        processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
        smoke_detected_ones = []
        # For each file nemo ran on and found smoke in
        for file in os.listdir(processed_images_dir):
            x = 0
            while x < len(cur_mp4_folders):
                detected_common_name = cur_mp4_folders[x][1:] in file
                if detected_common_name:
                    smoke_detected_ones.append(file)
                x = x + 1
        # for each video file directory
        for direc in cur_mp4_folders:
            # Get a list of all of the frames of the video that will be analyzed
            before_nemo_files = os.listdir(direc)
            # For each frame from the video originally
            for file in before_nemo_files:
                # for each file from a video that had smoke detected in it
                for detectFile in smoke_detected_ones:
                    if file in detectFile:
                        os.replace(os.path.join(processed_images_dir[2:], detectFile), os.path.join(direc, file))
            create_gif(direc, disp_attention)
    print("Getting Nemo Results")
    if disp_attention == 0:
        processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
        index = 0
        for file in os.listdir(processed_images_dir):
            files_to_send_back.append(os.path.join(processed_images_dir, file))
            index = index + 1

    else:
        attention_dir = './ProcessedImages/Attn_viz'
        for file in os.listdir(attention_dir):
            files_to_send_back.append(os.path.join(attention_dir, file))

    zip_file_to_send = zipfile.ZipFile('results.zip', 'w')
    for fileName in files_to_send_back:
        zip_file_to_send.write(fileName, os.path.basename(fileName))

    zip_file_to_send.close()


def clean_up_nemo_run(disp_attention):
    """ Function to clean up files for Nemo to run again. """
    print("Cleaning up Nemo Run")
    processed_images_dir = './ProcessedImages/Inferences-ImagesToRun'
    for file in os.listdir(processed_images_dir):
        os.remove(os.path.join(processed_images_dir, file))
    images_to_run_dir = './ImagesToRun'
    for file in os.listdir(images_to_run_dir):
        os.remove(os.path.join(images_to_run_dir, file))
    if disp_attention == 1:
        attention_dir = './ProcessedImages/Attn_viz'
        for file in os.listdir(attention_dir):
            os.remove(os.path.join(attention_dir, file))
    for direc in cur_mp4_folders:
        shutil.rmtree(direc)


def get_frames(input_file, output_folder):
    """
    Input:
      inputFile - name of the input file with directory
      outputFolder - name and path of the folder to save the results
      step - time-lapse between each step (in seconds)
      count - number of screenshots
    Output:
      'count' number of screenshots that are 'step' seconds apart created from video 'inputFile' and stored
      in folder 'outputFolder'
    Function Call:
        get_frames("test.mp4", 'data')
    """
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
    video_length_seconds = length / fps
    # IF the video is longer, analyze more frames
    if video_length_seconds > 60:
        count = 45
        step = video_length_seconds / count
    else:
        count = 30
        step = video_length_seconds / count
    while True:
        ret, frame = cap.read()
        if ret:
            if current_frame > (step * fps):
                current_frame = 0

                # saving the frames (screenshots)
                name = f"{output_folder}/{os.path.splitext(os.path.basename(input_file))[0]}_{frames_captured}.png"

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


def check_file_type(filename):
    split_type = filename.split(".")
    f_type = split_type[1]
    if f_type == "mp4":
        return True
    else:
        return False


def create_gif(direc, disp_attn):
    # specify the file path of the directory containing the images
    image_directory = direc  # 'path/to/directory'

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
    # specify the name and file format of the output GIF
    output_file_name = direc + ".gif"

    # specify the duration of each frame in milliseconds
    duration = 300

    # use Pillow to save the list of images as a GIF
    # If encoder-decoder attention weights, save to different place
    if disp_attn == 1:
        image_list[0].save(os.path.join("./ProcessedImages/Attn_viz/", output_file_name), 
                           save_all=True, append_images=image_list[1:], duration=duration, loop=0)
    else:
        image_list[0].save(os.path.join("./ProcessedImages/Inferences-ImagesToRun/", output_file_name), 
                           save_all=True, append_images=image_list[1:], duration=duration, loop=0)


if __name__ == "__main__":
    app.run(debug=True)
