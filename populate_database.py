from biographical_agent import BiographicalAgent

def populate_database():
    agent = BiographicalAgent()
    
    # Add historical figures
    agent.add_person(
        name="Alan Turing",
        birth_year="1912",
        birth_place="London, England",
        death_year="1954",
        death_place="Wilmslow, England",
        occupation="Computer Scientist and Mathematician",
        achievement="inventing the Turing machine, breaking the Enigma code, and pioneering artificial intelligence",
        education="King's College, Cambridge",
        nationality="British",
        known_for="Being the father of computer science and artificial intelligence"
    )
    
    agent.add_person(
        name="Ada Lovelace",
        birth_year="1815",
        birth_place="London, England",
        death_year="1852",
        death_place="Marylebone, London",
        occupation="Mathematician and Writer",
        achievement="writing the first computer program and recognizing that computers could go beyond mere calculation",
        education="Private tutoring in mathematics and science",
        nationality="British",
        known_for="Being the world's first computer programmer"
    )
    
    agent.add_person(
        name="Grace Hopper",
        birth_year="1906",
        birth_place="New York City, USA",
        death_year="1992",
        death_place="Arlington, Virginia",
        occupation="Computer Scientist and Navy Rear Admiral",
        achievement="developing the first compiler and pioneering computer programming",
        education="Yale University",
        nationality="American",
        known_for="Developing COBOL and finding the first computer 'bug'"
    )
    
    agent.add_person(
        name="John von Neumann",
        birth_year="1903",
        birth_place="Budapest, Hungary",
        death_year="1957",
        death_place="Washington, D.C.",
        occupation="Mathematician and Physicist",
        achievement="developing the von Neumann architecture for computers",
        education="University of Budapest",
        nationality="Hungarian-American",
        known_for="Contributing to quantum mechanics, economics, and computer science"
    )

    print("Database populated with historical figures!")

if __name__ == "__main__":
    populate_database() 