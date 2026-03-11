import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

def generate_and_save_image(client, prompt, output_path):
    """Generates an image using Nano Banana (Imagen 3) and saves it."""
    try:
        print(f"    -> Generating image for: {output_path.name}")
        # Note: Using imagen-4.0-fast-generate-001 which is available via your API
        result = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="9:16",
                # The model requires high quality prompts and outputs photorealistic results by default.
            )
        )
        
        # Save the generated image bytes
        if result and result.generated_images:
            image_bytes = result.generated_images[0].image.image_bytes
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            print(f"    [Success] Saved to {output_path}")
        else:
            print(f"    [Error] No image generated for {output_path.name}")
            
    except Exception as e:
        print(f"    [Error] API failed for {output_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Slide 1 and Slide 6 images using Google's Nano Banana (Imagen) API.")
    parser.add_argument("--prompts", type=str, default="tiktok_nano_banana_prompts.json", help="Path to the JSON file with the generated prompts.")
    parser.add_argument("--output_dir", type=str, default="scenario_assets", help="Directory where the scenario folders are located.")
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for API key in environment
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found.")
        print("Please create a .env file in this directory and add: GEMINI_API_KEY=your_api_key_here")
        return
        
    prompts_path = Path(args.prompts)
    output_dir = Path(args.output_dir)
    
    if not prompts_path.exists():
        print(f"Error: Prompts file not found at {prompts_path}")
        return
        
    # Read the data
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts_data = json.load(f)
        
    # Initialize the Google GenAI Client
    # It automatically picks up the GEMINI_API_KEY from your environment variables
    client = genai.Client()
    
    print(f"Found {len(prompts_data)} scenarios in prompts file. Starting image generation via API using imagen-4.0-fast-generate-001...")
    
    for item in prompts_data:
        s_id = item.get("scenario_id")
        if not s_id:
            continue
            
        scenario_dir = output_dir / f"scenario_{s_id:02d}"
        scenario_dir.mkdir(exist_ok=True)
        
        print(f"\n--> Processing Scenario {s_id}")
        
        # Slide 1 (The Hook)
        slide_1_prompt = item.get("slide_1_image_prompt")
        slide_1_path = scenario_dir / "1_Hook.jpg"
        
        if slide_1_prompt and not slide_1_path.exists(): # Skip if already generated
            generate_and_save_image(client, slide_1_prompt, slide_1_path)
        elif slide_1_path.exists():
            print(f"    [Skip] {slide_1_path.name} already exists.")
            
        # Slide 6 (The Shift)
        slide_6_prompt = item.get("slide_6_image_prompt")
        slide_6_path = scenario_dir / "6_Shift.jpg"
        
        if slide_6_prompt and not slide_6_path.exists(): # Skip if already generated
            generate_and_save_image(client, slide_6_prompt, slide_6_path)
        elif slide_6_path.exists():
            print(f"    [Skip] {slide_6_path.name} already exists.")

    print("\nAll API generations complete!")

if __name__ == "__main__":
    main()
