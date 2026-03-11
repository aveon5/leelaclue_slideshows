from PIL import Image, ImageDraw, ImageFont

def trace_wrap(text_fragments):
    img = Image.new("RGB", (1080, 1920), (0,0,0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 60)
    
    max_pixel_width = 900
    
    lines = []
    current_line = []
    current_line_width = 0
    
    for color, text in text_fragments:
        newline_splits = text.split("\n")
        
        for n_idx, split_text in enumerate(newline_splits):
            if n_idx > 0:
                if current_line:
                    lines.append(current_line)
                current_line = []
                current_line_width = 0
                
            if not split_text:
                continue

            words = split_text.split(" ")
            for i, word in enumerate(words):
                if not word and i != len(words)-1:
                    word = " "
                
                display_word = word + (" " if i < len(words) - 1 else "")
                word_w = draw.textlength(display_word, font=font)
                
                if current_line_width + word_w > max_pixel_width and current_line:
                    lines.append(current_line)
                    current_line = []
                    current_line_width = 0
                    
                current_line.append((color, display_word))
                current_line_width += word_w
                
    for i, l in enumerate(lines):
        print(f"Line {i}: {l}")

    x = 1080 // 2
    y = 1920 // 2
    align = "center"
    
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    total_height = len(lines) * line_height + (len(lines) - 1) * 10
    
    current_y = y - (total_height // 2)
    
    for line_fragments in lines:
        line_w = sum([draw.textlength(t[1], font=font) for t in line_fragments])
        
        if align == "center":
            current_x = x - (line_w // 2)
        elif align == "left":
            current_x = x
        else:
            current_x = x
            
        for color, word in line_fragments:
            print(f"Drawing '{word}' at x={current_x:.1f}, y={current_y:.1f}")
            shadow_offset = 3
            draw.text((current_x + shadow_offset, current_y + shadow_offset), word, font=font, fill=(50, 50, 50, 200))
            draw.text((current_x, current_y), word, font=font, fill=color)
            current_x += draw.textlength(word, font=font)
            
        current_y += line_height + 10
        
    img.save("test_wrap_output.jpg")

text = "Ressource (Tapa): Befreie dich von Erwartungen, die nicht dir gehören. Schaffe Raum für deinen wahren Weg."
prefix, description = text.split(":", 1)
formatted_card_text = [
    ((255, 215, 0), prefix + ":\n"),
    ((255, 255, 255), description.strip())
]

trace_wrap(formatted_card_text)
