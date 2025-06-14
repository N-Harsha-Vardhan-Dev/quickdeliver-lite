import os 
from dotenv import load_dotenv



class Settings() :
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        # self.MONGO_URL : str = os.getenv("MONGO_URL", "mongodb+srv://harshalearning9:quickdeliver_lite@cluster0.0z5xvfe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # checks in .env file for MONGO_URL, if not found, defaults to localhost

        self.MONGO_URL : str = "mongodb+srv://harshalearning9:quickdeliver_lite@cluster0.0z5xvfe.mongodb.net/quickdeliver"
        self.MONGO_DB : str = os.getenv("MONGO_DB", "quickdeliver")
        print(f"MongoDB URL: {self.MONGO_URL} I m in config.py")
        print(f"MongoDB DB: {self.MONGO_DB} I m in config.py")

settings = Settings()