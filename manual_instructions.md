# Manual Production Workflow for LeelaClue Slideshows

To build the slideshows after manually adding "Hook" and "Shift" images to the scenario folders:

## 1. Image Renaming & Scaling
Run this to rename your raw images (with timestamps) to `1_Hook.jpg` and `6_Shift.jpg` and scale them to 1080x1920.
```powershell
python scripts/auto_rename_images.py
```

## 2. Full Rendering (Phase 2)
Process the text overlays and generate the supporting slides (Question and Branding) for specific scenario IDs. Replace the IDs with the ones you want to process.
```powershell
python scripts/render_scenarios.py 8 9 10 11 12 13 14 --force
```
This command internally runs:
1.  **`overlay_text.py`**: Adds Hook text, card titles, and concluding thoughts.
2.  **`generate_question_slides.py`**: Creates **Slide 2** (The In-App Question).
3.  **`generate_emblem_slide.py`**: Creates **Slide 7** (The Branding/CTA).

## 3. Optional: Cloud Upload (Phase 3)
Push the finished assets to Google Drive:
```powershell
python scripts/upload_to_drive.py
```

---

### File Checklist (for each scenario folder):
*   `1_Hook_Text.jpg`
*   `2_Question.jpg`
*   `3_..._Text.jpg` (Card 1)
*   `4_..._Text.jpg` (Card 2)
*   `5_..._Text.jpg` (Card 3)
*   `6_Shift_Text.jpg`
*   `7_Emblem.jpg`
