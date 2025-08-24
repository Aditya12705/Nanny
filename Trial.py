import streamlit as st
import pandas as pd
import os
import tempfile
import gdown
from PIL import Image, ImageDraw, ImageFont
from rembg import remove
import textwrap
import zipfile

# ========================
# Function to generate nanny profile image
# ========================
def generate_nanny_profile(row, template_path, output_dir):
    age = str(row['Age'])
    location = row['Location']
    languages = row['Languages']
    education = row['Education']
    experience = str(row['Experience'])
    salary = row['Salary']
    availability = row['Availability']
    drive_link = row['DriveLink']

    with tempfile.TemporaryDirectory() as temp_dir:
        # Download image from Google Drive folder link
        try:
            folder_id = drive_link.split('/')[-1].split('?')[0]
            gdown.download_folder(id=folder_id, output=temp_dir, quiet=True, use_cookies=False)
        except Exception as e:
            st.error(f"❌ Error downloading from Google Drive: {e}")
            return None

        image_path = None
        for file in os.listdir(temp_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(temp_dir, file)
                break

        if image_path is None:
            st.warning(f"No image found for {row}")
            return None

        # Remove background
        with Image.open(image_path) as img:
            img = img.convert('RGBA')
            img_no_bg = remove(img)
            image_path = os.path.join(temp_dir, 'Trial.png')
            img_no_bg.save(image_path)

        name = os.path.splitext(os.path.basename(image_path))[0].replace('_', ' ').title()

        # Load template (always use local Blank.png)
        template = Image.open(template_path).convert('RGBA')
        draw = ImageDraw.Draw(template)

        # Load fonts
        try:
            title_font = ImageFont.truetype("arialbd.ttf", 55)
            subtitle_font = ImageFont.truetype("arialbd.ttf", 30)
            desc_font = ImageFont.truetype("arial.ttf", 24)
            value_font = ImageFont.truetype("arialbd.ttf", 22)
        except:
            title_font = subtitle_font = desc_font = value_font = ImageFont.load_default()

        blue_color = (25, 25, 112)
        black_color = (0, 0, 0)

        # Title + subtitle
        draw.text((template.width // 2, 250), f"MEET {name.upper()}!", fill=blue_color, font=title_font, anchor="mm")
        draw.text((template.width // 2, 310), "YOUR NEW NANNY", fill=blue_color, font=subtitle_font, anchor="mm")

        # Description
        description = (
            f"Compassionate, dedicated, and experienced, {name} brings "
            f"{experience} years of caregiving expertise, including past work "
            f"experience with families/elderly care. Fluent in {languages}, "
            f"she combines professional skill with genuine empathy, and is ready "
            f"to serve families in {location}."
        )
        wrapped_desc = textwrap.fill(description, width=70)
        draw.multiline_text((template.width // 2, 400), wrapped_desc, fill=black_color, font=desc_font, anchor="mm", spacing=6)

        # Value positions
        value_positions = {
            'age': (230, 527),
            'location': (285, 587),
            'languages': (317, 641),
            'education': (303, 706),
            'experience': (315, 765),
            'salary': (265, 824),
            'availability': (320, 888)
        }

        values = [age, location, languages, education, f"{experience} years", salary, availability]
        for (key, pos), value in zip(value_positions.items(), values):
            draw.text(pos, value, fill=black_color, font=value_font)

        # Paste nanny image
        try:
            nanny_img = Image.open(image_path).convert('RGBA').resize((400, 600), Image.LANCZOS)
            template_width, template_height = template.size
            x = template_width - 370
            y = template_height - 500
            template.paste(nanny_img, (x, y), nanny_img)
        except Exception as e:
            st.error(f"Error pasting nanny image: {e}")
            return None

        # Save
        output_path = os.path.join(output_dir, f"{name.replace(' ', '_')}.png")
        template.save(output_path, "PNG")
        return output_path


# ========================
# STREAMLIT APP
# ========================
st.title("👩‍🍼 Nanny Profile Generator")

uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])

# Template is already included in project folder
TEMPLATE_PATH = "Blank.png"

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Loaded {len(df)} nanny records")
    except Exception as e:
        st.error(f"❌ Error reading Excel: {e}")
        st.stop()

    if st.button("Generate Profiles"):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(tmpdir, exist_ok=True)
            output_files = []

            for index, row in df.iterrows():
                out_path = generate_nanny_profile(row, TEMPLATE_PATH, tmpdir)
                if out_path:
                    output_files.append(out_path)
                    st.image(out_path, caption=f"Profile {index+1}", use_container_width=True)

            # Zip all outputs
            if output_files:
                zip_path = os.path.join(tmpdir, "profiles.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for file in output_files:
                        zipf.write(file, os.path.basename(file))

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "📥 Download All Profiles (ZIP)",
                        f,
                        file_name="nanny_profiles.zip",
                        mime="application/zip"
                    )
