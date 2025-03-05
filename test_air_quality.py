import pandas as pd
from air_quality_agent import AirQualityAgent
import textwrap

def test_air_quality_agent():
    print("Starting AirQualityAgent tests...\n")
    
    # Create test data
    test_data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'City': ['Beijing', 'Shanghai', 'Beijing'],
        'PM2.5': [35.0, 42.0, 38.0],
        'PM10': [70.0, 85.0, 75.0],
        'SO2': [8.0, 10.0, 9.0]
    }
    
    # Save test data to CSV
    df = pd.DataFrame(test_data)
    df.to_csv('test_air_quality.csv', index=False)
    print("✓ Created test dataset\n")
    
    # Create agent
    agent = AirQualityAgent('test_air_quality.csv')
    print("✓ Created agent\n")
    
    # Test queries
    print("Testing queries...")
    test_questions = [
        "What is the current PM2.5 level?",
        "What's the average PM2.5?",
        "What is the PM10 level?",
        "What is the SO2 level?",
        "Which cities are being monitored?",
        "What's the latest data date?",
        "What's the PM2.5 trend?",
        "What's the air quality in Beijing?",
    ]
    
    # Print with proper formatting
    for question in test_questions:
        print(f"\nQ: {question}")
        answer = agent.query(question)
        # Wrap text to 80 characters and indent continuation lines
        wrapped_answer = textwrap.fill(str(answer), width=80, subsequent_indent='   ')
        print(f"A: {wrapped_answer}")
        print("-" * 80)
    
    # Test trend analysis
    print("\nTesting trend analysis...")
    trend = agent.analyze_trends("PM2.5")
    print(agent._format_trend_output(trend))
    
    print("\nTests completed.")

if __name__ == "__main__":
    test_air_quality_agent() 