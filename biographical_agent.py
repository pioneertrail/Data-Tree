import json
from datetime import datetime
from memory_manager import BiographicalMemory
import textwrap
import re

class BiographicalAgent:
    def __init__(self, db_path="bio_memory.db"):
        """Initialize the biographical agent.
        
        Args:
            db_path (str): Path to the database file
        """
        self.memory = BiographicalMemory(db_path)
        self.current_person = None
        self.unknown_questions = set()  # Track questions we can't answer

    def add_person(self, name, birth_year, birth_place, death_year=None, 
                  death_place=None, occupation=None, achievement=None,
                  education=None, nationality=None, known_for=None):
        """Add a person's biographical data.
        
        Args:
            name (str): Person's full name
            birth_year (str): Year of birth
            birth_place (str): Place of birth
            death_year (str, optional): Year of death
            death_place (str, optional): Place of death
            occupation (str, optional): Primary occupation
            achievement (str, optional): Notable achievement
            education (str, optional): Education
            nationality (str, optional): Nationality
            known_for (str, optional): Known for
        """
        data = {
            'birth_year': birth_year,
            'birth_place': birth_place,
            'death_year': death_year,
            'death_place': death_place,
            'occupation': occupation,
            'achievement': achievement,
            'education': education,
            'nationality': nationality,
            'known_for': known_for
        }
        self.memory.store(name, data)

    def query(self, question):
        """Answer questions about people in the database."""
        if question is None or not isinstance(question, str) or question.strip() == "":
            return "Please ask a question. Type 'help' for examples."
        
        question = question.lower().strip()
        
        if question in ['help', '?']:
            return self._show_help()
        elif question in ['list', 'who do you know?', 'who do you know about?']:
            return self._list_people()
        elif question == 'exit':
            return "Goodbye!"
            
        name = self._extract_name(question)
        if not name:
            return ("I don't recognize that person. Type 'list' to see who I know about, "
                   "or 'help' for example questions.")
            
        # Check if the question is about an unsupported attribute
        unsupported_patterns = [
            r'favorite color', r'favorite food', r'height', r'weight',
            r'eye color', r'hair color', r'favorite'
        ]
        if any(re.search(pattern, question) for pattern in unsupported_patterns):
            return (f"I don't have information about personal preferences or physical characteristics. "
                    f"Try asking about {name}'s birth, death, occupation, achievements, or what they were known for.")
        
        field = self._extract_field(question)
        if not field:
            if any(word in question for word in ['who', 'what', 'where', 'when', 'tell', 'about']):
                return self._handle_general_question(question, name)
            return (f"I don't understand what you're asking about {name}. "
                   "Try asking about their birth, death, occupation, achievements, or what they were known for.")
            
        answer = self.memory.retrieve(name, field)
        if answer:
            return self._format_answer(name, field, answer)
        return f"I don't have information about {name}'s {field.replace('_', ' ')}."

    def _show_help(self):
        """Show example questions."""
        examples = [
            "When was [person] born?",
            "Where was [person] born?",
            "What was [person]'s occupation?",
            "What did [person] achieve?",
            "Tell me about [person]",
            "Where did [person] study?",
            "What was [person] known for?",
            "Type 'list' to see all people I know about"
        ]
        return "Example questions:\n" + "\n".join(f"- {q}" for q in examples)

    def _list_people(self):
        """List all people in the database."""
        people = self.memory.get_all_people()
        return "I know about:\n" + "\n".join(f"- {p}" for p in people)

    def _extract_name(self, question):
        """Extract person's name from the question."""
        known_people = {
            'turing': 'Alan Turing',
            'lovelace': 'Ada Lovelace',
            'ada': 'Ada Lovelace',
            'alan': 'Alan Turing'
        }
        
        for key, full_name in known_people.items():
            if key in question:
                return full_name
        return None

    def _extract_field(self, question):
        """Extract the field being asked about."""
        patterns = {
            'birth_year': r'when.*born|birth.*year|year.*birth',
            'birth_place': r'where.*born|birth.*place|place.*birth',
            'death_year': r'when.*die|death.*year|year.*death',
            'death_place': r'where.*die|death.*place|place.*death',
            'occupation': r'occupation|job|work|profession|what.*do',
            'achievement': r'achieve|accomplish|contribution|what.*did.*do',
            'education': r'study|education|university|college',
            'nationality': r'nationality|citizen|where.*from',
            'known_for': r'known for|famous for|remembered|legacy'
        }
        
        for field, pattern in patterns.items():
            if re.search(pattern, question):
                return field
        return None

    def _handle_general_question(self, question, name):
        """Handle general questions about a person."""
        data = {}
        fields = ['birth_year', 'birth_place', 'occupation', 'nationality', 
                  'achievement', 'known_for', 'death_year']
        
        for field in fields:
            data[field] = self.memory.retrieve(name, field)
        
        # Check if asking specifically about achievements
        if 'achieve' in question or 'did' in question:
            if data['achievement']:
                return f"{name} {data['achievement']}."
            return f"I don't have information about {name}'s achievements."
        
        # Check if asking about what they're known for
        if 'known for' in question:
            if data['known_for']:
                return f"{name} is known for {data['known_for']}."
            return f"I don't have information about what {name} was known for."
        
        # General biography
        response = []
        if data['birth_year'] and data['birth_place']:
            response.append(f"{name} was born in {data['birth_year']} in {data['birth_place']}")
        
        if data['occupation']:
            response.append(f"They were a {data['occupation']}")
        
        if data['achievement']:
            response.append(f"They achieved {data['achievement']}")
        
        if data['known_for']:
            response.append(f"and are known for {data['known_for']}")
        
        if data['death_year']:
            response.append(f"They died in {data['death_year']}")
        
        if response:
            return '. '.join(response) + '.'
        return f"I don't have detailed information about {name}."

    def _format_answer(self, name, field, answer):
        """Format the answer in a natural way."""
        formats = {
            'birth_year': f"{name} was born in {answer}.",
            'birth_place': f"{name} was born in {answer}.",
            'death_year': f"{name} died in {answer}.",
            'death_place': f"{name} died in {answer}.",
            'occupation': f"{name} was a {answer}.",
            'achievement': f"{name} achieved {answer}.",
            'education': f"{name} studied at {answer}.",
            'nationality': f"{name} was {answer}.",
            'known_for': f"{name} is known for {answer}."
        }
        return formats.get(field, f"{name}'s {field.replace('_', ' ')} was {answer}.")

    def _parse_query(self, request):
        """Parse a biographical query into a path."""
        if "occupation" in request:
            return ["Personal", "Occupation"]
        elif "born" in request:
            return ["Personal", "Birth", "Year"]
        elif "work" in request:
            return ["Achievements", "Work"]
        elif "impact" in request:
            return ["Legacy", "Impact"]
        
        return None

    def _get_index(self, step):
        """Map path step to bit index."""
        mapping = {
            "Personal": 0,
            "Achievements": 1,
            "Legacy": 2,
            "Name": 0,
            "Known": 1,
            "Occupation": 2,
            "Birth": 3,
            "Work": 0,
            "Awards": 1,
            "Impact": 0,
            "Year": 0,
            "Place": 1
        }
        return mapping.get(step, 0)

    def get_historical_data(self, start_date=None, end_date=None):
        """Retrieve historical data entries."""
        return self.memory.get_history(start_date, end_date)

    def get_unknown_questions(self):
        """Return list of questions we couldn't properly answer."""
        return list(self.unknown_questions)

    def interactive_mode(self):
        """Start interactive mode."""
        print("\nWelcome to the Historical Figures Database!")
        print("Type 'help' for example questions, 'list' to see who I know about, or 'exit' to quit.\n")
        
        while True:
            question = input("\nYour question: ").strip()
            if question.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
                
            answer = self.query(question)
            print("\nAnswer:", textwrap.fill(answer, width=80, subsequent_indent='        ')) 