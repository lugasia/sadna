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
    /* Header styling */
    header {
        visibility: hidden;
    }

    /* Title styling */
    .main-title {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
        z-index: 1000;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
    }

    /* Spacer for fixed header */
    .header-spacer {
        margin-top: 4rem;
    }

    /* Grid layout for images */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        padding: 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* In view mode, show one image per row */
    .view-mode .image-grid {
        grid-template-columns: 1fr;
        max-width: 800px;
    }

    .image-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        aspect-ratio: 1;
        display: flex;
        flex-direction: column;
    }

    .image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 5px;
        flex: 1;
    }

    /* Control buttons container */
    .control-buttons {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        justify-content: center;
    }

    .control-buttons button {
        flex: 1;
        padding: 0.5rem;
        border: none;
        border-radius: 5px;
        background: #2c3e50;
        color: white;
        cursor: pointer;
        max-width: 60px;
    }

    .delete-button {
        background: #e74c3c !important;
    }

    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .image-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .view-mode .image-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 480px) {
        .image-grid {
            grid-template-columns: 1fr;
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
    if os.path.exists(rotation_file):
        with open(rotation_file, 'r') as f:
            return json.load(f)
    return {}

def save_rotation_data():
    with open(rotation_file, 'w') as f:
        json.dump(st.session_state.image_rotations, f)

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(st.session_state.upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def load_images_from_album():
    image_files = []
    for file in os.listdir(st.session_state.upload_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic')):
            image_files.append(os.path.join(st.session_state.upload_dir, file))
    return sorted(image_files)

def get_share_url():
    base_url = "https://lgvqgdba26dczmfvmh9qmd.streamlit.app"
    return f"{base_url}/?album_id={st.session_state.album_id}"

def delete_image(img_path):
    try:
        os.remove(img_path)
        if img_path in st.session_state.image_rotations:
            del st.session_state.image_rotations[img_path]
            save_rotation_data()
        return True
    except Exception as e:
        st.error(f"שגיאה במחיקת התמונה: {str(e)}")
        return False

# Load saved rotation data
st.session_state.image_rotations = load_rotation_data()

# Fixed header
st.markdown('<div class="main-title">סדנת יצירה 2025</div>', unsafe_allow_html=True)
st.markdown('<div class="header-spacer"></div>', unsafe_allow_html=True)

# Show admin controls at the top if in edit mode
if st.session_state.view_mode == 'edit':
    # Sharing options at the top
    st.subheader("שיתוף אלבום")
    share_url = get_share_url()
    st.write("קישור לשיתוף:", share_url)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # Generate QR code
        qr = qrcode.make(share_url)
        qr_bytes = BytesIO()
        qr.save(qr_bytes, format='PNG')
        qr_bytes = qr_bytes.getvalue()
        st.image(qr_bytes, width=200)
    
    with col2:
        st.download_button(
            label="הורד קוד QR",
            data=qr_bytes,
            file_name="album_qr.png",
            mime="image/png"
        )
        if st.button("תצוגה מקדימה"):
            st.session_state.view_mode = 'view'
            st.rerun()
    
    st.markdown("---")
    
    # Upload interface
    st.subheader("העלאת תמונות")
    uploaded_files = st.file_uploader(
        "בחר תמונות להעלאה",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'heic'],
        accept_multiple_files=True
    )
    
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
    
    st.markdown("---")

# Display images in grid
st.session_state.images = load_images_from_album()
if st.session_state.images:
    # Add view-mode class if needed
    grid_class = "image-grid" if st.session_state.view_mode == 'edit' else "image-grid view-mode"
    
    # Start grid container
    st.markdown(f'<div class="{grid_class}">', unsafe_allow_html=True)
    
    for img_path in st.session_state.images:
        try:
            current_rotation = st.session_state.image_rotations.get(img_path, 0)
            image = Image.open(img_path)
            if current_rotation:
                image = image.rotate(-current_rotation, expand=True)
            
            # Calculate dimensions
            if st.session_state.view_mode == 'edit':
                # In edit mode, resize to thumbnail
                image.thumbnail((300, 300))
            else:
                # In view mode, maintain larger size
                image.thumbnail((800, 800))
            
            # Create container for each image
            st.markdown(f'<div class="image-container">', unsafe_allow_html=True)
            
            # Display image
            st.image(image)
            
            # Show controls in edit mode
            if st.session_state.view_mode == 'edit':
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("↺", key=f"left_{img_path}"):
                        st.session_state.image_rotations[img_path] = (current_rotation - 90) % 360
                        save_rotation_data()
                        st.rerun()
                with col2:
                    if st.button("↻", key=f"right_{img_path}"):
                        st.session_state.image_rotations[img_path] = (current_rotation + 90) % 360
                        save_rotation_data()
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_{img_path}", type="primary"):
                        if delete_image(img_path):
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"שגיאה בטעינת התמונה: {str(e)}")
    
    # End grid container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Delete album button at the bottom of edit mode
    if st.session_state.view_mode == 'edit':
        st.markdown("---")
        if st.button("מחק את כל האלבום", type="primary"):
            shutil.rmtree(st.session_state.upload_dir)
            st.session_state.images = []
            st.rerun()
else:
    if st.session_state.view_mode == 'edit':
        st.info("העלה תמונות כדי להתחיל!")
    else:
        st.info("האלבום ריק.") 