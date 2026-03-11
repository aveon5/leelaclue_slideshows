import json
import argparse
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def fit_text_in_box(draw, text, box, font_path, color=(240, 230, 255), max_font_size=80):
    """
    Finds the maximum font size that fits the text inside the given box 
    (left, top, right, bottom) and draws it perfectly centered, up to a limit.
    """
    left, top, right, bottom = box
    box_w = right - left
    box_h = bottom - top
    
    # Try different font sizes to maximize fit
    best_font_size = 10
    best_lines = []
    
    # max font size to keep it elegant
    for size in range(20, max_font_size + 1):
        try:
            font = ImageFont.truetype(font_path, size)
        except IOError:
            font = ImageFont.load_default()
            
        # We need to wrap the text. We guess chars per line based on typical char width.
        # A more robust way is to wrap word by word and check width
        words = text.split(" ")
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if draw.textlength(test_line, font=font) <= box_w:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
            
        # Check total height
        if not lines:
            continue
            
        line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
        line_spacing = int(size * 0.3)
        total_h = len(lines) * line_height + (len(lines) - 1) * line_spacing
        
        if total_h <= box_h:
            best_font_size = size
            best_lines = lines
        else:
            break # Previous size was the best
            
    # Now draw with the best found size
    try:
        font = ImageFont.truetype(font_path, best_font_size)
    except IOError:
        font = ImageFont.load_default()
        
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    line_spacing = int(best_font_size * 0.3)
    total_h = len(best_lines) * line_height + (len(best_lines) - 1) * line_spacing
    
    # Center vertically in the box
    current_y = top + (box_h - total_h) // 2
    
    for line in best_lines:
        line_w = draw.textlength(line, font=font)
        # Center horizontally in the box
        current_x = left + (box_w - line_w) // 2
        
        # Draw soft shadow for readability
        shadow_offset = 3
        draw.text((current_x + shadow_offset, current_y + shadow_offset), line, font=font, fill=(0, 0, 0, 150))
        # Draw main text, "lila-white"
        draw.text((current_x, current_y), line, font=font, fill=color)
        
        current_y += line_height + line_spacing

def main():
    parser = argparse.ArgumentParser(description="Generate Question Slides using empty.jpg")
    parser.add_argument("--scenarios", type=str, default="tiktok_scenarios.json")
    parser.add_argument("--input_dir", type=str, default="scenario_assets")
    parser.add_argument("--output_dir", type=str, default="scenario_assets_text")
    parser.add_argument("--base_img", type=str, default="empty.jpg")
    parser.add_argument("--font", type=str, default=r"C:\GitHub\AppExperiment1\assets\fonts\Philosopher-Bold.ttf")
    parser.add_argument("--force", action="store_true")
    
    args = parser.parse_args()
    
    scenarios_path = Path(args.scenarios)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    base_img_path = Path(args.base_img)
    
    if not scenarios_path.exists():
        print(f"Error: Scenarios file not found at {scenarios_path}")
        return
        
    if not base_img_path.exists():
        print(f"Error: Base image not found at {base_img_path}")
        return
        
    with open(scenarios_path, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
        
    # Prepare the base 1080x1920 image by center cropping the empty.jpg
    base_img = Image.open(base_img_path).convert("RGB")
    target_w, target_h = 1080, 1920
    
    if base_img.size != (target_w, target_h):
        # Center crop from height
        width, height = base_img.size
        # Assuming width is already 1080 and height is ~2424
        # Calculate scaling to fit width
        scale_ratio = target_w / width
        new_h = int(height * scale_ratio)
        resized_base = base_img.resize((target_w, new_h), Image.Resampling.LANCZOS)
        
        # Crop from center
        y_offset = (new_h - target_h) // 2
        base_cropped = resized_base.crop((0, y_offset, target_w, y_offset + target_h))
    else:
        base_cropped = base_img

    print(f"Found {len(scenarios)} scenarios. Generating Question slides...")
    
    for scenario in scenarios:
        s_id = scenario.get("id")
        if not s_id: continue
        
        scenario_dir = input_dir / f"scenario_{s_id:02d}"
        if not scenario_dir.exists():
            continue
            
        # Create corresponding output directory
        out_scenario_dir = output_dir / f"scenario_{s_id:02d}"
        if not out_scenario_dir.exists():
            out_scenario_dir.mkdir(parents=True, exist_ok=True)
            
        out_img = out_scenario_dir / "2_Question_Text.jpg"
        
        if out_img.exists() and not args.force:
            print(f"    [Skip] Scenario {s_id} Question image already exists.")
            continue
            
        question_text = scenario.get("slide_2_question", "")
        if not question_text:
            continue
            
        # Copy the base cropped image to draw on
        img_to_draw = base_cropped.copy()
        draw = ImageDraw.Draw(img_to_draw)
        
        # The coordinates of the "red box" on the 1080x1920 cropped image
        text_box = (160, 500, 920, 1350)
        
        # More pronounced Lila color
        lila = (220, 160, 255)
        white = (255, 255, 255)
        
        # Draw Title at the top
        title_text = "Also habe ich meine LeelaClue gefragt..."
        try:
            title_font = ImageFont.truetype(args.font, 75)
        except IOError:
            title_font = ImageFont.load_default()
            
        title_lines = textwrap.wrap(title_text, width=20)
        title_y = 180  # Shifted to exactly 180px from top
        
        line_height = title_font.getbbox("A")[3] - title_font.getbbox("A")[1]
        line_spacing = 20
        total_title_h = len(title_lines) * line_height + (len(title_lines) - 1) * line_spacing
        
        # Draw dark background box for title
        # Snapped to the absolute top of the image (y=0) and extending down past the title
        draw.rectangle([0, 0, 1080, title_y + total_title_h + 40], fill=(0, 0, 0, 100))
        
        current_y = title_y
        for line in title_lines:
            line_w = draw.textlength(line, font=title_font)
            line_x = 1080 // 2 - line_w // 2
            
            # Shadow
            draw.text((line_x + 3, current_y + 3), line, font=title_font, fill=(0, 0, 0, 150))
            # Text
            draw.text((line_x, current_y), line, font=title_font, fill=white)
            
            current_y += line_height + line_spacing
        
        # Draw main question
        fit_text_in_box(draw, question_text, text_box, args.font, color=lila, max_font_size=65)
        
        # Save as JPEG
        img_to_draw.save(out_img, "JPEG", quality=95)
        print(f"    [Success] Generated {out_img.name} for Scenario {s_id}")

    print("\nAll Question slides generated!")

if __name__ == "__main__":
    main()
