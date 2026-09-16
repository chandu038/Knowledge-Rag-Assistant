# Knowledge RAG Assistant

An AI-powered study assistant that uses Retrieval-Augmented Generation (RAG) to answer questions from your own material and help manage personalized study notes.

🔗 **Live:** [knowledge-rag-assistant.streamlit.app](https://knowledge-rag-assistant.streamlit.app/)

## Overview

Knowledge RAG Assistant lets users interact with their study material through natural language. Instead of manually searching notes or documents, users can ask questions and get grounded, context-aware answers — powered by a RAG pipeline rather than a plain LLM call, so responses stay tied to the actual source material.

## Features

- Retrieval-Augmented Generation (RAG) pipeline for grounded, context-aware answers
- Add and manage personalized study notes
- Conversational interface for querying study material
- Agent-based architecture for handling multi-step reasoning tasks

## Tech Stack

**Language:** Python
**AI/GenAI:** LangChain, RAG pipeline, LLM APIs
**Interface:** Streamlit
**Deployment:** Streamlit Community Cloud

## Architecture

```
User Query → Streamlit UI → Agent/RAG Pipeline → Vector Retrieval → LLM → Response
                                    │
                              Study Notes Store
```

## Getting Started

### Prerequisites
- Python 3.9+
- API key for your chosen LLM provider (OpenAI/Gemini)

### Setup
```bash
git clone https://github.com/chandu038/Knowledge-Rag-Assistant.git
cd Knowledge-Rag-Assistant
pip install -r requirements.txt
```

### Configuration
Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
```

### Run
```bash
streamlit run app.py
```

## Roadmap

- [ ] Support for uploading PDFs/documents directly
- [ ] Multi-user support with saved sessions
- [ ] Expand agent capabilities beyond study notes

## Author

**Darapaneni Chandu**
[LinkedIn](https://www.linkedin.com/in/chandu-darapaneni-1631b3329/) · [GitHub](https://github.com/chandu038)
