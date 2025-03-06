from memory_manager import BiographicalMemory

def test_biographical_memory():
    print("Starting BiographicalMemory tests...")
    
    # Create memory manager
    memory = BiographicalMemory("test_bio.db")
    print("✓ Created memory manager")
    
    # Test data
    turing_data = {
        'name': 'Alan Turing',
        'birth_year': 1912,
        'occupation': 'Computer Scientist'
    }
    
    lovelace_data = {
        'name': 'Ada Lovelace',
        'birth_year': 1815,
        'occupation': 'Mathematician'
    }
    
    # Store test data
    print("\nStoring test data...")
    memory.store('Alan Turing', turing_data)
    memory.store('Ada Lovelace', lovelace_data)
    print("✓ Stored test data")
    
    # Test retrieval
    print("\nTesting retrieval...")
    
    # Test Turing data
    birth_year = memory.retrieve('Alan Turing', 'birth_year')
    print(f"Turing birth year: {birth_year}")
    assert birth_year == 1912, "Wrong birth year for Turing"
    
    occupation = memory.retrieve('Alan Turing', 'occupation')
    print(f"Turing occupation: {occupation}")
    assert occupation == 'Computer Scientist', "Wrong occupation for Turing"
    
    # Test Lovelace data
    birth_year = memory.retrieve('Ada Lovelace', 'birth_year')
    print(f"Lovelace birth year: {birth_year}")
    assert birth_year == 1815, "Wrong birth year for Lovelace"
    
    occupation = memory.retrieve('Ada Lovelace', 'occupation')
    print(f"Lovelace occupation: {occupation}")
    assert occupation == 'Mathematician', "Wrong occupation for Lovelace"
    
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    test_biographical_memory() 