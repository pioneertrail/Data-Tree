from biographical_agent import BiographicalAgent

def main():
    # Initialize the agent
    print("Initializing Biographical Agent...")
    agent = BiographicalAgent()
    
    # Add example data
    print("\nAdding biographical data...")
    
    # Ada Lovelace
    agent.add_person(
        name="Augusta Ada King",
        known_as="Ada Lovelace",
        birth_year="1815",
        birth_place="London",
        occupation="Mathematician and Computer Pioneer",
        main_work="First Computer Program",
        work_year="1843",
        awards="Ada programming language named after her",
        impact="First computer programmer",
        references="Multiple"
    )
    
    # Alan Turing
    agent.add_person(
        name="Alan Mathison Turing",
        known_as="Alan Turing",
        birth_year="1912",
        birth_place="London",
        occupation="Computer Scientist and Cryptanalyst",
        main_work="Turing Machine",
        work_year="1936",
        awards="OBE, FRS",
        impact="Father of Computer Science",
        references="Multiple"
    )
    
    # Test specific queries
    queries = [
        "What was Ada Lovelace's occupation?",
        "When was Turing born?",
        "What was Lovelace's main work?",
        "What was Turing's impact?"
    ]
    
    print("\nTesting queries...")
    for query in queries:
        print(f"\nQuery: {query}")
        result = agent.query(query)
        print(f"Result: {result}")
        
    # Add some interactive testing
    print("\nYou can now ask your own questions (type 'exit' to quit):")
    while True:
        query = input("\nYour question: ")
        if query.lower() == 'exit':
            break
        result = agent.query(query)
        print(f"Answer: {result}")

if __name__ == "__main__":
    main() 