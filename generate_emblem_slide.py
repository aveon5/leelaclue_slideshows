from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main():
    emblem_path = Path("emblem2.png")
    if not emblem_path.exists():
        print(f"Error: {emblem_path} not found.")
        return
        
    print(f"Loading {emblem_path}...")
    img = Image.open(emblem_path).convert("RGBA")
    
    # Target size
    target_width, target_height = 1080, 1920
    
    # Calculate scaling to cover the area (no black bars)
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        # Image is relatively wider, scale to match height, crop width
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is relatively taller, scale to match width, crop height
        new_width = target_width
        new_height = int(target_width / img_ratio)
        
    print(f"Resizing from {img.width}x{img.height} to {new_width}x{new_height}...")
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate crop coordinates for the center
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    cropped_img = resized_img.crop((left, top, right, bottom))
    
    # Create background (in case of transparency, though it's likely a solid screenshot)
    bg_color = (0, 0, 0)
    result = Image.new("RGB", (target_width, target_height), bg_color)
    
    # Paste using alpha channel as mask if it has one
    if cropped_img.mode == 'RGBA':
        result.paste(cropped_img, (0, 0), mask=cropped_img)
    else:
        result.paste(cropped_img, (0, 0))
    
    
    final_img = result.copy()
    draw = ImageDraw.Draw(final_img)
    
    # Text to add
    cta_text_1 = "Probiere die App noch heute aus!"
    
    font_path = r"C:\GitHub\AppExperiment1\assets\fonts\Philosopher-Bold.ttf"
    try:
        font_large = ImageFont.truetype(font_path, 60)
    except IOError:
        font_large = ImageFont.load_default()
        
    # Position under "LeelaClue" top text (approx Y=150-180 for standard app bar on 1920)
    current_y = 300
    
    # Draw line 1 centered
    w1 = draw.textlength(cta_text_1, font=font_large)
    x1 = 1080 // 2 - w1 // 2
    
    # Add shadow for readability without background box
    draw.text((x1 + 3, current_y + 3), cta_text_1, font=font_large, fill=(0, 0, 0, 150))
    # Draw main text in Gold
    draw.text((x1, current_y), cta_text_1, font=font_large, fill=(255, 215, 0))
    
    input_dir = Path("scenario_assets")
    
    if not input_dir.exists():
        print("Error: scenario_assets directory not found.")
        return
        
    # Find all scenario folders
    scenario_folders = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith("scenario_")]
    
    print(f"Found {len(scenario_folders)} scenario folders.")
    
    for folder in scenario_folders:
        out_path = folder / "7_Emblem.jpg"
        final_img.save(out_path, "JPEG", quality=95)
        print(f"  [Success] Saved {out_path}")
        
    print("Done generating Emblem slides!")

if __name__ == "__main__":
    main()
