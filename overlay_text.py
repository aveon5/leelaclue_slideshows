import os
import json
import argparse
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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
    
    # Create background and paste using RGBA throughout
    result = Image.new("RGBA", (target_width, target_height), bg_color + (255,))
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    # Paste using the alpha channel of resized_img as the mask
    result.paste(resized_img, (paste_x, paste_y), mask=resized_img)
    
    return result

def draw_text_with_shadow(draw, text_fragments, position, font, max_width, align="center", line_spacing=10, vertical_align="center", max_pixel_width=900):
    """
    Draws multi-line wrapped text with a drop shadow.
    text_fragments can be a string, or a list of tuples: (color, text)
    """
    if isinstance(text_fragments, str):
        text_fragments = [((255, 255, 255), text_fragments)]
        
    x, y = position
    
    # Pre-process the fragments into a single wrapped text structure while keeping color info
    full_text = "".join([t[1] for t in text_fragments])
    lines_text = textwrap.wrap(full_text, width=max_width)
    
    # For simplicity, if we have multiple colors, we'll draw word-by-word or use a fixed split approach
    # Let's rebuild the textwrap logic to handle colored fragments properly
    lines = []
    current_line = []
    current_line_width = 0
    
    for color, text in text_fragments:
        # Split by explicit newlines first
        newline_splits = text.split("\n")
        
        for n_idx, split_text in enumerate(newline_splits):
            if n_idx > 0:
                # Force a new line
                if current_line:
                    lines.append(current_line)
                current_line = []
                current_line_width = 0
                
            if not split_text:
                continue

            words = split_text.split(" ")
            for i, word in enumerate(words):
                if not word and i != len(words)-1: # preserve spaces
                    word = " "
                
                # Add trailing space back if it was split
                display_word = word + (" " if i < len(words) - 1 else "")
                word_w = draw.textlength(display_word, font=font)
                
                # Pixel width check for wrapping
                if current_line_width + word_w > max_pixel_width and current_line:
                    lines.append(current_line)
                    current_line = []
                    current_line_width = 0
                    
                current_line.append((color, display_word))
                current_line_width += word_w
            
    if current_line:
        lines.append(current_line)
        
    # Calculate total height
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
    
    if vertical_align == "top":
        current_y = y
    else:
        current_y = y - (total_height // 2)
        
    y_start = current_y
    
    for line_fragments in lines:
        # Calculate line width to center
        line_w = sum([draw.textlength(t[1], font=font) for t in line_fragments])
        
        if align == "center":
            current_x = x - (line_w // 2)
        elif align == "left":
            current_x = x
        else:
            current_x = x
            
        for color, word in line_fragments:
            # Draw drop shadow
            shadow_offset = 6
            draw.text((current_x + shadow_offset, current_y + shadow_offset), word, font=font, fill=(0, 0, 0, 200))
            # Draw text with stroke outline
            draw.text((current_x, current_y), word, font=font, fill=color, stroke_width=3, stroke_fill=(0, 0, 0, 255))
            
            current_x += draw.textlength(word, font=font)
            
        current_y += line_height + line_spacing

    return y_start, y_start + total_height

def process_image(input_path, output_path, text, font_path="arial.ttf", font_size=80, text_y=960, top_text=None, top_text_y=None, line_spacing=10, bg_start_from_top=False, vertical_align="center", top_vertical_align="center"):
    """Adds text overlay to an image and saves it."""
    try:
        if not input_path.exists():
            print(f"    [Warning] Input image not found: {input_path}")
            return False

        # Load and verify size
        img = Image.open(input_path).convert("RGBA")
        img = ensure_1080x1920(img)

        # Draw overlay
        # We use RGBA drawing surface for potential semi-transparent background boxes if needed later
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"    [Warning] Font '{font_path}' not found. Falling back to default.")
            font = ImageFont.load_default()

        # Define safe area for text to avoid TikTok UI on right edge (250px)
        safe_left_margin = 80
        safe_right_margin = 250
        max_px_width = img.width - safe_left_margin - safe_right_margin
        safe_center_x = safe_left_margin + (max_px_width // 2)

        # Draw the main text
        main_y_start, main_y_end = draw_text_with_shadow(
            draw=draw, 
            text_fragments=text, 
            position=(safe_left_margin, text_y), 
            font=font, 
            max_width=25, # rough chars per line for 80pt font on 1080px width
            line_spacing=line_spacing,
            vertical_align=vertical_align,
            max_pixel_width=max_px_width,
            align="left"
        )
        
        top_y_start, top_y_end = None, None
        # Draw top text if provided
        if top_text:
            top_font = ImageFont.truetype(font_path, font_size + 10) # slightly larger for title
            # If top_text_y is None, default to something reasonable
            top_y = top_text_y if top_text_y is not None else int(img.height * 0.15)
            
            top_y_start, top_y_end = draw_text_with_shadow(
                draw=draw,
                text_fragments=top_text,
                position=(safe_left_margin, top_y),
                font=top_font,
                max_width=25,
                line_spacing=10,
                vertical_align=top_vertical_align,
                max_pixel_width=max_px_width,
                align="left"
            )

        # Draw the background layer using the actual calculated heights
        bg_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        bg_draw = ImageDraw.Draw(bg_layer)

        # Padding around text
        rect_y1 = max(0, main_y_start - 200)
        if bg_start_from_top:
            rect_y1 = 0
            
        rect_y2 = main_y_end + 200
        bg_draw.rectangle([0, rect_y1, img.width, rect_y2], fill=(0, 0, 0, 100))

        # Composite and save
        out = Image.alpha_composite(img, bg_layer)
        out = Image.alpha_composite(out, txt_layer)
        out = out.convert("RGB")
        out.save(output_path, "JPEG", quality=95)
        print(f"    [Success] Created {output_path.name}")
        return True

    except Exception as e:
        print(f"    [Error] Processing {input_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Add text overlays to TikTok scenario images.")
    parser.add_argument("--scenarios", type=str, default="tiktok_scenarios.json")
    parser.add_argument("--input_dir", type=str, default="scenario_assets")
    parser.add_argument("--font", type=str, default="arial.ttf", help="Path to a TrueType font file.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing _Text.jpg images.")
    parser.add_argument("--scenario_ids", type=int, nargs="+", help="Specific scenario IDs to process (e.g. 1 2 3).")
    
    args = parser.parse_args()
    
    scenarios_path = Path(args.scenarios)
    input_dir = Path(args.input_dir)
    
    if not scenarios_path.exists():
        print(f"Error: Scenarios file not found at {scenarios_path}")
        return
        
    with open(scenarios_path, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
        
    print(f"Found {len(scenarios)} scenarios. Adding text overlays...")
    
    for scenario in scenarios:
        s_id = scenario.get("id")
        if not s_id: continue
        
        if args.scenario_ids and s_id not in args.scenario_ids:
            continue
        
        scenario_dir = input_dir / f"scenario_{s_id:02d}"
        if not scenario_dir.exists():
            print(f"Skipping Scenario {s_id}: Directory not found.")
            continue
            
        print(f"\n--> Processing Scenario {s_id}")
        
        # --- Slide 1: Hook ---
        hook_text_raw = scenario.get("slide_1_hook", "")
        
        # Split text by colon to color intro gold and quote white
        if ":" in hook_text_raw:
            intro, quote = hook_text_raw.split(":", 1)
            hook_text = [
                ((255, 215, 0), intro + ":"), # Gold color
                ((255, 255, 255), quote)      # White color
            ]
        else:
            hook_text = hook_text_raw
            
        in_img = scenario_dir / "1_Hook.jpg"
        out_img = scenario_dir / "1_Hook_Text.jpg" # Create copy
        if in_img.exists() and (args.force or not out_img.exists()):
            process_image(in_img, out_img, hook_text, font_path=args.font, font_size=70, text_y=200, vertical_align="top", bg_start_from_top=True, line_spacing=40)
        elif out_img.exists():
            print(f"    [Skip] {out_img.name} already exists.")



        # --- Slides 3, 4, 5: Cards ---
        texts = [
            scenario.get("slide_3_standort", {}).get("text", ""),
            scenario.get("slide_4_hindernis", {}).get("text", ""),
            scenario.get("slide_5_ressource", {}).get("text", "")
        ]
        
        for idx, text in enumerate(texts):
            slide_num = idx + 3
            # Find the card image dynamically (e.g. 3_Mada.jpg)
            card_files = list(scenario_dir.glob(f"{slide_num}_*.jpg"))
            card_files = [f for f in card_files if not f.name.endswith("_Text.jpg")]
            
            if card_files:
                in_card = card_files[0]
                out_card = scenario_dir / f"{in_card.stem}_Text.jpg"
                
                # Format card text (e.g. "Standort (Mada)" at top, rest in white in middle)
                if ":" in text:
                    prefix, description = text.split(":", 1)
                    top_text = [((255, 215, 0), prefix)] # Gold color, NO colon
                    formatted_card_text = [
                        ((255, 255, 255), description.strip()) # White color
                    ]
                    
                    if args.force or not out_card.exists():
                        process_image(in_card, out_card, formatted_card_text, font_path=args.font, font_size=60, text_y=960, top_text=top_text, top_text_y=200, vertical_align="center", top_vertical_align="top", line_spacing=25)
                    else:
                        print(f"    [Skip] {out_card.name} already exists.")
                else:
                    formatted_card_text = text
                    if args.force or not out_card.exists():
                        # Put card text near the center
                        process_image(in_card, out_card, formatted_card_text, font_path=args.font, font_size=60, text_y=960, vertical_align="center", line_spacing=25)
                    else:
                        print(f"    [Skip] {out_card.name} already exists.")
            else:
                print(f"    [Warning] Card image for slide {slide_num} not found.")

        # --- Slide 6: Shift ---
        shift_text = scenario.get("slide_6_shift", "")
        in_img6 = scenario_dir / "6_Shift.jpg"
        out_img6 = scenario_dir / "6_Shift_Text.jpg"
        if in_img6.exists() and (args.force or not out_img6.exists()):
             process_image(in_img6, out_img6, shift_text, font_path=args.font, font_size=70, text_y=960, vertical_align="center")
        elif out_img6.exists():
            print(f"    [Skip] {out_img6.name} already exists.")

    print("\nAll text overlays added successfully!")

if __name__ == "__main__":
    main()
