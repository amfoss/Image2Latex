import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont
from time import perf_counter
from dotenv import load_dotenv 

load_dotenv()
# --- Server Configuration ---
BASE_URL = os.getenv("BASE_URL","")
UPLOAD_URL = os.getenv("UPLOAD_URL","")
RESULT_URL_BASE = os.getenv("RESULT_URL_BASE","")
TEST_IMAGE_NAME = "image.png"

def create_test_image():
    """Creates a simple PNG image with text for testing."""
    print(f"Creating '{TEST_IMAGE_NAME}'...")
    try:
        # Create a white 300x100 image
        img = Image.new('RGB', (300, 100), color = 'white')
        d = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default
        try:
            # You may need to change this path for your WSL environment
            # Or just let it fail and use the default font
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            print("Arial font not found, using default font.")
            font = ImageFont.load_default()
            
        # Draw text in black
        d.text((10,10), "E = mc^2", fill=(0,0,0), font=font)
        img.save(TEST_IMAGE_NAME)
        print(f"Successfully created '{TEST_IMAGE_NAME}'.")
        return True
    except Exception as e:
        print(f"Error creating test image: {e}")
        print("Please ensure 'Pillow' is installed: pip install Pillow")
        return False

def run_test():
    """Runs the full upload and poll test."""
    
    if not os.path.exists(TEST_IMAGE_NAME):
        if not create_test_image():
            return

    # 1. --- Upload the image ---
    print(f"Testing UPLOAD to {UPLOAD_URL}...")
    try:
        with open(TEST_IMAGE_NAME, 'rb') as f:
            files = {'file': (TEST_IMAGE_NAME, f, 'image/png')}
            response = requests.post(UPLOAD_URL, files=files, timeout=30)
        
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        print(data)
        if data.get('s') != 'ok' or not data.get('id'):
            print(f"Upload failed: Server returned an invalid response: {data}")
            return

        task_id = data['id']
        print(f"Upload SUCCESS. Task ID: {task_id}")

    except requests.exceptions.HTTPError as e:
        print(f"Upload FAILED. Status Code: {e.response.status_code}")
        print(f"Server says: {e.response.text}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Upload FAILED. Could not connect to server: {e}")
        return

    # 2. --- Poll for the result ---
    result_url = f"{RESULT_URL_BASE}{task_id}"
    print(f"Polling for result at {result_url}...")
    
    for i in range(120): # Poll for 120 seconds max
        try:
            time.sleep(1)
            response = requests.get(result_url, timeout=5)
            
            if response.status_code == 404:
                print("Polling... (Got 404, which is expected for a pending job)")
                continue

            response.raise_for_status()
            data = response.json()
            
            print(f"Poll {i+1}: Server status is '{data.get('status')}'")

            if data.get('status') == 'done':
                print("\n--- TEST SUCCESS ---")
                print(f"Final LaTeX Result: {data.get('result')}")
                print("----------------------")
                return
            
            if data.get('status') == 'error':
                print("\n--- TEST FAILED (Worker Error) ---")
                print(f"Worker returned an error: {data.get('e')}")
                print("----------------------------------")
                return

        except requests.exceptions.HTTPError as e:
            print(f"Polling FAILED. Status Code: {e.response.status_code}")
            print(f"Server says: {e.response.text}")
            return
        except requests.exceptions.RequestException as e:
            print(f"Polling FAILED. Could not connect to server: {e}")
            return
            
    print("\n--- TEST FAILED (Timeout) ---")
    print("Gave up after 120 seconds. The result was still pending.")
    print("-----------------------------")


if __name__ == "__main__":
    from threading import Thread
    t = [Thread(target=run_test) for i in range(int(input("Enter requests:")))]
    start = perf_counter()
    for i in t:
        i.start()
    for i in t:
        i.join()
        
    print("\n\n",perf_counter()-start," seconds taken.")