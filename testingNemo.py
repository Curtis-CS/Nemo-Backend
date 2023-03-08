import subprocess
print("In Testing Nemo")
subprocess.Popen(["python3", "./NemoModel/detr/test.py", 
        "--data_path", "./NemoModel/Images/ImagesToRun/", 
        "--resume", "./NemoModel/Nemo-DETR-dg.pth", 
        "--output_dir", "./NemoModel/Images/ProcessedImages/", 
        "--device" , "cpu", "--disp" ,"1"]).wait()