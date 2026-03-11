import os
import json
import argparse
from pathlib import Path
from PIL import Image, ImageFilter

def create_padded_image(img_path, target_size=(1080, 1920)):
    """
    Resizes image to fit target size while maintaining aspect ratio.
    Adds a blurred background to fill the empty space (perfect for TikTok slides).
    """
    # Open the image and ensure it's in a standard RGB format
    img = Image.open(img_path).convert("RGB")
    
    # Create the heavily blurred background
    bg = img.resize(target_size, Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=45))
    
    # Calculate dimensions for the foreground image to fit within target_size purely
    target_width, target_height = target_size
    img_width, img_height = img.size
    
    aspect_target = target_width / target_height
    aspect_img = img_width / img_height
    
    if aspect_img > aspect_target:
        # Image is wider than target aspect ratio (fit by width)
        new_width = target_width
        new_height = int(target_width / aspect_img)
    else:
        # Image is taller than target aspect ratio (fit by height)
        new_height = target_height
        new_width = int(target_height * aspect_img)
        
    fg = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Paste the strictly-proportioned foreground image onto the blurred background
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    bg.paste(fg, (paste_x, paste_y))
    
    return bg

def main():
    parser = argparse.ArgumentParser(description="Generate scenario folders and process images for TikTok.")
    parser.add_argument("--scenarios", type=str, default="tiktok_scenarios.json", help="Path to the JSON file with the TikTok scenarios.")
    parser.add_argument("--cards", type=str, default=r"C:\GitHub\AppExperiment1\assets\cards_de.json", help="Path to the cards JSON file.")
    parser.add_argument("--assets_dir", type=str, default=r"C:\GitHub\AppExperiment1", help="Base directory containing the 'assets' folder.")
    parser.add_argument("--output_dir", type=str, default="scenario_assets", help="Directory where the scenario folders will be created.")
    
    args = parser.parse_args()
    
    # Resolving Paths
    scenarios_path = Path(args.scenarios)
    cards_path = Path(args.cards)
    assets_dir = Path(args.assets_dir)
    output_dir = Path(args.output_dir)
    
    if not scenarios_path.exists():
        print(f"Error: Scenarios file not found at {scenarios_path}")
        return
        
    if not cards_path.exists():
        print(f"Error: Cards file not found at {cards_path}")
        return
        
    # Read the data
    with open(scenarios_path, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
        
    with open(cards_path, 'r', encoding='utf-8') as f:
        cards_data = json.load(f)
        
    # Dictionary for O(1) card lookups
    card_dict = {card["id"]: card for card in cards_data}
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Found {len(scenarios)} scenarios. Starting processing...")
    
    for scenario in scenarios:
        s_id = scenario.get("id")
        if not s_id:
            continue
            
        # Create a folder for the current scenario
        scenario_dir = output_dir / f"scenario_{s_id:02d}"
        scenario_dir.mkdir(exist_ok=True)
        print(f"\n--> Processing Scenario {s_id}")
        
        # In the scenario JSON, cards are listed in 'card_assignments' [card_1, card_2, card_3]
        # In TikTok slides, cards represent Slide 3, Slide 4, and Slide 5.
        card_ids = scenario.get("card_assignments", [])
        
        for index, card_id in enumerate(card_ids):
            slide_number = index + 3 # Offset by 3 (Slide 3, 4, 5)
            
            card = card_dict.get(card_id)
            if not card:
                print(f"    [Warning] Card ID {card_id} not found in cards_de.json.")
                continue
                
            image_rel_path = card.get("image")
            if not image_rel_path:
                print(f"    [Warning] Card ID {card_id} has no image path.")
                continue
                
            # Construct the absolute path to the original image
            original_image_path = assets_dir / image_rel_path
            
            if not original_image_path.exists():
                print(f"    [Warning] Image file not found: {original_image_path}")
                continue
                
            card_title = card.get("title", f"card_{card_id}")
            # Ensure the title is safe for filenames
            card_title_safe = "".join(c for c in card_title if c.isalnum() or c in (" ", "-", "_")).strip()
            
            # Construct output filename: Slide position first (e.g. "3_Mada.jpg")
            output_filename = f"{slide_number}_{card_title_safe}.jpg"
            output_filepath = scenario_dir / output_filename
            
            try:
                # Process the image! 
                processed_img = create_padded_image(str(original_image_path))
                
                # Save as high-quality JPEG, suitable for TikTok
                processed_img.save(str(output_filepath), "JPEG", quality=95)
                print(f"    Created: {output_filepath.name}")
            except Exception as e:
                print(f"    [Error] Processing {original_image_path.name}: {e}")
                
    print(f"\nAll done! Processed jpeg assets have been saved to '{output_dir.absolute()}'")

if __name__ == "__main__":
    main()
