# AI Educational Assistant

An intelligent educational assistant that provides personalized responses and learning experiences using OpenAI's GPT-3.5 model.

## Features

- **Interactive Q&A Interface**: Ask questions on various subjects and receive detailed, educational responses
- **Analytics**: Get insights into response complexity, engagement level, and topic relevance
- **Subject-Specific Responses**: Specialized responses for different subjects including:
  - Science
  - Mathematics
  - History
  - Literature
  - Art
  - Music
  - Technology

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Data-Tree
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your-api-key-here
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

4. Initialize the database:
```bash
python run.py
```

## Usage

1. Start the Flask server:
```bash
python run.py
```

2. Open your browser and navigate to `http://127.0.0.1:5000`

3. Use the web interface to:
   - Ask questions on various topics
   - View response analytics
   - Get personalized educational responses

## API Endpoints

### Generate AI Response
- **URL**: `/api/ai/generate`
- **Method**: `POST`
- **Body**:
```json
{
    "content": "Your question here",
    "topic_area": "science"
}
```
- **Response**:
```json
{
    "content": "AI generated response",
    "analytics": {
        "complexity_score": 0.7,
        "engagement_score": 0.8,
        "topic_relevance": 0.9
    }
}
```

### Create Lesson Plan
- **URL**: `/api/ai/lesson-plan`
- **Method**: `POST`
- **Body**:
```json
{
    "user_id": "user_id",
    "subject": "subject_name"
}
```

### Create Group Activity
- **URL**: `/api/ai/group-activity`
- **Method**: `POST`
- **Body**:
```json
{
    "user_ids": ["user_id1", "user_id2"],
    "subject": "subject_name"
}
```

## Project Structure

```
app/
├── __init__.py          # Flask application factory
├── extensions.py        # Flask extensions (SQLAlchemy)
├── models.py           # Database models
├── routes/
│   ├── __init__.py
│   └── ai.py           # AI-related routes
├── services/
│   └── ai_teacher.py   # AI teaching logic
└── templates/
    └── index.html      # Web interface
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT-3.5 model
- Flask framework and its extensions
- SQLAlchemy for database management 