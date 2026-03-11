import os
import json
import time
import requests
import argparse
from pathlib import Path
from PIL import Image, ImageFilter

# AI Horde API Endpoints
API_ASYNC = "https://aihorde.net/api/v2/generate/async"
API_CHECK = "https://aihorde.net/api/v2/generate/check/{}"
API_STATUS = "https://aihorde.net/api/v2/generate/status/{}"

def submit_generation_job(prompt, width=512, height=512):
    """Submits a generation job to AI Horde and returns the job ID."""
    payload = {
        "prompt": prompt,
        "params": {
            "n": 1,
            "width": width,    # 512x512 to avoid anonymous limit on AI Horde
            "height": height,
            "steps": 30,
            "sampler_name": "k_euler_a"
        },
        # Using the anonymous API key, but requesting no NSFW
        "nsfw": False,
        "censor_nsfw": False,
        "trusted_workers": False,
    }
    
    headers = {
        "Content-Type": "application/json",
        "apikey": "0000000000" # Anonymous key
    }
    
    try:
        resp = requests.post(API_ASYNC, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        print(f"Error submitting job: {e}")
        return None

def wait_for_job(job_id, timeout_minutes=15):
    """Polls the API until the job is done."""
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_minutes * 60:
            print(f"    [Error] Job {job_id} timed out after {timeout_minutes} minutes.")
            return False
            
        try:
            check = requests.get(API_CHECK.format(job_id)).json()
            if check.get("done"):
                return True
            
            # Print status periodically
            wait_time = check.get("wait_time", "unknown")
            queue_pos = check.get("queue_position", "unknown")
            print(f"    [Status] Job in queue (Pos: {queue_pos}, Est. Wait: {wait_time}s)...", end="\r")
            
        except Exception as e:
            print(f"    [Error] Checking job status: {e}")
            
        time.sleep(10) # Poll every 10 seconds

def pad_image_to_tiktok(img_path, target_size=(1080, 1920)):
    """Pads a 512x512 image to 1080x1920 by adding a blurred background."""
    img = Image.open(img_path).convert("RGB")
    
    bg = img.resize(target_size, Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=45))
    
    target_width, target_height = target_size
    img_width, img_height = img.size
    
    # 512x512 resized proportionally to fit 1080 width
    new_width = target_width
    new_height = int(target_width * (img_height / img_width))
        
    fg = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    bg.paste(fg, (paste_x, paste_y))
    
    bg.save(img_path, "JPEG", quality=95)
    print(f"    [Post-Process] Padded {Path(img_path).name} to 1080x1920.")

def download_image(job_id, output_path):
    """Downloads the completed image from the job and pads it."""
    try:
        result = requests.get(API_STATUS.format(job_id)).json()
        generations = result.get("generations", [])
        
        if not generations:
            print(f"    [Error] No generations returned for job {job_id}")
            return False
            
        img_url = generations[0].get("img")
        if not img_url:
            print(f"    [Error] No image URL in generation data.")
            return False
            
        img_data = requests.get(img_url).content
        with open(output_path, "wb") as f:
            f.write(img_data)
            
        pad_image_to_tiktok(output_path)
        print(f"\n    [Success] Saved and formatted {output_path.name}")
        return True
    except Exception as e:
        print(f"\n    [Error] Downloading/formatting image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate images using AI Horde.")
    parser.add_argument("--prompts", type=str, default="tiktok_nano_banana_prompts.json")
    parser.add_argument("--output_dir", type=str, default="scenario_assets")
    
    args = parser.parse_args()
    
    prompts_path = Path(args.prompts)
    output_dir = Path(args.output_dir)
    
    if not prompts_path.exists():
        print(f"Error: Prompts file not found at {prompts_path}")
        return
        
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts_data = json.load(f)
        
    print(f"Found {len(prompts_data)} scenarios. Starting AI Horde generation...")
    print("Note: AI Horde is a free volunteer network. Generations may take a few minutes each.")
    
    jobs = [] # Store (job_id, output_path)
    
    # Pass 1: Queue all missing images first
    print("\n--- Phase 1: Submitting Jobs ---")
    for item in prompts_data:
        s_id = item.get("scenario_id")
        if not s_id: continue
            
        scenario_dir = output_dir / f"scenario_{s_id:02d}"
        scenario_dir.mkdir(exist_ok=True)
        
        for slide_key, filename in [("slide_1_image_prompt", "1_Hook.jpg"), 
                                  ("slide_6_image_prompt", "6_Shift.jpg")]:
            prompt = item.get(slide_key)
            out_path = scenario_dir / filename
            
            if prompt and not out_path.exists():
                # Remove confusing size hints and add a negative prompt to avoid false SFW flags
                clean_prompt = prompt.replace("1080x1920 (9:16), ", "")
                full_prompt = f"masterpiece, best quality, safe for work, {clean_prompt} ### nsfw, nude, censored, text, watermark, worst quality"
                job_id = submit_generation_job(full_prompt)
                if job_id:
                    jobs.append((job_id, out_path))
                    print(f"  Job ID: {job_id}")
                time.sleep(1) # Be gentle to the API
            elif out_path.exists():
                print(f"Skipping Scenario {s_id} - {filename} (Already exists)")

    # Pass 2: Wait for and download all jobs
    print(f"\n--- Phase 2: Waiting for {len(jobs)} Jobs ---")
    for job_id, out_path in jobs:
        print(f"\nPolling Job {job_id} for {out_path.parent.name}/{out_path.name}...")
        success = wait_for_job(job_id)
        if success:
            download_image(job_id, out_path)

    print("\nAll AI Horde generations complete!")

if __name__ == "__main__":
    main()
