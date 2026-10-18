import glob
import os
import sys
from PIL import Image


def jpeg_convert(parent_folder_path):    
    target_pattern = os.path.join(parent_folder_path, "*.png")
    png_file_path_list = glob.glob(target_pattern)
    for image_path in png_file_path_list:
        im = Image.open(image_path)
        img = im.convert("RGB")
        
        # a/b/c.png -> a
        dirname = os.path.dirname(image_path)
        parent_dirname = os.path.dirname(dirname)

        # a/b/c.png -> c.png
        basename = os.path.basename(image_path)

        # c.png -> c.jpeg
        jpeg_filename = basename.replace(".png", ".jpeg")

        # c.jpeg -> a/c.jpeg
        file_path = os.path.join(parent_dirname, jpeg_filename)

        print(file_path)
        img.save(file_path)

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <parent_folder_path>")
        exit(1)

    parent_folder_path = sys.argv[1]

    print("=" * 30)
    print(f"Parent folder : {parent_folder_path}")
    print("=" * 30)

    jpeg_convert(parent_folder_path=parent_folder_path)
