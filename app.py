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
    /* Prevent screen capture and strengthen protection */
    body {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
        -webkit-touch-callout: none !important;
        -webkit-text-size-adjust: none !important;
    }
    
    img {
        -webkit-user-drag: none !important;
        -khtml-user-drag: none !important;
        -moz-user-drag: none !important;
        -o-user-drag: none !important;
        user-drag: none !important;
        pointer-events: none !important;
        -webkit-touch-callout: none !important;
        -webkit-user-select: none !important;
    }
    
    /* Title styling - fixed and always visible */
    .sticky-header {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 9999 !important;
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(5px) !important;
        -webkit-backdrop-filter: blur(5px) !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        text-align: center !important;
        height: auto !important;
        min-height: 60px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .sticky-header h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 24px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        font-family: Arial, sans-serif !important;
    }
    
    /* Spacer to prevent content from hiding under header */
    .header-spacer {
        height: 80px !important;
        width: 100% !important;
        display: block !important;
    }
    
    /* Rest of your existing styles... */
    .mobile-container {
        max-width: 100%;
        padding: 10px;
        margin: 0 auto;
    }
    
    .stImage {
        margin: 30px 0;
        transition: all 0.3s ease;
        -webkit-tap-highlight-color: transparent;
    }
    
    .stImage > img {
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
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
    
    .delete-button {
        background: #e74c3c !important;
    }
    
    .delete-button:hover {
        background: #c0392b !important;
    }
    
    .stButton button:hover {
        background: #34495e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* Edit mode controls */
    .edit-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 10px 0;
    }
    
    /* Image container */
    .image-container {
        position: relative;
        margin: 20px 0;
        padding: 10px;
        border-radius: 15px;
        background: white;
    }
    
    /* Additional screen capture prevention */
    ::selection {
        background: transparent !important;
    }
    ::-moz-selection {
        background: transparent !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .sticky-header {
            min-height: 50px !important;
        }
        
        .sticky-header h1 {
            font-size: 20px !important;
        }
        
        .header-spacer {
            height: 60px !important;
        }
        
        .stButton button {
            padding: 10px 20px;
            font-size: 14px;
        }
        
        .stImage {
            margin: 15px 0;
        }
    }
    
    /* Prevent text selection globally */
    * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
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

def delete_image(img_path):
    """Delete an image and its rotation data."""
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

# Add meta tags to prevent screen capture
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# Sticky header with improved styling
st.markdown('''
    <div class="sticky-header">
        <h1>סדנת יצירה 2025</h1>
    </div>
    <div class="header-spacer"></div>
''', unsafe_allow_html=True)

# Show admin controls at the top if in edit mode
if st.session_state.view_mode == 'edit':
    # Sharing options at the top
    st.subheader("שיתוף אלבום")
    share_url = get_share_url()
    st.write("קישור לשיתוף:", share_url)
    qr_code = qrcode.make(share_url)
    qr_bytes = BytesIO()
    qr_code.save(qr_bytes, format='PNG')
    qr_bytes = qr_bytes.getvalue()
    
    col1, col2 = st.columns([1, 2])
    with col1:
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
    
    st.markdown("---")

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
                
                # Calculate image dimensions
                img_width, img_height = image.size
                aspect_ratio = img_height / img_width
                
                # Adjust image size based on view mode
                if st.session_state.view_mode == 'edit':
                    # In edit mode, display at 20% of original size
                    display_width = int(img_width * 0.2)
                else:
                    # In view mode, maintain the current max width of 800px
                    display_width = min(800, img_width)
                
                display_height = int(display_width * aspect_ratio)
                
                # Resize image while maintaining aspect ratio
                image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Create image container
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                
                # Display image with padding
                st.image(image, use_container_width=True)
                
                # Show controls in edit mode
                if st.session_state.view_mode == 'edit':
                    col1, col2, col3 = st.columns(3)
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
                    with col3:
                        if st.button("🗑️ מחק תמונה", key=f"delete_{img_path}", type="primary"):
                            if delete_image(img_path):
                                st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"שגיאה בטעינת התמונה: {str(e)}")
    
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