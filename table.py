# from flask import Flask, request, jsonify
# import psycopg2
# import requests
# from psycopg2.extras import Json
# from tokens_generate_functions import get_valid_access_token
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_openai import ChatOpenAI
# import os
# from dotenv import load_dotenv
# load_dotenv()
# from flask_cors import CORS


# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# app = Flask(__name__)
# CORS(app)

# # Configuration for Zoho API and database
# ZOHO_API_URL = "https://www.zohoapis.com/crm/v2/Leads"
# DB_CONFIG = {
#     "dbname": os.getenv("DB_NAME"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "host": os.getenv("DB_HOST"),
#     "port": int(os.getenv("DB_PORT", 5432)),  
# }



# def create_table():
#     """Create the uploaded_leads table."""
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS uploaded_leads (
#                 id SERIAL PRIMARY KEY,
#                 record_id VARCHAR(50),
#                 Lead_Status VARCHAR(50),
#                 Email VARCHAR(100),
#                 quotation_pdf BYTEA,
#                 invoice_pdf BYTEA,  
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 data JSONB NOT NULL,
#                 pricing JSONB,
#                 estimate_number VARCHAR(50),
#                 invoice_number VARCHAR(50),
#                 approve_status VARCHAR(10) DEFAULT 'no'
#             );
#         """)
#         conn.commit()
#         print("Table 'uploaded_leads' created successfully.")
#     except Exception as e:
#         print(f"Error creating table: {e}")
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()

# # create_table()

# if __name__ == "__main__":
#     create_table()


from flask import Flask, request, jsonify
import psycopg2
import requests
from psycopg2.extras import Json
from tokens_generate_functions import get_valid_access_token
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

print("DB_HOST from env:", os.getenv("DB_HOST"))

required_env_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable {var} is not set")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Configuration for Zoho API and database
ZOHO_API_URL = "https://www.zohoapis.com/crm/v2/Leads"
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
}

def create_table():
    """Create the uploaded_leads table."""
    print("DB_CONFIG:", DB_CONFIG)  # Debug: Print DB_CONFIG to verify env variables
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.uploaded_leads (
                id SERIAL PRIMARY KEY,
                record_id VARCHAR(50),
                Lead_Status VARCHAR(50),
                Email VARCHAR(100),
                quotation_pdf BYTEA,
                invoice_pdf BYTEA,  
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data JSONB NOT NULL,
                pricing JSONB,
                estimate_number VARCHAR(50),
                invoice_number VARCHAR(50),
                approve_status VARCHAR(10) DEFAULT 'no'
            );
        """)
        conn.commit()
        print("Table 'uploaded_leads' created successfully.")
    except Exception as e:
        print(f"Error creating table: {type(e).__name__} - {str(e)}")
        raise  # Re-raise to make errors visible during debugging
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Database connection closed.")

# Call create_table during app initialization
with app.app_context():
    create_table()

if __name__ == "__main__":
    app.run(debug=True)