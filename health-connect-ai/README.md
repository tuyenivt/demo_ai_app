# HealthConnect AI Chatbot System

## Overview
- A telehealth chatbot system providing 24/7 patient support.
- Using pre-trained NLP models for clinical [scispaCy](https://github.com/allenai/scispacy) - `en_core_sci_md`: This is a medium-sized spaCy model trained on biomedical literature, enabling accurate entity recognition and text processing for medical data.

## Features
- **Rasa NLP**: Intent recognition, entity extraction, dialogue management (spaCy, TensorFlow).
- **FastAPI Backend**: RESTful APIs for chatbot, feedback.

## Setup

### 1. Validate pre-trained `en_core_sci_md` model
```shell
python -m spacy validate
```
Installed pipeline packages should included `en_core_sci_md` (which installed via `pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz`)

### 2. Rasa (NLP) train
```shell
cd rasa
python train_rasa.py
```
The `train_rasa.py` script leverages the pre-trained `en_core_sci_md` model to train Rasa's NLU components, such as intent detection and entity extraction, specifically for handling clinical and scientific terminology in the chatbot's responses.

### 3. Test via shell (interactive console)
```shell
cd rasa
rasa shell --debug
```

### 4. Test via HTTP API (REST)
```shell
cd rasa
rasa run --enable-api --debug
```
The assistant's REST API is available at `http://localhost:5005`

Use the model programmatically: `http://localhost:5005/webhooks/rest/webhook`

Sample Request
```shell
curl -X POST http://localhost:5005/webhooks/rest/webhook -H "Content-Type: application/json" -d '{"sender":"test_user", "message":"hello"}'
```

Sample Response
```shell
[{
    "recipient_id" : "test_user",
    "text" : "Hello! How can I assist you today?"
}]
```

### 5. FastAPI Backend
```shell
uvicorn backend.main:app --reload
```

Sample Request
```shell
curl -X POST http://localhost:8000/chat/ -H "Content-Type: application/json" -d '{"sender_id":"test_user", "message":"hello"}'
```

Sample Response
```shell
{
    "responses": [{
        "recipient_id": "test_user",
        "text": "Hello! How can I assist you today?"
    }]
}
```
