import chromadb
from groq import Groq
import os
import uuid
from datetime import date, datetime
from dotenv import load_dotenv
import PyPDF2
from docx import Document

load_dotenv()

# --- Setup ---
client = chromadb.PersistentClient(path="./study_notes_db")
collection = client.get_or_create_collection("study_notes")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# Handles user study notes
def add_study_note(text, user_id, topic):
    collection.add(
        documents=[text],
        metadatas=[{"user": user_id, "topic": topic, "date": str(date.today())}],
        ids=[str(uuid.uuid4())]
    )

#Helps to get current date and time

def get_current_date():
    """Get today's actual real date."""
    return datetime.now().strftime("%B %d, %Y")

#Helps to search notes based on user query and user id

def search_notes(query, user_id, n_results=3):
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"user": user_id}
    )
    return results["documents"][0] if results["documents"] else []


def list_my_notes(user_id):
    """Return a list of note summaries for this user, including their IDs for deletion."""
    all_data = collection.get(where={"user": user_id})
    notes = []
    for i in range(len(all_data["ids"])):
        notes.append({
            "id": all_data["ids"][i],
            "topic": all_data["metadatas"][i]["topic"],
            "date": all_data["metadatas"][i]["date"],
            "preview": all_data["documents"][i][:80]
        })
    return notes


def delete_note(note_id):
    """Delete a single note/chunk by its ID."""
    collection.delete(ids=[note_id])


def delete_all_notes(user_id):
    """Delete every note belonging to this user."""
    all_data = collection.get(where={"user": user_id})
    if all_data["ids"]:
        collection.delete(ids=all_data["ids"])


# --- File ingestion: PDF, DOCX, TXT ---
def extract_text_from_file(filepath):
    """Extract raw text from PDF, DOCX, or TXT files."""
    if filepath.endswith(".pdf"):
        text = ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    elif filepath.endswith(".docx"):
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    elif filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {filepath}")


def chunk_text(text, chunk_size=500):
    """Split text into chunks of roughly chunk_size characters, by word boundaries."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1
        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def add_file_notes(filepath, user_id, topic):
    full_text = extract_text_from_file(filepath)
    chunks = chunk_text(full_text)

    for chunk in chunks:
        add_study_note(chunk, user_id, topic)

    return len(chunks)


# --- The assistant, with memory ---
class KnowledgeAssistant:
    def __init__(self, user_id):
        self.user_id = user_id
        self.conversation_history = []

    def ask(self, question):
        # Reliable, code-based answers for things models get wrong (date/time)
        date_keywords = ["today's date", "what date", "what's the date", "current date", "today date"]
        time_keywords = ["what time", "current time", "what's the time"]

        if any(word in question.lower() for word in date_keywords):
            answer = f"Today's date is {get_current_date()}."
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer, []

        if any(word in question.lower() for word in time_keywords):
            current_time = datetime.now().strftime("%I:%M %p")
            answer = f"The current time is {current_time}."
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer, []

        # Everything else: search notes, but let the model freely use general knowledge too
        relevant_notes = search_notes(question, self.user_id)
        context = "\n\n".join(relevant_notes) if relevant_notes else "No relevant notes found."

        system_prompt = """You are a helpful, knowledgeable assistant.

You have access to the student's personal study notes as additional context below.
- If the notes are relevant to the question, use them and mention "(from your notes)".
- If the notes aren't relevant, or the question is general knowledge, answer normally
  using what you know - don't refuse just because it's not in the notes.
- Never claim the user said something they didn't actually say.
- Give correct information when asked about time and date related information.
- Don't show ur thinking process to the user ; if you don't know, say so honestly instead of guessing. Be careful and cautios"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": f"Notes context:\n{context}\n\nQuestion: {question}"})

        response = groq_client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=messages,
            temperature=0.3
        )
        answer = response.choices[0].message.content

        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})

        return answer, relevant_notes