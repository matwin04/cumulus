import customtkinter as ctk
import requests
import webbrowser
import os
import zipfile
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import threading
# Immich API Config
API_KEY = '1iJIyS4JsjvOZMKXR3nOGIFuKovjK2YOvza4XgDm8'
BASE_URL = 'https://immich.mattwiner.org/api'
UPLOAD_DIR = './upload'
DEVICE_ID = 'python-uploader'

# ========== Helper Functions ==========

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        print("Created Upload Directory")
        output_box.insert("end", "Created Upload Directory: ./upload\n")

def unzip_files():
    for root, _, files in os.walk(UPLOAD_DIR):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(root)
                    output_box.insert("end", f"Unzipped: {zip_path}\n")
                    os.remove(zip_path)
                except zipfile.BadZipFile:
                    output_box.insert("end", f"[ERROR] Bad zip file: {zip_path}\n")

def get_exif_datetime(filepath):
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S").isoformat()
            elif tag == "DateTime":
                return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception as e:
        output_box.insert("end", f"[EXIF ERROR] {filepath}: {e}\n")
    return None

def get_file_time(filepath):
    try:
        ts = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(ts).isoformat()
    except Exception as e:
        output_box.insert("end", f"[TIME ERROR] {filepath}: {e}\n")
        return datetime.datetime.now().isoformat()

def upload_photo(filepath):
    filename = os.path.basename(filepath)
    exif_time = get_exif_datetime(filepath)
    fallback_time = get_file_time(filepath)

    try:
        with open(filepath, "rb") as f:
            files = {
                "assetData": (filename, f, "application/octet-stream")
            }
            data = {
                "deviceAssetId": f'{filename}-{os.path.getmtime(filepath)}',
                "deviceId": DEVICE_ID,
                "fileCreatedAt": exif_time or fallback_time,
                "fileModifiedAt": exif_time or fallback_time,
                "filename": filename,
                "isFavorite": "false",
                "visibility": "timeline"
            }
            headers = {
                "x-api-key": API_KEY,
                "Accept": "application/json"
            }

            response = requests.post(f"{BASE_URL}/assets", headers=headers, data=data, files=files)
            status_code = response.status_code
            status = response.json().get("status", "no status")
            output_box.insert("end", f"Uploaded {filename} → {status_code} ({status})\n")

            if status_code in [200, 201] and status in ["created", "duplicate"]:
                os.remove(filepath)
                output_box.insert("end", f"Deleted local file: {filepath}\n\n")
    except Exception as e:
        output_box.insert("end", f"[UPLOAD ERROR] {filepath}: {e}\n")

def upload_all_photos():
    ensure_upload_folder()
    unzip_files()

    filepaths = []
    for root, _, files in os.walk(UPLOAD_DIR):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif")):
                filepaths.append(os.path.join(root, file))

    if not filepaths:
        output_box.insert("end", "No photos found in ./upload\n")
        return

    for filepath in filepaths:
        upload_photo(filepath)

# ========== Immich Statistics ==========
def send_request():
    try:
        response = requests.get(
            url=f"{BASE_URL}/assets/statistics",
            headers={"x-api-key": API_KEY},
        )
        output_box.delete("0.0", "end")
        output_box.insert("end", f"Status: {response.status_code}\n")
        output_box.insert("end", response.text)
    except requests.exceptions.RequestException as e:
        output_box.insert("end", f"Request failed: {e}")

# ========== Takeout Part Downloader ==========
def download_zip():
    os.makedirs("takeout", exist_ok=True)

    try:
        part_num = int(part_entry.get())
    except ValueError:
        output_box.delete("0.0", "end")
        output_box.insert("end", "Invalid part number. Enter a number like 0, 20, 40...\n")
        return

    url = (
        "https://takeout.google.com/takeout/download?"
        "j=79789aa9-5f68-4d39-918f-9cc5a0c79618&"
        f"i={part_num}&"
        "user=110451928625470528578&"
        "rapt=AEjHL4MrpvH4XwUmhhLk2rzLfqO90alYu4GApLbM5ywRCrQXOuVmleS_TFzq2FQYNaiPtgCwfP4HS9Fpea9WQNAucEy0hEsI-EEZJIc5dQ7iPe9PRSBB43Q"
    )

    webbrowser.get("firefox").open(url)
    output_box.delete("0.0", "end")
    output_box.insert("end", f"Firefox opened with part {part_num}.\n")
    output_box.insert("end", "Please move the downloaded ZIP into the 'takeout' folder manually.\n")

# ========== UI Setup ==========
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Immich Uploader + Takeout Helper")
app.geometry("640x580")

btn1 = ctk.CTkButton(app, text="Get Immich Stats", command=send_request)
btn1.pack(pady=10)

part_label = ctk.CTkLabel(app, text="Enter Takeout Part Number:")
part_label.pack()

part_entry = ctk.CTkEntry(app, width=100)
part_entry.insert(0, "0")
part_entry.pack(pady=5)

btn2 = ctk.CTkButton(app, text="Download Takeout Part", command=download_zip)
btn2.pack(pady=10)

btn3 = ctk.CTkButton(app, text="Upload All Photos", command=lambda: threading.Thread(target=upload_all_photos, daemon=True).start())
btn3.pack(pady=10)

output_box = ctk.CTkTextbox(app, width=600, height=300)
output_box.pack(padx=10, pady=10)

app.mainloop()