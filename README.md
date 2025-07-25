# DESIDOC Library Search System

A comprehensive document search system for DESIDOC library that allows users to search for specific content within books and get exact page references.

## Features

- PDF document upload and indexing
- Full-text search with page-level results
- MongoDB-based storage and indexing
- Web-based interface
- RESTful API

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Start MongoDB service
5. Run the application: `python backend/app.py`

## Usage

1. Upload PDF documents through the web interface
2. Search for content using keywords
3. View results with page numbers and relevance scores

## API Endpoints

- `POST /api/upload` - Upload and index documents
- `GET /api/search` - Search documents
- `GET /api/books` - List all books

## Project Structure

