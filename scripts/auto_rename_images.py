import os
import re
import argparse
from pathlib import Path
from PIL import Image

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def ensure_1080x1920(img, bg_color=(0, 0, 0)):
    """Ensures the image is exactly 1080x1920 by scaling and padding if necessary."""
    target_width, target_height = 1080, 1920
    if img.size == (target_width, target_height):
        return img

    # Resize proportionally to fit within 1080x1920
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider, scale to target width
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller, scale to target height
        new_height = target_height
        new_width = int(target_height * img_ratio)

    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create background and paste
    result = Image.new("RGB", (target_width, target_height), bg_color)
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    result.paste(resized_img, (paste_x, paste_y))
    
    return result

def extract_timestamp(filename):
    """Extracts a 12-digit timestamp from the filename."""
    match = re.search(r"(\d{12})", filename)
    if match:
        return match.group(1)
    return ""

def main():
    parser = argparse.ArgumentParser(description="Auto-rename and scale Hook (Slide 1) and Shift (Slide 6) images.")
    parser.add_argument("--dir", type=str, default=str(PROJECT_ROOT / "scenario_assets"), help="Directory containing scenario folders.")
    parser.add_argument("--force", action="store_true", help="Process even if 1_Hook.jpg or 6_Shift.jpg already exist.")
    
    args = parser.parse_args()
    base_dir = Path(args.dir)
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} not found.")
        return

    scenario_folders = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("scenario_")])
    
    print(f"Scanning {len(scenario_folders)} scenario folders...")

    for folder in scenario_folders:
        # Collect candidates
        candidates = []
        for f in folder.iterdir():
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                # Exclude already processed/numbered files
                if re.match(r"^[1-7]_", f.name):
                    continue
                
                timestamp = extract_timestamp(f.name)
                if timestamp:
                    candidates.append((timestamp, f))
        
        if not candidates:
            continue
            
        print(f"\n--> Checking {folder.name}")
        
        # Check if Slide 1 or 6 already exist
        hook_exists = (folder / "1_Hook.jpg").exists()
        shift_exists = (folder / "6_Shift.jpg").exists()
        
        if (hook_exists or shift_exists) and not args.force:
            print(f"    [Skip] Scenario {folder.name} already has Hook or Shift images. Use --force to override.")
            continue

        if len(candidates) != 2:
            print(f"    [Error] Expected exactly 2 new images with timestamps, found {len(candidates)}: {[c[1].name for c in candidates]}")
            continue
            
        # Sort by timestamp (alphabetically works for YYYYMMDDHHMM)
        # Fallback to filename if timestamps are identical
        candidates.sort(key=lambda x: (x[0], x[1].name))
        
        hook_source = candidates[0][1]
        shift_source = candidates[1][1]
        
        for source, target_name in [(hook_source, "1_Hook.jpg"), (shift_source, "6_Shift.jpg")]:
            try:
                img = Image.open(source).convert("RGB")
                img_scaled = ensure_1080x1920(img)
                
                target_path = folder / target_name
                img_scaled.save(target_path, "JPEG", quality=95)
                print(f"    [Success] {source.name} -> {target_name}")
                
                # Delete original
                os.remove(source)
                print(f"    [Clean] Removed original: {source.name}")
            except Exception as e:
                print(f"    [Error] Processing {source.name}: {e}")

    print("\nRenaming and scaling complete!")

if __name__ == "__main__":
    main()
