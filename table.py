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
load_dotenv()
from flask_cors import CORS


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Configuration for Zoho API and database
ZOHO_API_URL = "https://www.zohoapis.com/crm/v2/Leads"
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": 5432,
}



def create_table():
    """Create the uploaded_leads table."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_leads (
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
        print(f"Error creating table: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

create_table()

