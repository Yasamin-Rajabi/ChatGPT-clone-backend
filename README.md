# 💬 ChatGPT Clone Backend API (Django REST Framework)

This is a robust, production-ready backend API simulating a ChatGPT-like AI chatbot system. Built using **Django** and **Django REST Framework (DRF)**, this application is fully compliant with modern RESTful practices, secure authorization, and advanced features such as tenant-like project partitioning, database soft-deletion, account-linking/switching, and file uploads.

---

## API Documentation & Interactive Playground (Swagger)

All API endpoints are fully documented and structured with appropriate schemas and real-world examples (Requests and Responses) using `drf-spectacular`.

* **Interactive Swagger UI:** 🔗 [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
* **Redoc Alternative View:** 🔗 [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
* **Raw OpenAPI Schema (JSON):** 🔗 [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

## Key Features Implemented

* **JWT Authentication:** Secure user sign-up, sign-in, and token-refresh flows utilizing `djangorestframework-simplejwt`.
* **Account Linking & Switching:** Allows users to securely link multiple accounts and switch between active sessions dynamically without re-entering credentials.
* **Subscription & Rate Limiting (Throttling):** * **Free Tier:** Restricted to 50 messages/day, standard models (e.g., GPT-3.5), and no file uploads.
    * **Premium Tier:** Unlimited usage, access to advanced models (e.g., GPT-4/Claude), and file attachment capabilities.
* **Advanced Conversation Management:**
    * Multi-turn chat sessions bound to custom Projects.
    * **Soft Delete:** Conversations are never physically deleted from the database; their status is marked as `DELETED` to preserve history.
    * **Mocked AI Responses:** Seamless generation of realistic, context-aware mock responses based on the selected AI model and current assistant.
* **Multipart File Uploads:** Supports uploading documents, images, or code attachments directly via `multipart/form-data` requests (restricted to Premium users).
* **Cross-Reference Validation:** Tight backend security ensuring users can only interact with, modify, or send messages to projects and conversations they actually own.

---

## Installation & Local Setup Guide

Follow these steps to set up and run the backend server locally on your machine:

### 1. Clone and Initialize Virtual Environment
```bash
# Initialize a virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate
