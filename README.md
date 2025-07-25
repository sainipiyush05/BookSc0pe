# BookScope - AI Book Search System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.0+-brightgreen.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-powered book search system for DRDO's DESIDOC lab. Search topics and get exact book titles with page numbers using semantic search and automated indexing.

## 🎯 Overview

Built during DRDO internship to automate technical book management. Users search topics in natural language and receive precise book/page results instantly.

## ✨ Features

- **🔍 Semantic Search**: Context-aware AI search beyond keywords
- **📄 Text Extraction**: OCR and PDF processing for all document types
- **🤖 Auto Indexing**: AI maps topics to exact page numbers
- **⚡ Real-time Results**: Instant search with page-level precision
- **🔄 Automation**: Make.com integration for workflow automation
- **👥 User Auth**: JWT-based authentication and access control

## 🛠️ Tech Stack

- **Backend**: Python, Flask, MongoDB
- **AI/ML**: HuggingFace, BERT, OpenAI API
- **Processing**: PyPDF2, Tesseract OCR, NLTK
- **Frontend**: JavaScript, HTML, CSS
- **Automation**: Make.com

## 📋 Requirements

- Python 3.8+
- MongoDB 4.0+
- Tesseract OCR
- OpenAI/HuggingFace API key

## 🚀 Quick Setup

1. **Clone & Install**
git clone https://github.com/sainipiyush05/bookscope.git
cd bookscope
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

text

2. **Configure**
cp .env.example .env

Edit .env with your API keys
text

3. **Run**
python app.py

Visit http://localhost:5000
text

## 📁 Structure

bookscope/
├── app.py # Main application
├── scripts/ # Processing utilities
├── api/ # REST endpoints
├── templates/ # Web interface
├── static/ # CSS/JS assets
└── tests/ # Unit tests

text

## 🔧 API Usage

### Search
POST /api/search
{
"query": "machine learning",
"limit": 10
}

text

### Upload
POST /api/upload
Content-Type: multipart/form-data
file: [PDF]

text

## 🧪 Testing

python -m pytest tests/ -v

text


## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

## 📞 Contact

**Piyush Saini**
- Email: saini2005piyush@gmail.com
- GitHub: [@sainipiyush05](https://github.com/sainipiyush05)
- LinkedIn: [piyush-saini-8bb40827a](https://www.linkedin.com/in/piyush-saini-8bb40827a/)

## 📊 Metrics

- Search Accuracy: 95%+
- Processing: 2 min/100 pages
- Formats: PDF, ePub, DOCX, TXT
- Concurrent Users: 100+

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

