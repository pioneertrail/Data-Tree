from enum import Enum

class SenderType(Enum):
    STUDENT = 'student'
    AI = 'ai'

class TopicArea(Enum):
    MATH = 'math'
    SCIENCE = 'science'
    LANGUAGE = 'language'
    HISTORY = 'history'
    COMPUTER_SCIENCE = 'computer_science'
    OTHER = 'other'

class LearningStyle(Enum):
    VISUAL = 'visual'
    AUDITORY = 'auditory'
    KINESTHETIC = 'kinesthetic'
    READING_WRITING = 'reading_writing'
    MULTIMODAL = 'multimodal' 