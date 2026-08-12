import streamlit as st
import tempfile
import os
from assistant import (
    KnowledgeAssistant, add_study_note, add_file_notes,
    list_my_notes, delete_note
)

st.set_page_config(page_title="Study Assistant", page_icon="📚", layout="wide")

# --- Session state setup (Streamlit's way of "remembering" between interactions) ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # for DISPLAY purposes (separate from agent memory)


# --- Login screen (simple name entry, no real auth - as discussed) ---
if st.session_state.user_id is None:
    st.title("📚 Personal AI Knowledge Assistant")
    st.write("Enter your name to access your study notes.")
    name = st.text_input("Your name")
    if st.button("Start"):
        if name.strip():
            st.session_state.user_id = name.strip().lower()
            st.session_state.assistant = KnowledgeAssistant(st.session_state.user_id)
            st.rerun()
    st.stop()


# --- Main app (once logged in) ---
user_id = st.session_state.user_id
assistant = st.session_state.assistant

st.title(f"📚 {user_id}'s Study Assistant")

# --- Sidebar: add notes, upload files, view + delete stored notes ---
with st.sidebar:
    st.header("Add Knowledge")

    tab1, tab2 = st.tabs(["✏️ Type a note", "📄 Upload a file"])

    with tab1:
        topic = st.text_input("Topic", key="type_topic")
        note_text = st.text_area("Note content", key="type_text")
        if st.button("Add Note"):
            if topic and note_text:
                with st.spinner("💾 Saving your note..."):
                    add_study_note(note_text, user_id, topic)
                st.success(f"Added note on '{topic}'")
                st.rerun()
            else:
                st.warning("Please fill in both fields.")

    with tab2:
        uploaded_file = st.file_uploader("Choose a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
        file_topic = st.text_input("Topic for this file", key="file_topic")
        if st.button("Add File"):
            if uploaded_file and file_topic:
                with st.spinner(f"📖 Reading and chunking {uploaded_file.name}..."):
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        num_chunks = add_file_notes(tmp_path, user_id, file_topic)
                        st.success(f"✅ Added {num_chunks} chunks from {uploaded_file.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
                    finally:
                        os.unlink(tmp_path)
            else:
                st.warning("Please choose a file and enter a topic.")

    st.divider()
    st.header("Your Notes")
    notes = list_my_notes(user_id)
    if not notes:
        st.caption("No notes yet — add some above!")
    else:
        st.caption(f"{len(notes)} chunk(s) stored")
        for note in notes:
            with st.expander(f"[{note['topic']}] {note['date']}"):
                st.write(note["preview"] + "...")
                if st.button("🗑️ Delete", key=f"delete_{note['id']}"):
                    delete_note(note["id"])
                    st.success("Deleted!")
                    st.rerun()


# --- Main chat area ---
st.subheader("Ask your assistant")

# Replay past messages in this session
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources used"):
                for s in msg["sources"]:
                    st.caption(s[:150] + "...")

# New question input
question = st.chat_input("Ask a question about your notes, or anything else...")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("🔎 Thinking..."):
            answer, sources = assistant.ask(question)
        st.write(answer)
        if sources:
            with st.expander("📎 Sources used"):
                for s in sources:
                    st.caption(s[:150] + "...")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })