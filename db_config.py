import os
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host"     : "localhost",
    "user"     : "root",
    "password" : os.getenv(DB_PASSWORD),  
    "database" : "parking_db"
}
