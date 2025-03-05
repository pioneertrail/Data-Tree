from biographical_agent import BiographicalAgent

def test_biographical_agent():
    print("Starting BiographicalAgent tests...\n")
    
    try:
        # Create agent
        agent = BiographicalAgent("test_bio.db")
        print("✓ Created agent")
        
        # Add test data
        print("\nAdding test data...")
        agent.add_person(
            name="Alan Turing",
            birth_year="1912",
            occupation="Computer Scientist"
        )
        agent.add_person(
            name="Ada Lovelace",
            birth_year="1815",
            occupation="Mathematician"
        )
        print("✓ Added test data")
        
        # Test queries
        print("\nTesting queries...")
        
        test_questions = [
            "When was Turing born?",
            "What was Ada's occupation?",
            "What did Lovelace do?",
            "When was Alan born?",
            "What was xyz's occupation?",  # Should handle unknown person
            "What is Turing's favorite color?"  # Should handle unknown field
        ]
        
        for question in test_questions:
            print(f"\nQ: {question}")
            print(f"A: {agent.query(question)}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_biographical_agent() 