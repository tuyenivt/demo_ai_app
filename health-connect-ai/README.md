# HealthConnect AI Chatbot System

## Overview
- A telehealth chatbot system providing 24/7 patient support, appointment scheduling, and EHR integration.
- Using pre-trained NLP models for clinical [scispaCy](https://github.com/allenai/scispacy) - `en_core_sci_md`: This is a medium-sized spaCy model trained on biomedical literature, enabling accurate entity recognition and text processing for medical data.

## Features
- **Rasa NLP**: Intent recognition, entity extraction, dialogue management (spaCy, TensorFlow)
- **FastAPI Backend**: RESTful APIs for chatbot, appointments, EHR, feedback
- **Feedback Loop**: Collects feedback for continuous learning

## Setup

### 1. Rasa (NLP)
```bash
cd rasa
python train_rasa.py
```
The `train_rasa.py` script leverages the pre-trained `en_core_sci_md` model to train Rasa's NLU components, such as intent detection and entity extraction, specifically for handling clinical and scientific terminology in the chatbot's responses.

