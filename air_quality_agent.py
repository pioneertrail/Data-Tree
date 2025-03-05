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
        request = request.lower()
        
        # City-specific queries
        if "in" in request:
            for city in ["beijing", "shanghai"]:
                if city in request:
                    return ["City Data", city.title()]
        
        # Basic query parsing
        if "pm2.5" in request or "pm 2.5" in request:
            if "trend" in request:
                return ["Trends", "PM2.5"]
            elif "average" in request or "avg" in request:
                return ["Aggregates", "PM2.5"]
            return ["Pollutant Levels", "PM2.5"]
        elif "pm10" in request or "pm 10" in request:
            return ["Pollutant Levels", "PM10"]
        elif "so2" in request:
            return ["Pollutant Levels", "SO2"]
        elif any(word in request for word in ["cities", "monitored", "monitoring"]):
            return ["Metadata", "City"]
        elif "date" in request or "latest" in request:
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
        """Analyze trends for a specific pollutant."""
        history = self.get_historical_data()
        if not history:
            return {
                "status": "No data available for analysis",
                "pollutant": pollutant,
                "period": f"{days} days"
            }
        
        values = [row[7] if pollutant == "PM2.5" else row[9] if pollutant == "PM10" else row[10] 
                  for row in history]
        
        current = values[-1]
        avg = sum(values) / len(values)
        trend = "increasing" if current > avg else "decreasing" if current < avg else "stable"
        
        return {
            "pollutant": pollutant,
            "period": f"{len(values)} days",
            "current_value": f"{current:.1f} µg/m³",
            "average": f"{avg:.1f} µg/m³",
            "trend": trend,
            "samples": len(values)
        }

    def _format_trend_output(self, trend_data):
        """Format trend analysis output."""
        return (
            f"Trend Analysis for {trend_data['pollutant']}:\n"
            f"  Period: {trend_data['period']}\n"
            f"  Current: {trend_data['current_value']}\n"
            f"  Average: {trend_data['average']}\n"
            f"  Trend: {trend_data['trend'].title()}\n"
            f"  Samples: {trend_data['samples']}"
        ) 