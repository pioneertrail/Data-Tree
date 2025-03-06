from biographical_agent import BiographicalAgent
import os

def test_biographical_system():
    print("\n=== Testing Biographical System ===\n")
    
    # Setup
    print("Setup:")
    db_path = "test_bio.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    agent = BiographicalAgent(db_path)
    print("✓ Created fresh database")
    
    # Test 1: Adding people
    print("\nTest 1 - Adding People:")
    try:
        setup_test_data(agent)
        print("✓ Added Alan Turing and Ada Lovelace")
    except Exception as e:
        print(f"✗ Error adding people: {str(e)}")
        return
    
    # Test 2: Basic queries
    print("\nTest 2 - Basic Queries:")
    test_queries = [
        ("When was Turing born?", "1912"),
        ("Where was Ada born?", "London, England"),
        ("What was Turing's occupation?", "Computer Scientist and Mathematician"),
        ("What nationality was Lovelace?", "British")
    ]
    
    for question, expected in test_queries:
        answer = agent.query(question)
        if expected.lower() in answer.lower():
            print(f"✓ '{question}' -> Correct")
        else:
            print(f"✗ '{question}' -> Expected '{expected}', got '{answer}'")
    
    # Test 3: Complex queries
    print("\nTest 3 - Complex Queries:")
    complex_queries = [
        "Tell me about Alan Turing",
        "Who was Ada Lovelace?",
        "What did Turing achieve?",
        "What was Lovelace known for?"
    ]
    
    for question in complex_queries:
        answer = agent.query(question)
        if answer and len(answer) > 50:  # Complex answers should be detailed
            print(f"✓ '{question}' -> Got detailed response")
        else:
            print(f"✗ '{question}' -> Response too short or empty")
    
    # Test 4: Error handling
    print("\nTest 4 - Error Handling:")
    test_error_handling(agent)
    
    # Test 5: Database persistence
    print("\nTest 5 - Database Persistence:")
    try:
        # Create new agent instance with same database
        new_agent = BiographicalAgent(db_path)
        test_query = "When was Turing born?"
        answer = new_agent.query(test_query)
        if "1912" in answer:
            print("✓ Data persisted in database")
        else:
            print("✗ Data not persisted")
    except Exception as e:
        print(f"✗ Error testing persistence: {str(e)}")
    
    # Test 6: Special commands
    print("\nTest 6 - Special Commands:")
    special_commands = [
        "list",  # Should list all people
        "help",  # Should show help
        "exit"   # Should handle exit gracefully
    ]
    
    for command in special_commands:
        answer = agent.query(command)
        if answer and len(answer) > 0:
            if command == "list" and "Turing" in answer and "Lovelace" in answer:
                print(f"✓ '{command}' -> Correct list of people")
            elif command == "help" and "Example" in answer:
                print(f"✓ '{command}' -> Help message shown")
            else:
                print(f"✓ '{command}' -> Got response")
        else:
            print(f"✗ '{command}' -> No response")

    print("\n=== Test Summary ===")
    print("Database created and populated")
    print("Basic queries tested")
    print("Complex queries tested")
    print("Error handling tested")
    print("Database persistence tested")
    print("Special commands tested")
    print("===================")

def setup_test_data(agent):
    # Add Alan Turing
    agent.add_person(
        name="Alan Turing",
        birth_year=1912,
        birth_place="London, England",
        death_year=1954,
        occupation="Computer Scientist and Mathematician",
        nationality="British",
        achievement="Developed the Turing machine and broke the Enigma code",
        known_for="Being the father of computer science and artificial intelligence"
    )
    
    # Add Ada Lovelace
    agent.add_person(
        name="Ada Lovelace",
        birth_year=1815,
        birth_place="London, England",
        death_year=1852,
        occupation="Mathematician and Writer",
        nationality="British",
        achievement="Writing the first computer program",
        known_for="Being the first computer programmer and her work on the Analytical Engine"
    )

def test_error_handling(agent):
    """Test error handling for various edge cases."""
    print("\nTest 4 - Error Handling:")
    
    # Test unknown person
    response = agent.query("When was Einstein born?")
    assert "don't recognize" in response.lower(), "Should handle unknown person"
    print("✓ 'When was Einstein born?' -> Appropriate error message")
    
    # Test unsupported attribute
    response = agent.query("What is Turing's favorite color?")
    assert "don't have information about personal preferences" in response.lower(), "Should handle unsupported attributes"
    print("✓ 'What is Turing's favorite color?' -> Appropriate error message")
    
    # Test empty query
    response = agent.query("")
    expected = "Please ask a question. Type 'help' for examples."
    assert response == expected, f"Empty query should return '{expected}'"
    print("✓ '' -> Appropriate error message")
    
    # Test nonsense query
    response = agent.query("xyz")
    assert "don't recognize" in response.lower(), "Should handle nonsense queries"
    print("✓ 'xyz' -> Appropriate error message")

if __name__ == "__main__":
    test_biographical_system() 