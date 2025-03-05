import pandas as pd
from datetime import datetime
from memory_manager import AirQualityMemory

class AirQualityAgent:
    def __init__(self, dataset_path=None):
        """Initialize the AI agent with a memory system.
        
        Args:
            dataset_path (str, optional): Path to the air quality dataset CSV
        """
        self.memory = AirQualityMemory()
        if dataset_path:
            self.load_dataset(dataset_path)

    def load_dataset(self, path):
        """Load data from a CSV file into memory.
        
        Args:
            path (str): Path to the CSV file
        """
        df = pd.read_csv(path)
        
        # Process each row
        for _, row in df.iterrows():
            # Convert date to components
            date = pd.to_datetime(row['Date'])
            year, month, day = date.year, date.month, date.day
            
            # Calculate PM2.5 trend (simple difference from previous day)
            trend = "+0"  # Default trend
            
            # Construct user string
            user_string = (
                f"{row['City']},North,{year},{month},{day},S123,"
                f"{row['PM2.5']},{trend},{row['PM10']},{row['SO2']},"
                f"{row['PM2.5']},Monthly"  # Using PM2.5 as monthly average for simplicity
            )
            
            # Store with timestamp
            self.memory.store(user_string, date.isoformat())

    def query(self, request):
        """Process a natural language query and retrieve data.
        
        Args:
            request (str): Natural language query
            
        Returns:
            str: Query result
        """
        # Parse the query to determine the path
        path = self._parse_query(request.lower())
        if not path:
            return "I don't understand that query."
        
        # Retrieve the data
        result = self.memory.retrieve(path)
        if result is None:
            return "No data found for that query."
            
        return result

    def _parse_query(self, request):
        """Parse a natural language query into a path.
        
        Args:
            request (str): Natural language query
            
        Returns:
            list: Path components for tree traversal
        """
        # Basic query parsing
        if "pm2.5" in request:
            if "average" in request or "avg" in request:
                return ["Aggregates", "PM2.5", "Value"]
            return ["Pollutant Levels", "PM2.5", "Value"]
        elif "pm10" in request:
            return ["Pollutant Levels", "PM10"]
        elif "so2" in request:
            return ["Pollutant Levels", "SO2"]
        elif "city" in request:
            return ["Metadata", "City", "Name"]
        elif "date" in request:
            return ["Metadata", "Date"]
        
        return None

    def get_historical_data(self, start_date=None, end_date=None):
        """Retrieve historical data within a date range.
        
        Args:
            start_date (str, optional): Start date in ISO format
            end_date (str, optional): End date in ISO format
            
        Returns:
            list: List of historical data points
        """
        return self.memory.get_history(start_date, end_date)

    def analyze_trends(self, pollutant, days=30):
        """Analyze trends for a specific pollutant.
        
        Args:
            pollutant (str): Pollutant name (e.g., "PM2.5")
            days (int): Number of days to analyze
            
        Returns:
            dict: Trend analysis results
        """
        history = self.get_historical_data()
        # This is a placeholder for trend analysis
        # In a real implementation, we would:
        # 1. Extract pollutant values from history
        # 2. Calculate moving averages
        # 3. Detect patterns and anomalies
        # 4. Return insights
        return {
            "pollutant": pollutant,
            "period": f"{days} days",
            "status": "Analysis not implemented yet"
        } 