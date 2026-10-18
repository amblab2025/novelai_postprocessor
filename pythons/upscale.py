import asyncio
import base64
import glob
import httpx
import os
import sys
from io import BytesIO
from zipfile import ZipFile
from dotenv import load_dotenv
from PIL import Image


# 設定
SCALE = 4  # 2 or 4
UPSCALE_MODEL = "nai-diffusion-5-curated"  # 必須になったmodel指定

load_dotenv()
api_key = os.environ.get("NOVELAI_API_KEY", "")


async def upscale_images(parent_folder_path: str):
    if not api_key:
        print("NOVELAI_API_KEY is required.")
        exit(1)

    target_folder_path = os.path.join(parent_folder_path, "_01_base")
    image_path_list = glob.glob(os.path.join(target_folder_path, "*"))

    if not image_path_list:
        print(f"No images found in: {target_folder_path}")
        return

    print(f"Found {len(image_path_list)} images. Scale = {SCALE}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "*/*",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        for image_path in image_path_list:
            try:
                img_file_name = os.path.basename(image_path)
                stem = os.path.splitext(img_file_name)[0]
                output_file_name = f"{stem}_up.png"
                output_file_path = os.path.join(parent_folder_path, output_file_name)

                print(f"Processing: {img_file_name} -> {output_file_name}")

                # 画像を読み込んでbase64化
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                # 元画像のサイズ取得
                with Image.open(image_path) as img:
                    width, height = img.size

                payload = {
                    "image": image_b64,
                    "width": width,
                    "height": height,
                    "scale": SCALE,
                    "model": UPSCALE_MODEL,          # これが必須
                    "declared_blur_sigma": 0.0,     # 任意だが入れておくと安定
                }

                # リクエスト送信
                resp = await client.post(
                    "https://image.novelai.net/ai/upscale",
                    headers=headers,
                    json=payload,
                )

                if resp.status_code != 200:
                    print(f"Error {resp.status_code}: {resp.text}")
                    continue

                # レスポンスはZIP
                with ZipFile(BytesIO(resp.content)) as zf:
                    # 通常は1ファイルだけ入っている
                    name = zf.namelist()[0]
                    with zf.open(name) as img_file:
                        data = img_file.read()

                with open(output_file_path, "wb") as f:
                    f.write(data)

                print(f"Saved: {output_file_path}")

            except Exception as e:
                print(f"Error processing {image_path}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upscale.py <parent_folder_path>")
        exit(1)

    parent_folder_path = sys.argv[1]

    print("=" * 30)
    print(f"Parent folder : {parent_folder_path}")
    print(f"Scale         : {SCALE}")
    print(f"Model         : {UPSCALE_MODEL}")
    print("=" * 30)

    asyncio.run(upscale_images(parent_folder_path=parent_folder_path))
