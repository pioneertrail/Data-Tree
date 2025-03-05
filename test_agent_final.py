from biographical_agent import BiographicalAgent

def test_biographical_agent():
    print("Starting Final BiographicalAgent tests...\n")
    
    # Create agent
    agent = BiographicalAgent("test_bio.db")
    print("✓ Created agent\n")
    
    # Add test data
    print("Adding test data...")
    agent.add_person(
        name="Alan Turing",
        birth_year="1912",
        occupation="Computer Scientist",
        achievement="developing the Turing machine and breaking the Enigma code"
    )
    agent.add_person(
        name="Ada Lovelace",
        birth_year="1815",
        occupation="Mathematician",
        achievement="writing the first computer program"
    )
    print("✓ Added test data\n")
    
    # Test queries
    print("Testing queries...")
    test_questions = [
        "When was Turing born?",
        "What was Ada's occupation?",
        "What did Lovelace achieve?",
        "Tell me about Alan Turing",
        "Who was Ada