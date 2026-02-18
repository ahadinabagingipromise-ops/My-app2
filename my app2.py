import streamlit as st
from firebase_config import db
from datetime import datetime
from PIL import Image
import os

# --------------------------
# Setup
# --------------------------
st.title("Mini WhatsApp Clone - Streamlit")

# Create folder for uploaded images
if not os.path.exists("images"):
    os.makedirs("images")

# --------------------------
# 1. User Login
# --------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    username = st.text_input("Enter your username")
    if st.button("Login"):
        if username.strip():
            st.session_state.user = username.strip()
            st.experimental_rerun()
else:
    st.write(f"Logged in as: **{st.session_state.user}**")

    # --------------------------
    # 2. Select Chat Room
    # --------------------------
    chats_ref = db.collection("chats")
    chats_docs = chats_ref.stream()
    chat_names = [doc.id for doc in chats_docs]
    
    chat_choice = st.selectbox("Select Chat Room", chat_names + ["Create New Chat"])
    
    if chat_choice == "Create New Chat":
        new_chat = st.text_input("Enter chat room name")
        if st.button("Create Chat"):
            if new_chat.strip():
                db.collection("chats").document(new_chat.strip()).set({"created_at": datetime.utcnow()})
                st.experimental_rerun()
    elif chat_choice:
        chat_id = chat_choice

        # --------------------------
        # 3. Show Messages
        # --------------------------
        messages_ref = db.collection("chats").document(chat_id).collection("messages").order_by("timestamp")
        messages = messages_ref.stream()
        
        st.subheader(f"Chat Room: {chat_id}")
        for msg in messages:
            msg_data = msg.to_dict()
            user = msg_data.get("sender")
            text = msg_data.get("text", "")
            image_path = msg_data.get("image", None)
            timestamp = msg_data.get("timestamp")
            
            time_str = ""
            if timestamp:
                if hasattr(timestamp, "seconds"):  # Firestore timestamp
                    ts = datetime.fromtimestamp(timestamp.seconds)
                    time_str = ts.strftime("%H:%M")
                else:
                    time_str = str(timestamp)
            
            if image_path:
                st.image(image_path, caption=f"{user} ({time_str})", width=200)
            if text:
                st.write(f"**{user} ({time_str}):** {text}")

        # --------------------------
        # 4. Send Message
        # --------------------------
        st.subheader("Send a message")
        message_text = st.text_input("Message", key="msg_input")
        image_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], key="img_upload")
        
        if st.button("Send"):
            data = {"sender": st.session_state.user,
                    "timestamp": datetime.utcnow()}

            if message_text.strip():
                data["text"] = message_text.strip()
            
            if image_file is not None:
                img = Image.open(image_file)
                img_name = f"images/{datetime.utcnow().timestamp()}_{image_file.name}"
                img.save(img_name)
                data["image"] = img_name  # Save local path for demo
            
            db.collection("chats").document(chat_id).collection("messages").add(data)
            st.experimental_rerun()