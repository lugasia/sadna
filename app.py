import streamlit as st
import os
import qrcode
from PIL import Image
import re
from io import BytesIO
import base64
import shutil
import uuid
import json
from pillow_heif import register_heif_opener

# Register HEIF/HEIC support
register_heif_opener()

# Set page config
st.set_page_config(
    page_title="סדנת יצירה 2025",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS for mobile-friendly view
st.markdown("""
<style>
    /* Mobile-friendly container */
    .mobile-container {
        max-width: 100%;
        padding: 10px;
        margin: 0 auto;
    }
    
    /* Image styling */
    .stImage {
        margin: 30px 0;
        transition: all 0.3s ease;
    }
    
    .stImage > img {
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    /* Title styling */
    h1 {
        text-align: center;
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
        font-size: 2em;
        margin: 20px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        position: sticky;
        top: 0;
        background: white;
        padding: 10px;
        z-index: 1000;
    }
    
    /* Button styling */
    .stButton button {
        background: #2c3e50;
        color: white;
        border-radius: 25px;
        padding: 12px 24px;
        border: none;
        transition: all 0.3s ease;
        font-family: 'Arial', sans-serif;
        font-size: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        margin: 5px;
        width: 100%;
    }
    
    .stButton button:hover {
        background: #34495e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Edit mode controls */
    .edit-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 10px 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .mobile-container {
            padding: 5px;
        }
        
        h1 {
            font-size: 1.5em;
        }
        
        .stButton button {
            padding: 10px 20px;
            font-size: 14px;
        }
        
        .stImage {
            margin: 20px 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []
if 'upload_dir' not in st.session_state:
    st.session_state.upload_dir = 'album'
if 'album_id' not in st.session_state:
    st.session_state.album_id = 'default'
if 'image_rotations' not in st.session_state:
    st.session_state.image_rotations = {}
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'edit'

# Get album_id from URL parameters
params = st.query_params
if 'album_id' in params:
    st.session_state.album_id = params['album_id']
    st.session_state.view_mode = 'view'

# Create upload directory if it doesn't exist
os.makedirs(st.session_state.upload_dir, exist_ok=True)

# Path for storing rotation data
rotation_file = os.path.join(st.session_state.upload_dir, 'rotations.json')

def load_rotation_data():
    """Load saved rotation data for images."""
    if os.path.exists(rotation_file):
        with open(rotation_file, 'r') as f:
            return json.load(f)
    return {}

def save_rotation_data():
    """Save rotation data for images."""
    with open(rotation_file, 'w') as f:
        json.dump(st.session_state.image_rotations, f)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to the album directory."""
    file_path = os.path.join(st.session_state.upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def load_images_from_album():
    """Load images from the album directory."""
    image_files = []
    for file in os.listdir(st.session_state.upload_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic')):
            image_files.append(os.path.join(st.session_state.upload_dir, file))
    return sorted(image_files)

def get_share_url():
    """Generate shareable URL for the album."""
    base_url = "https://lgvqgdba26dczmfvmh9qmd.streamlit.app"
    return f"{base_url}/?album_id={st.session_state.album_id}"

# Load saved rotation data
st.session_state.image_rotations = load_rotation_data()

# Main app
st.title("סדנת יצירה 2025")

# Toggle view mode if in edit mode
if st.session_state.view_mode == 'edit':
    if st.button("תצוגה מקדימה"):
        st.session_state.view_mode = 'view'
        st.rerun()

# Show edit interface only in edit mode
if st.session_state.view_mode == 'edit':
    st.subheader("העלאת תמונות")
    uploaded_files = st.file_uploader("בחר תמונות להעלאה", type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'heic'], accept_multiple_files=True)

    if uploaded_files:
        if st.button("שמור תמונות"):
            with st.spinner("שומר תמונות..."):
                for uploaded_file in uploaded_files:
                    file_path = save_uploaded_file(uploaded_file)
                    if file_path not in st.session_state.image_rotations:
                        st.session_state.image_rotations[file_path] = 0
                save_rotation_data()
                st.session_state.images = load_images_from_album()
                st.success(f"הועלו {len(uploaded_files)} תמונות בהצלחה!")

# Display images
st.session_state.images = load_images_from_album()
if st.session_state.images:
    # Create a container for all images
    with st.container():
        for img_path in st.session_state.images:
            try:
                current_rotation = st.session_state.image_rotations.get(img_path, 0)
                image = Image.open(img_path)
                if current_rotation:
                    image = image.rotate(-current_rotation, expand=True)
                
                # Calculate image dimensions for mobile
                img_width, img_height = image.size
                aspect_ratio = img_height / img_width
                
                # Adjust image size for mobile viewing
                display_width = min(800, img_width)
                display_height = int(display_width * aspect_ratio)
                
                # Resize image while maintaining aspect ratio
                image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Display image with padding
                st.image(image, use_container_width=True)
                
                # Show rotation controls in edit mode
                if st.session_state.view_mode == 'edit':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("↺ סובב שמאלה", key=f"left_{img_path}"):
                            st.session_state.image_rotations[img_path] = (current_rotation - 90) % 360
                            save_rotation_data()
                            st.rerun()
                    with col2:
                        if st.button("↻ סובב ימינה", key=f"right_{img_path}"):
                            st.session_state.image_rotations[img_path] = (current_rotation + 90) % 360
                            save_rotation_data()
                            st.rerun()
            except Exception as e:
                st.error(f"שגיאה בטעינת התמונה: {str(e)}")
    
    # Show sharing options only in edit mode
    if st.session_state.view_mode == 'edit':
        st.markdown("---")
        st.subheader("שיתוף אלבום")
        share_url = get_share_url()
        st.write("קישור לשיתוף:", share_url)
        qr_code = qrcode.make(share_url)
        qr_bytes = BytesIO()
        qr_code.save(qr_bytes, format='PNG')
        qr_bytes = qr_bytes.getvalue()
        st.image(qr_bytes, width=200)
        
        st.download_button(
            label="הורד קוד QR",
            data=qr_bytes,
            file_name="album_qr.png",
            mime="image/png"
        )
        
        st.markdown("---")
        if st.button("מחק אלבום", type="primary"):
            shutil.rmtree(st.session_state.upload_dir)
            st.session_state.images = []
            st.rerun()
else:
    if st.session_state.view_mode == 'edit':
        st.info("העלה תמונות כדי להתחיל!")
    else:
        st.info("האלבום ריק.") 