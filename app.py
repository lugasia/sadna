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
        margin-bottom: 0 !important;
        border-bottom: none !important;
    }

    /* Spacer for fixed header */
    .header-spacer {
        margin: 0 !important;
        padding: 0 !important;
        height: 60px !important;
    }

    /* Additional screenshot prevention */
    body {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
        -webkit-touch-callout: none !important;
        -webkit-text-size-adjust: none !important;
    }

    /* Prevent screenshot on iOS */
    img {
        -webkit-user-select: none !important;
        -webkit-touch-callout: none !important;
        pointer-events: none !important;
        user-select: none !important;
        -webkit-user-drag: none !important;
        filter: blur(0.000001px) !important;
    }

    /* Grid layout for admin mode */
    .admin-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        padding: 8px;
        width: 100%;
        max-width: 1200px;
        margin: 0 auto;
    }

    .admin-image-container {
        position: relative;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
    }

    .admin-image-container img {
        width: 100%;
        aspect-ratio: 1;
        object-fit: cover;
        display: block;
    }

    .admin-controls {
        display: flex;
        gap: 4px;
        padding: 4px;
        background: rgba(255,255,255,0.9);
    }

    .admin-controls button {
        flex: 1;
        padding: 4px 8px;
        border: none;
        border-radius: 4px;
        background: #2c3e50;
        color: white;
        cursor: pointer;
        font-size: 14px;
    }

    /* View mode layout - continuous images */
    .view-grid {
        display: flex;
        flex-direction: column;
        gap: 0;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
        padding: 0;
        background: white;
        line-height: 0;
    }

    /* Remove ALL possible spacing from Streamlit elements */
    .view-grid > div {
        margin: 0 !important;
        padding: 0 !important;
    }

    .view-grid div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .view-grid div[class*="stVerticalBlock"] {
        gap: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .view-grid .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }

    .view-grid .stImage {
        margin: 0 !important;
        padding: 0 !important;
    }

    .view-grid .stImage > img {
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
    }

    .view-image-container {
        width: 100%;
        position: relative;
        margin: 0;
        padding: 0;
        line-height: 0;
        font-size: 0;
    }

    .view-image-container img {
        width: 100%;
        height: auto;
        display: block;
        margin: 0;
        padding: 0;
        transform: translate3d(0,0,0);
        backface-visibility: hidden;
    }

    /* Override any Streamlit default styles */
    .stApp [data-testid="stToolbar"] {
        display: none;
    }

    .stApp [data-testid="stDecoration"] {
        display: none;
    }

    .stApp [data-testid="stHeader"] {
        display: none;
    }

    /* Force remove any whitespace */
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }

    @media (max-width: 768px) {
        .admin-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 480px) {
        .admin-grid {
            grid-template-columns: repeat(1, 1fr);
        }
    }
</style>
""", unsafe_allow_html=True)

# Add meta tags for iOS screenshot prevention
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
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
if 'image_order' not in st.session_state:
    st.session_state.image_order = {}

# Get album_id from URL parameters
params = st.query_params
if 'album_id' in params:
    st.session_state.album_id = params['album_id']
    st.session_state.view_mode = 'view'

# Create upload directory if it doesn't exist
os.makedirs(st.session_state.upload_dir, exist_ok=True)

# Path for storing rotation data
rotation_file = os.path.join(st.session_state.upload_dir, 'rotations.json')

# Path for storing order data
order_file = os.path.join(st.session_state.upload_dir, 'image_order.json')

def load_rotation_data():
    if os.path.exists(rotation_file):
        with open(rotation_file, 'r') as f:
            return json.load(f)
    return {}

def save_rotation_data():
    with open(rotation_file, 'w') as f:
        json.dump(st.session_state.image_rotations, f)

def load_order_data():
    if os.path.exists(order_file):
        with open(order_file, 'r') as f:
            return json.load(f)
    return {}

def save_order_data():
    with open(order_file, 'w') as f:
        json.dump(st.session_state.image_order, f)

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(st.session_state.upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def move_image_up(img_path):
    images = st.session_state.images
    idx = images.index(img_path)
    if idx > 0:
        images[idx], images[idx-1] = images[idx-1], images[idx]
        # Update order data
        for i, img in enumerate(images):
            st.session_state.image_order[img] = i
        save_order_data()

def move_image_down(img_path):
    images = st.session_state.images
    idx = images.index(img_path)
    if idx < len(images) - 1:
        images[idx], images[idx+1] = images[idx+1], images[idx]
        # Update order data
        for i, img in enumerate(images):
            st.session_state.image_order[img] = i
        save_order_data()

def load_images_from_album():
    image_files = []
    for file in os.listdir(st.session_state.upload_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic')):
            image_files.append(os.path.join(st.session_state.upload_dir, file))
    
    # Load order data
    order_data = load_order_data()
    # Sort images based on saved order
    return sorted(image_files, key=lambda x: order_data.get(x, float('inf')))

def get_share_url():
    base_url = "https://lgvqgdba26dczmfvmh9qmd.streamlit.app"
    return f"{base_url}/?album_id={st.session_state.album_id}"

def delete_image(img_path):
    try:
        with st.spinner("מוחק תמונה..."):
            # Remove from rotations
            if img_path in st.session_state.image_rotations:
                del st.session_state.image_rotations[img_path]
                save_rotation_data()
            
            # Remove from order
            if img_path in st.session_state.image_order:
                del st.session_state.image_order[img_path]
                save_order_data()
            
            # Remove file from disk
            if os.path.exists(img_path):
                os.remove(img_path)
                
                # Git operations with proper error handling
                try:
                    # Run git commands with proper quoting and error checking
                    import subprocess
                    
                    # Stage the deletion
                    subprocess.run(['git', 'add', img_path], check=True)
                    
                    # Commit the change
                    subprocess.run(['git', 'commit', '-m', f'Remove image: {os.path.basename(img_path)}'], check=True)
                    
                    # Push to remote
                    subprocess.run(['git', 'push'], check=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"שגיאה בפעולות Git: {str(e)}")
                    return False
            
            # Remove from session state
            if img_path in st.session_state.images:
                st.session_state.images.remove(img_path)
            
            st.success("התמונה נמחקה בהצלחה!")
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

# Display images based on mode
st.session_state.images = load_images_from_album()
if st.session_state.images:
    if st.session_state.view_mode == 'edit':
        # Admin mode - grid layout
        st.markdown('<div class="admin-grid">', unsafe_allow_html=True)
        
        for img_path in st.session_state.images:
            try:
                current_rotation = st.session_state.image_rotations.get(img_path, 0)
                image = Image.open(img_path)
                if current_rotation:
                    image = image.rotate(-current_rotation, expand=True)
                
                # Resize for admin view
                image.thumbnail((300, 300))
                
                # Create container for each image
                st.markdown('<div class="admin-image-container">', unsafe_allow_html=True)
                st.image(image)
                
                # Admin controls
                col1, col2, col3, col4, col5 = st.columns(5)
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
                    if st.button("⬆️", key=f"up_{img_path}"):
                        move_image_up(img_path)
                        st.rerun()
                with col4:
                    if st.button("⬇️", key=f"down_{img_path}"):
                        move_image_down(img_path)
                        st.rerun()
                with col5:
                    if st.button("🗑️", key=f"delete_{img_path}", type="primary"):
                        if delete_image(img_path):
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"שגיאה בטעינת התמונה: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # View mode - continuous layout
        st.markdown('<div class="view-grid">', unsafe_allow_html=True)
        
        for img_path in st.session_state.images:
            try:
                current_rotation = st.session_state.image_rotations.get(img_path, 0)
                image = Image.open(img_path)
                if current_rotation:
                    image = image.rotate(-current_rotation, expand=True)
                
                # Resize for view mode
                image.thumbnail((800, 800))
                
                # Display image
                st.markdown('<div class="view-image-container">', unsafe_allow_html=True)
                st.image(image)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"שגיאה בטעינת התמונה: {str(e)}")
        
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