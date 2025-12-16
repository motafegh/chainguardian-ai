"""
Test PostgreSQL connection from Python
"""
import psycopg2
from psycopg2 import OperationalError

def test_connection():
    """
    Test if we can connect to PostgreSQL database.
    
    🎓 This is like testing if you can connect to an Ethereum node
    Similar to: web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    """
    try:
        # Connection parameters
        # 🎓 Think of this like your .env file for Alchemy/Infura
        connection = psycopg2.connect(
            host="localhost",        # Where database is running
            port=5432,               # PostgreSQL default port
            database="chainguardian", # Database name we created
            user="chainguardian_user", # Username we created
            password="2220128"        # Password you set
        )
        
        # Create cursor (🎓 like web3.eth - lets you execute commands)
        cursor = connection.cursor()
        
        # Test query (🎓 like web3.eth.get_block_number())
        cursor.execute("SELECT version();")
        
        # Fetch result
        db_version = cursor.fetchone()
        
        print("✅ SUCCESS! Connected to PostgreSQL")
        print(f"📊 Database version: {db_version[0]}")
        
        # Close connections (🎓 like closing websocket)
        cursor.close()
        connection.close()
        
        return True
        
    except OperationalError as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Check PostgreSQL is running: sudo service postgresql status")
        print("2. Check password is correct: '2220128'")
        print("3. Check user exists: sudo -u postgres psql -c '\\du'")
        return False

if __name__ == "__main__":
    test_connection()