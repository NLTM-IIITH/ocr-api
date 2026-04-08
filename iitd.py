# import base64
# import json
# import asyncio
# import aiohttp
# from dataclasses import dataclass
# from typing import List, Optional, Dict
# from PIL import Image
# import io

# # -------------------------------
# # Convert Image File -> Base64
# # -------------------------------
# def image_to_base64(image_path: str) -> Optional[str]:
#     try:
#         with open(image_path, "rb") as image_file:
#             return base64.b64encode(image_file.read()).decode("utf-8")
#     except Exception as e:
#         print(f"Error reading {image_path}: {e}")
#         return None


# # -------------------------------
# # Normalize Base64 Image -> RGB JPEG Base64
# # (helps when image is RGBA/PNG/greyscale, etc.)
# # -------------------------------
# def normalize_base64_to_rgb(base64_string: str) -> Optional[str]:
#     try:
#         image_bytes = base64.b64decode(base64_string)
#         img = Image.open(io.BytesIO(image_bytes))

#         # Debug: show original mode (L, RGB, RGBA, etc.)
#         print("Original Mode:", img.mode)

#         img = img.convert("RGB")
#         buffer = io.BytesIO()
#         img.save(buffer, format="JPEG")

#         fixed_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
#         return fixed_base64
#     except Exception as e:
#         print("Error normalizing base64:", e)
#         return None


# # -------------------------------
# # OCR Response Model
# # -------------------------------
# @dataclass
# class OCRImageResponse:
#     text: str
#     meta: dict


# # -------------------------------
# # DO NOT MODIFY (Your Async Function)
# # -------------------------------
# async def call_new_iitd_api(request) -> List[OCRImageResponse]:
#     url = "https://lipikar.cse.iitd.ac.in/api-direct/recognition/infer"
#     if request.language == "me":
#         request.language = "mni"

#     payload = json.dumps(
#         {
#             "modality": "Printed+SceneText",
#             "language": "Combined Indic",
#             "version": "2",
#             "imageContent": request.imageContent,
#         }
#     )

#     headers = {"Content-Type": "application/json"}

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, data=payload, headers=headers) as response:
#             print("Status Code:", response.status)
#             raw = await response.text()
#             print("Raw Response:", raw)

#             try:
#                 content = await response.json()
#                 ret: List[OCRImageResponse] = []
#                 for i in content.get("output", []):
#                     try:
#                         t = i["source"][0]
#                     except Exception:
#                         t = ""
#                     ret.append(OCRImageResponse(text=t, meta={}))
#                 return ret
#             except Exception as e:
#                 print(e)
#                 raise Exception(f"Error while calling IITD API: {e}")


# # -------------------------------
# # Request Object
# # -------------------------------
# class DummyRequest:
#     def __init__(self, language: str, imageContent: List[str]):
#         self.language = language
#         self.imageContent = imageContent


# # -------------------------------
# # Languages to try (common Indian language codes)
# # -------------------------------
# SUPPORTED_LANGUAGES = [
#     'en',  # english
#     'hi',  # hindi
#     'mr',  # marathi
#     'ta',  # tamil
#     'te',  # telugu
#     'kn',  # kannada
#     'gu',  # gujarati
#     'pa',  # punjabi
#     'bn',  # bengali
#     'ml',  # malayalam
#     'asa',  # assamese
#     'ori',  # oriya
#     'mni',  # manipuri
#     'ur',  # urdu
#     'me',
#     # extra languages
#     'brx',  # Bodo
#     'doi',  # Dogri
#     'ks',  # Kashmiri
#     'kok',  # Konkani
#     'mai',  # Maithili
#     'ne',  # Nepali
#     'sa',  # Sanskrit
#     'sat',  # Santali
#     'sd',  # Sindhi
# ]


# # -------------------------------
# # MAIN
# # -------------------------------
# async def main():
#     # Put your image paths here
#     image_paths = [
#         "/home/ocr/experiment/images/page_6_word_23.jpg",
#     ]

#     # Convert all images to base64 + normalize to RGB JPEG base64
#     base64_images: List[str] = []
#     for path in image_paths:
#         encoded = image_to_base64(path)
#         if not encoded:
#             continue

#         encoded_fixed = normalize_base64_to_rgb(encoded)
#         if not encoded_fixed:
#             continue

#         base64_images.append(encoded_fixed)

#     print(f"\nTotal Images Converted & Normalized: {len(base64_images)}")
#     if not base64_images:
#         print("No valid images found.")
#         return

#     # Run OCR for every language and print results
#     for lang in SUPPORTED_LANGUAGES:
#         print("\n" + "=" * 70)
#         print(f"Running OCR for language: {lang}")
#         print("=" * 70)

#         request = DummyRequest(language=lang, imageContent=base64_images)

#         try:
#             results = await call_new_iitd_api(request)
#         except Exception as e:
#             print(f"OCR failed for {lang}: {e}")
#             continue

#         print("\nFinal OCR Results:\n")
#         for idx, result in enumerate(results, start=1):
#             print(f"Image {idx}:")
#             print("Text:", result.text)
#             print("-" * 40)


# if __name__ == "__main__":
#     asyncio.run(main())
import base64
import aiohttp
import asyncio


async def call_new_iitd_ci_api():
    url = "https://lipikar.cse.iitd.ac.in/api-direct/recognition/infer"

    image_path = "/home/ocr/experiment/images/page_6_word_7.jpg"

    print("Reading image...")

    try:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("Image read error:", e)
        return

    payload = {
        "modality": "Printed+SceneText",
        "language": "combined_indic",
        "version": "2",
        "imageContent": [image_base64]
    }

    print("Calling IITD API...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:

                print("Status:", response.status)

                raw_text = await response.text()
                print("Raw response:", raw_text)

                data = await response.json()

                result = []
                for item in data.get("output", []):
                    text = item.get("source", [""])[0]
                    result.append(text)

                return result

    except Exception as e:
        print("API error:", e)
        return


async def main():
    result = await call_new_iitd_ci_api()

    print("\nFinal Output:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())