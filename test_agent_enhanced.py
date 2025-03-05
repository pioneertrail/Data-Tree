from biographical_agent import BiographicalAgent
import textwrap

def test_biographical_agent():
    print("Starting Enhanced BiographicalAgent tests...\n")
    
    # Create agent
    agent = BiographicalAgent("test_bio.db")
    print("✓ Created agent\n")
    
    # Add test data
    print("Adding test data...")
    agent.add_person(
        name="Alan Turing",
        birth_year="1912",
        birth_place="London, England",
        occupation="Computer Scientist",
        achievement="inventing the Turing machine, breaking the Enigma code, and pioneering artificial intelligence"
    )
    agent.add_person(
        name="Ada Lovelace",
        birth_year="1815",
        birth_place="London, England",
        occupation="Mathematician",
        achievement="writing the first computer program and recognizing that computers could go beyond mere calculation"
    )
    print("✓ Added test data\n")
    
    # Test queries
    print("Testing queries...")
    test_questions = [
        "When was Turing born?",
        "What was Ada's occupation?",
        "What did Lovelace do?",
        "Tell me about Alan Turing",
        "Who was Ada Lovelace?",
        "What was Turing's profession?",
        "What year was Ada born?",
        "What was xyz's occupation?",
        "What is Turing's favorite color?",
        "What did Turing achieve?",
        "What was Lovelace known for?",
        "What were Ada's contributions?"
    ]
    
    # Print with proper formatting
    for question in test_questions:
        print(f"\nQ: {question}")
        answer = agent.query(question)
        # Wrap text to 80 characters and indent continuation lines
        wrapped_answer = textwrap.fill(answer, width=80, subsequent_indent='   ')
        print(f"A: {wrapped_answer}")
        print("-" * 80)

if __name__ == "__main__":
    test_biographical_agent() 