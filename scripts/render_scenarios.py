import os
import argparse
import subprocess
import sys
from pathlib import Path

# Get the directory where THIS script is located
SCRIPT_DIR = Path(__file__).resolve().parent

def run_script(script_name, args_list):
    """Runs a python script with the given arguments."""
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args_list
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: {script_name} failed with return code {result.returncode}")
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="End-to-End Scenario Renderer (Phase 2)")
    parser.add_argument("ids", type=int, nargs="*", help="Specific scenario IDs to process (e.g. 11 12 13). If empty, processes all.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing assets.")
    
    args = parser.parse_args()
    
    scenario_args = []
    if args.ids:
        scenario_args = ["--scenario_ids"] + [str(i) for i in args.ids]
    
    force_arg = ["--force"] if args.force else []

    print(f"Starting Phase 2 Rendering for scenarios: {args.ids if args.ids else 'ALL'}")

    # 1. Overlay Text (Slides 1, 3, 4, 5, 6)
    run_script("overlay_text.py", scenario_args + force_arg)

    # 2. Question Slide (Slide 2)
    run_script("generate_question_slides.py", scenario_args + force_arg)

    # 3. Finish Slide (Slide 7)
    run_script("generate_emblem_slide.py", scenario_args)

    print("\nPhase 2 Complete!")

if __name__ == "__main__":
    main()
