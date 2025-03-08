# AI Educational Assistant

An interactive educational AI assistant that provides detailed, age-appropriate responses across various subjects including science, mathematics, history, literature, art, music, and technology.

## Features

- Interactive web interface
- Real-time AI responses using OpenAI's GPT-3.5
- Topic-specific educational content
- Analytics for response complexity, engagement, and relevance
- Conversation history tracking
- Age-appropriate content delivery

## Tech Stack

- Python 3.x
- Flask
- SQLAlchemy
- OpenAI API
- HTML/CSS/JavaScript

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-educational-assistant.git
cd ai-educational-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python run.py
```

5. Visit `http://127.0.0.1:5000` in your browser

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_ENV`: Set to `development` for debug mode
- `DATABASE_URL`: SQLite database URL (defaults to SQLite)

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── extensions.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── ai.py
│   │   └── ...
│   └── templates/
│       └── index.html
├── requirements.txt
├── run.py
└── README.md
```

## Security Note

This project uses environment variables for sensitive information. Never commit your `.env` file or expose your API keys. 