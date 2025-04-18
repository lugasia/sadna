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

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'images_per_page' not in st.session_state:
    st.session_state.images_per_page = 4
if 'upload_dir' not in st.session_state:
    st.session_state.upload_dir = 'album'
if 'album_id' not in st.session_state:
    st.session_state.album_id = 'default'
if 'image_rotations' not in st.session_state:
    st.session_state.image_rotations = {}
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'edit'
if 'transition' not in st.session_state:
    st.session_state.transition = False
if 'port' not in st.session_state:
    # Get the port from the environment or use default
    st.session_state.port = int(os.environ.get('PORT', 8501))

# Get album_id from URL parameters
params = st.query_params
if 'album_id' in params:
    st.session_state.album_id = params['album_id']
    st.session_state.view_mode = 'view'

# Create upload directory if it doesn't exist
os.makedirs(st.session_state.upload_dir, exist_ok=True)

# No need for album-specific directory since we're using a fixed directory
album_dir = st.session_state.upload_dir

# Path for storing rotation data
rotation_file = os.path.join(album_dir, 'rotations.json')

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
    file_path = os.path.join(album_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def load_images_from_album():
    """Load images from the album directory."""
    image_files = []
    for file in os.listdir(album_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic')):
            image_files.append(os.path.join(album_dir, file))
    return sorted(image_files)

def generate_qr_code(url):
    """Generate QR code for the album URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def pil_to_bytes(pil_image):
    """Convert PIL Image to bytes for Streamlit."""
    img_byte_arr = BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

def get_share_url():
    """Generate shareable URL for the album."""
    # Use the Streamlit Cloud URL if available, otherwise use localhost
    base_url = "https://lgvqgdba26dczmfvmh9qmd.streamlit.app"
    return f"{base_url}/?album_id={st.session_state.album_id}"

# Load saved rotation data
st.session_state.image_rotations = load_rotation_data()

# Custom CSS for book-like appearance
st.markdown("""
<style>
    /* Book container */
    .book-container {
        background: linear-gradient(to right, #d4d4d4, #f0f0f0, #d4d4d4);
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(0,0,0,0.4);
        margin: 20px auto;
        max-width: 1200px;
        position: relative;
        transform-style: preserve-3d;
        perspective: 2000px;
    }
    
    /* Page appearance */
    .stImage {
        position: relative;
        margin: 10px;
        transition: all 0.5s ease;
    }
    
    .stImage > img {
        background: white;
        padding: 10px;
        border: 1px solid #ddd;
        box-shadow: 2px 4px 8px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
        border-radius: 5px;
    }
    
    .stImage > img:hover {
        transform: scale(1.02);
        box-shadow: 4px 8px 16px rgba(0,0,0,0.3);
    }
    
    /* Navigation buttons */
    .stButton button {
        background: #2c3e50;
        color: white;
        border-radius: 25px;
        padding: 12px 24px;
        border: none;
        transition: all 0.3s ease;
        font-family: 'Georgia', serif;
        font-size: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .stButton button:hover {
        background: #34495e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Page turn animation */
    @keyframes pageFlip {
        0% { 
            transform: rotateY(0deg); 
            box-shadow: -5px 5px 5px rgba(0,0,0,0.2);
        }
        100% { 
            transform: rotateY(-180deg);
            box-shadow: 5px 5px 5px rgba(0,0,0,0.2);
        }
    }
    
    .page-flip {
        animation: pageFlip 1s ease-in-out;
    }
    
    /* Album title */
    h1 {
        text-align: center;
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
        margin-bottom: 30px;
        font-size: 2.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Page numbers */
    .page-number {
        text-align: center;
        font-family: 'Georgia', serif;
        font-size: 1.2em;
        color: #2c3e50;
        margin: 10px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Center content */
    .block-container {
        max-width: 1400px;
        padding: 2rem;
        margin: 0 auto;
    }
    
    /* Book spine effect */
    .book-spine {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 40px;
        background: linear-gradient(to right, #2c3e50, #34495e);
        border-radius: 15px 0 0 15px;
    }
</style>
""", unsafe_allow_html=True)

# Main app
if st.session_state.view_mode == 'view':
    st.title("סדנת יצירה 2025")
else:
    st.title("סדנת יצירה 2025")

# Toggle view mode if in edit mode
if st.session_state.view_mode == 'edit':
    if st.button("Preview Album View"):
        st.session_state.view_mode = 'view'
        st.rerun()

# Show edit interface only in edit mode
if st.session_state.view_mode == 'edit':
    st.subheader("Upload Images")
    uploaded_files = st.file_uploader("Choose images to upload", type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'heic'], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Save Images"):
            with st.spinner("Saving images..."):
                for uploaded_file in uploaded_files:
                    file_path = save_uploaded_file(uploaded_file)
                    if file_path not in st.session_state.image_rotations:
                        st.session_state.image_rotations[file_path] = 0
                save_rotation_data()
                st.session_state.images = load_images_from_album()
                st.session_state.current_page = 0
                st.success(f"Successfully uploaded {len(uploaded_files)} images!")

# Display images in a book-like layout
st.session_state.images = load_images_from_album()
if st.session_state.images:
    total_pages = (len(st.session_state.images) - 1) // st.session_state.images_per_page + 1
    
    start_idx = st.session_state.current_page * st.session_state.images_per_page
    end_idx = min(start_idx + st.session_state.images_per_page, len(st.session_state.images))
    
    # Book container
    with st.container():
        st.markdown('<div class="book-container"><div class="book-spine"></div>', unsafe_allow_html=True)
        
        # Display images in a 2x2 grid
        for row in range(2):
            cols = st.columns(2)
            for col in range(2):
                idx = start_idx + row * 2 + col
                if idx < end_idx:
                    with cols[col]:
                        try:
                            img_path = st.session_state.images[idx]
                            current_rotation = st.session_state.image_rotations.get(img_path, 0)
                            image = Image.open(img_path)
                            if current_rotation:
                                image = image.rotate(-current_rotation, expand=True)
                            
                            st.image(image, use_container_width=True)
                            
                            if st.session_state.view_mode == 'edit':
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(f"↺", key=f"left_{idx}"):
                                        st.session_state.image_rotations[img_path] = (current_rotation - 90) % 360
                                        save_rotation_data()
                                        st.rerun()
                                with col2:
                                    if st.button(f"↻", key=f"right_{idx}"):
                                        st.session_state.image_rotations[img_path] = (current_rotation + 90) % 360
                                        save_rotation_data()
                                        st.rerun()
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
        
        # Page numbers at the bottom
        st.markdown(f"<div class='page-number'>עמודים {start_idx + 1}-{end_idx} מתוך {len(st.session_state.images)}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation controls
        st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 3, 2])
        with col1:
            if st.session_state.current_page > 0:
                if st.button("◀️ העמוד הקודם"):
                    st.session_state.transition = True
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<h3 style='text-align: center; font-family: Arial, sans-serif; direction: rtl;'>עמוד {st.session_state.current_page + 1} מתוך {total_pages}</h3>", unsafe_allow_html=True)
        
        with col3:
            if st.session_state.current_page < total_pages - 1:
                if st.button("העמוד הבא ▶️"):
                    st.session_state.transition = True
                    st.session_state.current_page += 1
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show sharing options only in edit mode
    if st.session_state.view_mode == 'edit':
        st.markdown("---")
        st.subheader("Share Album")
        share_url = get_share_url()
        st.write("Share this link:", share_url)
        qr_code = generate_qr_code(share_url)
        qr_bytes = pil_to_bytes(qr_code)
        st.image(qr_bytes, width=200)
        
        st.download_button(
            label="Download QR Code",
            data=qr_bytes,
            file_name="album_qr.png",
            mime="image/png"
        )
        
        st.markdown("---")
        if st.button("Delete Album", type="primary"):
            shutil.rmtree(album_dir)
            st.session_state.images = []
            st.session_state.current_page = 0
            st.rerun()
else:
    if st.session_state.view_mode == 'edit':
        st.info("Upload some images to get started!")
    else:
        st.info("This album is empty.") 