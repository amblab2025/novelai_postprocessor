import base64
from dotenv import load_dotenv
import glob
import json
import math
import os 
from PIL import Image
import requests
import sys


# .env
load_dotenv()
api_key = os.environ.get("NOVELAI_API_KEY", "")

# API endpoint
ENDPOINT_URL = "https://image.novelai.net/ai/generate-image-stream"

# target folder
TARGET_FOLDER_NAME = "_00_base"
OUTPUT_FOLDER_NAME = "_01_base"

# NovelAI Model
# NOVEL_AI_MODEL = "nai-diffusion-5-full"
NOVEL_AI_MODEL_V5 = "nai-diffusion-5-full-medium"  # 節約モード
NOVEL_AI_MODEL_V4_5 = "nai-diffusion-4-5-full"  # V4.5
STEPS_V5 = 14
SCALE_V5 = 6.5
STEPS_V4_5 = 28
SCALE_V4_5 = 6

# Scaling factor
SCALING_FACTOR = 1.5

# Enhacnement strength: default = 0.2
ENHANCE_STRENGTH = 0.2

def size_definer(width, height, upscale_factor):
    """
    upscaling
    """
    return upscale_to_nearest_64(width, upscale_factor), upscale_to_nearest_64(height, upscale_factor)


def upscale_to_nearest_64(original_size, upscale_factor):
    """
    upscale_factor倍した後に、64で割り切れる最も近い値に変換する
    
    Args:
        original_size (int): 元の幅または高さ (例: 1216)
    
    Returns:
        int: 64の倍数で最も近い値
    """
    scaled = original_size * upscale_factor
    # 64の倍数に丸める（最も近い値）
    nearest = math.ceil(scaled / 64) * 64
    return int(nearest)


def main_with_token(parent_folder_path, output_folder_path, model_type_param, enhancement_strength=ENHANCE_STRENGTH):
    """
    generating image via API KEY
    """
    if api_key == "":
        print("NOVELAI_API_KEY is required.")
        exit(1)

    target_folder_path = os.path.join(parent_folder_path, TARGET_FOLDER_NAME)
    print(target_folder_path)

    # obtaining images in target folder
    image_path_list = glob.glob(os.path.join(target_folder_path, "*"))
    print(image_path_list)
    for image_path in image_path_list:
        img = Image.open(image_path)
        img_info = img.info
        img_file_name = os.path.basename(image_path)

        # output definition
        output_file_name = img_file_name.replace(".png", "") + "_up.png"
        output_file_path = os.path.join(output_folder_path, output_file_name)

        comment = json.loads(img_info.get("Comment", "{}"))
        prompt = comment.get("prompt", "")
        uc = comment.get("uc", "")
        steps = STEPS_V5 if model_type_param == "V5" else STEPS_V4_5
        scale = SCALE_V5 if model_type_param == "V5" else SCALE_V4_5 
        #steps = comment.get("steps", 28)
        #scale = comment.get("scale", 5.0)

        width, height = size_definer(comment.get("width", 0), comment.get("height", 0), upscale_factor=SCALING_FACTOR)
        if width <= 0 or height <= 0:
            print(f"image file {image_path} has 0 width/height: ({width}, {height})")
            continue

        char_captions = comment.get("v4_prompt", {}).get("caption", {}).get("char_captions", [])

        #
        # generating image
        #
        url = ENDPOINT_URL
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # common parameters (to be updated)
        parameters = {
            "width": width,
            "height": height,
            "scale": scale,
            "sampler": "k_euler_ancestral",
            "steps": steps,
            "n_samples": 1,
            "strength": enhancement_strength,
            "noise": 0,
            "autoSmea": False,
            "dynamic_thresholding": False,
            "controlnet_strength": 1,
            "legacy": False,
            "add_original_image": True,
            "noise_schedule": "karras",
            "legacy_v3_extend": False,
            "use_coords": False,
            "legacy_uc": False,
            "normalize_reference_strength_multiple": True,
            "inpaintImg2ImgStrength": 1,
            "image": "image",
            "characterPrompts": [],
            "color_correct": False,
            "v4_prompt": {
                "caption": {
                    "base_caption": prompt,
                    "char_captions": char_captions
                },
                "use_coords": False,
                "use_order": True
            },
            "v4_negative_prompt": {
                "caption": {
                    "base_caption": uc,
                    "char_captions": []
                },
                "legacy_uc": False
            },
            "negative_prompt": uc,
            "deliberate_euler_ancestral_bug": False,
            "prefer_brownian": True,
            "image_format": "png",
        }

        if model_type_param == "V5":
            parameters.update({
                "params_version": 4,
                "ucPresetId": "heavy",
                "qualityPresetId": "standard",
                "tag_hint_qt": 1,
                "tag_hint_uc_preset": 2,
                "straight_alpha": True,
                "upscaled_enhance": True,
            })
        else:
            parameters.update({
                "params_version": 3,
                "ucPreset": 0,  # heavy
                "qualityToggle": True,
                "cfg_rescale": 0,
            })

        request_json = {
            "model": NOVEL_AI_MODEL_V5 if model_type_param == "V5" else NOVEL_AI_MODEL_V4_5,
            "input": prompt,
            "action": "img2img",
            "parameters": parameters,
            "use_new_shared_trial": True
        }

        files = {
            # 元画像
            "image": (
                img_file_name,
                open(image_path, "rb"),
                "image/png"
            ),

            # request JSON
            "request": (
                None,
                json.dumps(request_json),
                "application/json"
            )
        }

        response = requests.post(
            url,
            headers=headers,
            files=files
        )
        print("status:", response.status_code)
        print("content-type:", response.headers.get("content-type"))

        for raw_line in response.iter_lines():
            if not raw_line:
                continue

            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue

            data = json.loads(line[6:])
            event_type = data.get("event_type")

            if event_type == "intermediate":
                print(
                    f"step={data.get('step_ix')} "
                    f"sigma={data.get('sigma')}"
                )
            elif event_type == "final":
                # 画像ファイル保存
                image_b64 = data["image"]
                image_bytes = base64.b64decode(image_b64)

                with open(output_file_path, "wb") as f:
                    f.write(image_bytes)

                print(f"saved: {output_file_path}")
                break


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("(1) folder path (2) V4.5/V5 parameter are required.")
        exit(1)
    
    parent_folder_path = sys.argv[1]
    model_type_param = sys.argv[2]
    output_folder_path = os.path.join(parent_folder_path, OUTPUT_FOLDER_NAME)
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path, exist_ok=True)

    print(f"model you choice: {model_type_param}")

    # parameter
    while True:
        value = input("Strength of enhancement (default=0.2 for Level1, 0.4 for Lavel2). Please input 'q' if you want to cancel: ")
        if value == "q":
            exit(1)

        try:
            enhancement_strength = float(value)
            break
        except ValueError:
            print("Pleast input float value.")

    print("=" * 30)
    print(f"Enhancement: {enhancement_strength}")

    #
    # Step1: Generating Single Image
    #
    print("=" * 30)
    generated_image_file_path = main_with_token(
        parent_folder_path=parent_folder_path, 
        output_folder_path=output_folder_path, 
        model_type_param=model_type_param,
        enhancement_strength=enhancement_strength)
    print("End.")
