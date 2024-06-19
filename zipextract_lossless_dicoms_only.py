import os
import pydicom
from zipfile import ZipFile
from pathlib import Path
from contextlib import closing

def find_zip_files(path):
    zip_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.zip'):
                zip_files.append(os.path.join(root, file))

    return zip_files


def temp_unzip(zip, temp_out_path):

    # make zip object for current file
    with closing(ZipFile(zip, 'r')) as zObject: 

        f_count = 0
        for f in zObject.infolist():

            if f.filename.endswith('.dcm'):
                zObject.extract(f, path=temp_out_path)

            f_count += 1

    zObject.close() 

    return f_count


def prune_lossy_dcms(path):

    removed_dcm_count = 0

    for root, dirs, files in os.walk(path):
        for file in files:

            if file.endswith('.dcm'):

                #dicom = pydicom.filereader.read_file_meta_info(os.path.join(root, file)) # doesn't load the tag we need :(
                dicom = pydicom.filereader.dcmread(os.path.join(root, file))
                #print(dicom.get('LossyImageCompression','00'))

                try:
                    #print(dicom[0x0028, 0x2110].value)
                    if dicom.get('LossyImageCompression','00') == '01':
                        file_path = os.path.join(path, os.path.basename(dicom.filename))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            removed_dcm_count += 1
                except KeyError:
                    continue

    return removed_dcm_count


def save_dcms_from_temp_and_tidy(out_path, temp_out_path):

    for root, dirs, files in os.walk(temp_out_path):
        for file in files:
            if file.endswith('.dcm'):
                old_file = os.path.join(temp_out_path, file)
                new_file = os.path.join(out_path, file)
                os.rename(old_file, new_file)

    try:
        os.rmdir(temp_out_path) # try to delete the temp path
        print("Directory '% s' has been removed successfully" % temp_out_path)
    except OSError as error:
        print(error)
        print("Directory '% s' can not be removed - are there files remaining?" % temp_out_path) # this suggests there are unexpected files, so let's not burn down the world

    return True
    

if __name__ == "__main__":
    in_path = input("Please enter the path to the directory containing the Zip files:\n")
    in_path = os.path.normpath(in_path)

    zip_files = find_zip_files(in_path)

    zip_count = 0
    for zip in zip_files:

        print(f"\nProcessing {zip}...")

        out_path = os.path.join(in_path, Path(zip).stem)
        print(f"Output path: {out_path}")
        temp_out_path = os.path.join(out_path, "temp")
        print(f"Temp output path: {temp_out_path}")
        
        print(f"Extracted {temp_unzip(zip, temp_out_path)} files from this Zip.")
        
        print(f"Pruned {prune_lossy_dcms(temp_out_path)} lossy files.")

        save_dcms_from_temp_and_tidy(out_path, temp_out_path)

        zip_count += 1

    print(f"Extracted and cleaned lossy files from {zip_count} Zips.\n")

