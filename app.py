from http import client
from flask import Flask, request, jsonify,render_template_string
import psycopg2
import psycopg2.extras
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import openai
import json
import psycopg2
from datetime import datetime,timedelta
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

with open('data.json', 'r') as f:
    PRICING_DATA = json.load(f)

BACKEND_URL = os.getenv("BACKEND_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Configuration for Zoho API and database
ZOHO_API_URL = "https://www.zohoapis.com/crm/v7/Leads"
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),  # fallback to 5432 if not set
}

def generate_estimate_number():
    random_digits = random.randint(100000, 999999)  
    return f"EST-{random_digits}"

print(generate_estimate_number())

def generate_invoice_number():
    random_digits = random.randint(100000, 999999) 
    return f"INV-{random_digits}"

print(generate_invoice_number())

def save_to_database(record_id, email, lead_data, lead_status):

    print('helllloooo#############################')
    """
    Save lead information to the database with Lead Status
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        estimate_number = generate_estimate_number()
        invoice_number = generate_invoice_number()

        formatted_lead_data = {
            "First_Name": lead_data["First_Name"],
            "Last_Name": lead_data["Last_Name"],
            "Email": lead_data["Email"],
            "Mobile": lead_data["Mobile"],
            "Email_status": {
                "Send_Quotation_Email": "no",
                "Received_Quotation_Email": "no"
            },
            "Security_Need_Reason": lead_data["Security_Need_Reason"],
            "Company_Name": lead_data["Company_Name"],
            "Company_Address": lead_data["Company_Address"],
            "Security_Type": lead_data["Security_Type"],
            "Location_Serviced": lead_data["Location_Serviced"],
            "Start_Date": lead_data["Start_Date"],
            "End_Date": lead_data["End_Date"],
            "Start_Time": lead_data["Start_Time"],
            "End_Time": lead_data["End_Time"],
            "Indoor_Or_Outdoor": lead_data["Indoor_Or_Outdoor"],
            "Alcohol_Present": lead_data["Alcohol_Present"],
            "Job_Description": lead_data["Job_Description"],
            "No_of_guards": lead_data["How many guards?"],
            "State": lead_data["State"]  # Added State to database storage
        }
        print(formatted_lead_data["No_of_guards"])

        cursor.execute(
            """
            INSERT INTO uploaded_leads (data, email, record_id, Lead_Status, estimate_number, invoice_number)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [Json(formatted_lead_data), email, record_id, lead_status, estimate_number, invoice_number]
        )

        conn.commit()
        return True
    except Exception as e:
        print("Database error:", str(e))
        return False
    finally:
        if conn:
            conn.close()



@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    try:
        data = request.json

        print("DATA-----",data)
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        location_serviced = data.get("Location_Serviced", "Not Provided")
        print("Extracted Location_Serviced:", location_serviced)
        
      
        result_obj = "QUALIFY"
        # print(result_obj,"==========")


        if result_obj == "QUALIFY":
            print("Qualify==============")

            zoho_lead = {
                "First_Name": data.get("First_Name"),
                "Last_Name": data.get("Last_Name"),
                "Email": data.get("Email"),
                "Lead_Status": "Qualify",
                "Mobile": data.get("Mobile"),
                "Description": data.get("Job_Description"),
                "Services Needed": data.get("Security_Type"),
                "Company": data.get("Company_Name"),
                "Dates and Hours": data.get("Start_Date"),
                "Date/Time 4": data.get("Start_Time"),
                "Service Loc Buisness Name": data.get("Location_Serviced"),
                
            }

  
            access_token = get_valid_access_token()
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                ZOHO_API_URL, 
                headers=headers, 
                json={"data": [zoho_lead]}
            )

            print(response.status_code,'0000000##')
            
            if response.status_code == 201:
                record_id = response.json()["data"][0]["details"]["id"]
                email = data['Email']

                print('########',record_id)

                save_to_database(record_id, data["Email"], data, lead_status="Qualify")
        
                generate_quotation(record_id)  # Call generate_quotation() here


                send_quotation(record_id)  
                

                print('"Lead submitted, quotation generated and sent successfully"')
                return jsonify({
                    "message": "Lead submitted successfully",
                    "record_id": record_id
                }), 201
            else:
                print("Zoho API error:", response.json())
                return jsonify({
                    "message": "Zoho API error",
                    "error": "Failed to submit lead to Zoho",
                    "details": response.json()
                }), response.status_code

        else: 
            print('Not qualify=========')

            save_to_database(None, data["Email"], data, lead_status="Not Qualify")
            return jsonify({
                "message": "Not Qualify Location Serviced not belongs to the United States"
            }), 201
        

    except Exception as e:
        print("Error:", str(e))
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500


#======================Generate Quotation=============================


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
import textwrap
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def wrap_text(text, width=40):
    """Wrap text to specified width."""
    return textwrap.fill(text, width=width)


def setup_llm():
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    openai.api_key = OPENAI_API_KEY
    return ChatOpenAI(model='gpt-4o-mini',temperature=0.1,openai_api_key = openai.api_key)

# calculate function
def calculate_total_cost(lead_data):

    state = lead_data.get("State", "")
    security_type = lead_data.get("Security_Type", "")
    num_guards = int(lead_data.get("No_of_guards", "1"))

    # Dates
    start_date = datetime.strptime(lead_data["Start_Date"], "%Y-%m-%d")
    end_date = datetime.strptime(lead_data["End_Date"], "%Y-%m-%d")



    # Time (with fallback between 12-hour and 24-hour)
    dummy_date = datetime(2000, 1, 1)
    try:
        start_time = datetime.strptime(lead_data["Start_Time"], "%I:%M %p")
        end_time = datetime.strptime(lead_data["End_Time"], "%I:%M %p")
    except ValueError:
        start_time = datetime.strptime(lead_data["Start_Time"], "%H:%M")
        end_time = datetime.strptime(lead_data["End_Time"], "%H:%M")



    start_dt = dummy_date.replace(hour=start_time.hour, minute=start_time.minute)
    end_dt = dummy_date.replace(hour=end_time.hour, minute=end_time.minute)

    # Handle overnight shifts
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    daily_hours = round((end_dt - start_dt).total_seconds() / 3600, 2)

    count = (end_date - start_date).days + 1

    # Hourly Rate from PRICING_DATA based on state & security type
    base_hourly_rate = 0
    for territory in PRICING_DATA.values():
        if state in territory:
            pricing = territory[state]
 
            security_type_map = {
                "Unarmed": "Unarmed",
                "Armed": "Armed",
                "Firewatch": "Firewatch",
                "Body Guard Unarmed": "Body Guard Unarmed",
                "Body Guard Armed": "Body Guard Armed",
                "Body Guard with Suit": "Body Guard with Suit",
                "Employee Termination": "Employee Termination"
            }
            pricing_key = security_type_map.get(security_type, "")

            if pricing_key and pricing_key in pricing:
                base_hourly_rate = pricing[pricing_key]

                if isinstance(base_hourly_rate, str) and '-' in base_hourly_rate:
                    base_hourly_rate = float(base_hourly_rate.split('-')[0].replace('$', '').strip())
                break

    # Total Hours and Cost
    total_hours = daily_hours * num_guards * count
    subtotal = round(base_hourly_rate * total_hours, 2)

    if state == "Florida":
        tax_rate = 0.07
        tax_amount = round(subtotal * tax_rate, 2)
    else:
        tax_amount=0

    total = round(subtotal + tax_amount, 2)

    # Tax
    # tax_rate = 0.07 if state == "Florida" else 1
    # tax_amount = round(subtotal * tax_rate, 2)
    # total = round(subtotal + tax_amount, 2)

    return {
        "Hourly_Rate": base_hourly_rate,
        "Count": count,
        "Daily_Hours": daily_hours,
        "Total_Hours": total_hours,
        "No_of_Guards": num_guards,
        "Subtotal": subtotal,
        # "Florida (7%)": tax_rate,
        "Florida (7%)": tax_amount,
        "Total": total
    }

def generate_ai_response(lead_data, record_id):
    extracted_data = {
        "Company_Name": lead_data.get("Company_Name", ""),
        "First_Name": lead_data.get("First_Name", ""),
        "Last_Name": lead_data.get("Last_Name", ""),
        "Mobile": lead_data.get("Mobile", ""),
        "Email": lead_data.get("Email", ""),
        "Security_Type": lead_data.get("Security_Type", ""),
        "Job_Location": lead_data.get("Location_Serviced", ""),
        "Start_Date": lead_data.get("Start_Date", ""),
        "End_Date": lead_data.get("End_Date", ""),
        "Start_Time": lead_data.get("Start_Time", ""),
        "End_Time": lead_data.get("End_Time", ""),
        "Job_Type": lead_data.get("Indoor_Or_Outdoor", ""),
        "Alcohol_On_Site": lead_data.get("Alcohol_Present", ""),
        "Specific_Duties": lead_data.get("Job_Description", ""),
        "No_of_guards": lead_data.get("How many guards?", ""),
        "State": lead_data.get("State", "")  # Added State
    }
    
    pricing = calculate_total_cost(lead_data)

    extracted_data["pricing"] = pricing
    
    try:
        pricing_json = json.dumps(pricing)
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
   
        cursor.execute("""
            UPDATE uploaded_leads
            SET pricing = %s::jsonb
            WHERE record_id = %s
            RETURNING pricing;
        """, (pricing_json, record_id))
        
        updated_record = cursor.fetchone()
        conn.commit()
        
        if updated_record:
            print(f"Pricing data updated successfully for record_id {record_id}.")
            print("Updated Pricing in Database:", updated_record[0])
    
    except Exception as e:
        print("Database Error:", e)
    
    finally:
        cursor.close()
        conn.close()
    
    return extracted_data


def fetch_leads():
    """Fetch leads requiring quotations."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT record_id, data 
        FROM uploaded_leads 
        WHERE 
            data->'status'->>'Send_Questionnaire_Email' = 'yes' AND 
            data->'status'->>'Received_Questionnaire_Email' = 'yes' AND 
            data->'status'->>'Generate_Quotation'= 'no'
        """)
        leads = cursor.fetchall()
        return leads, conn, cursor
    except Exception as e:
        raise ValueError(f"Error fetching leads from database: {str(e)}")

def update_lead(cursor, conn, lead_data, record_id):
    """Update lead data in the database."""
    try:
        cursor.execute("""
        UPDATE uploaded_leads
        SET data = %s
        WHERE record_id = %s
        """, [Json(lead_data), record_id])
        conn.commit()
    except Exception as e:
        raise ValueError(f"Error updating lead in database: {str(e)}")
    

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def wrap_text(text, width):
    """Wrap text to specified width."""
    return '\n'.join(textwrap.fill(line, width) for line in text.split('\n'))

def create_quotation_pdf(ai_response,estimate_number):
    print('#0#0#0#0#0#0',ai_response,estimate_number)
    """Generate a PDF quotation based on AI response and return as binary."""
    try:
        ai_response = json.loads(ai_response) if isinstance(ai_response, str) else ai_response
        ai_responses = {key: (value if value is not None else "") for key, value in ai_response.items()}
        pricing = ai_responses.get('pricing', {})
        print('=====',ai_response)
        #print(pricing)

      
        buffer = BytesIO()

        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add logo
        logo_path = "logo.png"  # Update this path to your logo file location
        c.drawImage(logo_path, 40, 710, width=140, height=60, mask='auto')
        
        # Company Header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 695, "Fast Guard Service World Wide")
        c.setFont("Helvetica", 10)
        c.drawString(40, 680, "844-254-8273")
        c.drawString(40, 665, "https://fastguardservice.com/")
        c.drawString(40, 650, "925 S 21 AVE")
        c.drawString(40, 635, "HOLLYWOOD, Florida, 33020")
        
        # Estimate Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(450, 730, "Estimate")
        c.setFont("Helvetica", 10)
        c.drawString(450, 715, estimate_number)
        
        # Bill To Section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 605, "Bill To")
        c.setFont("Helvetica", 10)
        c.drawString(40, 590, f"{ai_responses.get('First_Name', '')} {ai_responses.get('Last_Name', '')}")
        c.drawString(40, 575, f"{ai_responses.get('Company_Name', '')}")
        c.drawString(40, 560, ai_responses.get('Company_Address', ''))
        # c.drawString(40, 560, ai_response.get('Street', ''))
        # c.drawString(40, 545, f"{ai_response.get('City', '')}, {ai_response.get('State', '')} {ai_response.get('Zip_Code', '')}")
        # c.drawString(40, 530, ai_response.get('Country', ''))
        
        # Service Address
        # c.setFont("Helvetica-Bold", 10)
        # c.drawString(40, 495, "Service Address")
        # c.setFont("Helvetica", 10)
        # job_location = wrap_text(ai_response.get('Job_Location', ''), width=40)
        # c.drawString(40, 480, job_location)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 495, "Service Address")

        c.setFont("Helvetica", 10)
        job_location = ai_responses.get('Job_Location', '')

        # Wrap text to ensure it fits properly
        wrapped_text = wrap_text(job_location, width=40)

        # Create a text object for multi-line support
        text_object = c.beginText(40, 480)  # Set starting position
        text_object.setFont("Helvetica", 10)

        # Add each line separately
        for line in wrapped_text.split("\n"):
            text_object.textLine(line)

        c.drawText(text_object)
        
        # Estimate Details
        c.drawString(450, 510, "Estimate Date:")
        c.drawString(530, 510, datetime.now().strftime("%d.%m.%Y"))
        c.drawString(450, 495, "Reference#:")
        c.drawString(530, 495, "Service Past")

        # Prepare table data with proper line breaks
        duties = wrap_text(ai_responses.get('Specific_Duties', ''), width=50)
        description = (
            f"Number of Guards: {pricing.get('No_of_Guards', '')} "
            f"Security Type: {ai_responses.get('Security_Type', '')}\n"
            f"Duration: {pricing.get('Count', '')} Days\n"
            f"Date: {ai_responses.get('Start_Date', '')} - {ai_responses.get('End_Date', '')}\n"
            # f"Duties: {duties}\n"
            # f"Location: {job_location}"
        )
        
        # Create table data with column headers
        data = [
            ['#', 'Item & Description', 'Duration', 'Count', 'Hourly\nRate', 'Number of\nguards', 'Hours per\nday', 'Amount'],
            ['1', description, 'Daily', 
             str(pricing.get('Count', '')), 
             f"${pricing.get('Hourly_Rate', '')}",
             str(pricing.get('No_of_Guards', '')),
             str(pricing.get('Daily_Hours', '')),
             f"${pricing.get('Subtotal', ''):.2f}"]
        ]
        # Set column widths
        col_widths = [20, 240, 45, 35, 45, 45, 45, 45]
        table = Table(data, colWidths=col_widths)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, 1), 'CENTER'),
            ('ALIGN', (1, 1), (1, 1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEADING', (1, 1), (1, 1), 12),
        ])
        table.setStyle(style)
        
        # Draw table on the canvas
        table.wrapOn(c, 40, 40)
        table.drawOn(c, 40, 300)
        
    

        total_hours = pricing.get('Total_Hours', 0)  # Get Total Hours
        total_amount = pricing.get('Subtotal', 0)   # Get Sub Total (which will be same as Sub Total)
        total_taxable_amount = pricing.get('Subtotal', 0)
        florida_tax = pricing.get('Florida (7%)', 0)  # Get Florida Tax (7%)
        total = pricing.get('Total', 0)  # Get Total

        # Add Total Hours
        c.setFont("Helvetica", 10)
        c.drawString(40, 100, f"Total Hours: {total_hours}")
     
        c.drawString(400, 100, "Sub Total")
        c.drawString(520, 100, f"{total_amount:,.2f}")

        c.drawString(400, 85, "Total Taxable Amount")
        c.drawString(520, 85, f"{total_amount:,.2f}")

        # Add Florida Tax (7%), adjust y-position further down
        c.drawString(400, 70, "Florida (7%)")
        c.drawString(520, 70, f"{florida_tax:,.2f}")


        # Add Total after Florida Tax
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, 60, "Total")
        c.drawString(520, 60, f"{total:,.2f}$")
        
        # Thank you note
        c.setFont("Helvetica", 10)
        c.drawString(40, 40, "Thank you!")

        # Start new page for Notes
        c.showPage()
        
        # Notes section on new page
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 750, "Notes")
        
        # Referral program text
        c.setFont("Helvetica", 10)
        text = ("We're thrilled to introduce a referral program that rewards you for recommending our services. "
               "For every referral that turns into a 40-hour contract or more, you'll receive 8 free hours of security service "
               "or a 5% cash reward. Would you like to participate and start saving on your security needs while helping others?")
        
        # Wrap and draw referral text
        wrapped_text = wrap_text(text, width=85)
        textobject = c.beginText()
        textobject.setTextOrigin(40, 730)
        for line in wrapped_text.split('\n'):
            textobject.textLine(line)
        c.drawText(textobject)
        
        # Free security camera text
        text2 = ("For a limited time, we're providing a FREE 4G security camera with any service of 40 hours or more. "
                "Would you like to learn more about how this can protect your property and save you time and money? "
                "Let's schedule a quick call to discuss your specific needs.")
        
        # Wrap and draw security camera text
        wrapped_text2 = wrap_text(text2, width=85)
        textobject2 = c.beginText()
        textobject2.setTextOrigin(40, 670)
        for line in wrapped_text2.split('\n'):
            textobject2.textLine(line)
        c.drawText(textobject2)
        
        # Add Insurance section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 610, "Add Insurance to Your Invoice")
        
        c.setFont("Helvetica", 10)
        c.drawString(40, 590, "Would you like to enhance your peace of mind with our optional insurance? Here's what it includes:")
        
        # Refund Flexibility section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 560, "1. Refund Flexibility")
        c.setFont("Helvetica", 10)
        c.drawString(55, 545, "Instead of receiving in-store credit for unused services, you'll be eligible for a full refund of the unused portion of")
        c.drawString(55, 530, "your invoice.")
        
        # Draw line under Refund Flexibility section
        # c.line(40, 510, 570, 510)
        
        # Additional Insured Status section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 490, "2. Additional Insured Status")
        c.setFont("Helvetica", 10)
        c.drawString(55, 475, "Your business or entity will be added as an Additional Insured on our $5,000,000 liability insurance policy,")
        c.drawString(55, 460, "ensuring extra protection during your service period.")
        
        # No Credit Card Fees section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 430, "3. No Credit Card Fees")
        c.setFont("Helvetica", 10)
        c.drawString(55, 415, "Opting for this insurance also waives all credit card processing fees associated with your invoice.")
        
        # How It Works section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 385, "How It Works:")
        c.setFont("Helvetica", 10)
       
        text3 = """Simply check the "Add Insurance" box on your invoice to unlock these exclusive benefits. Whether you're safeguarding 
              your investment or boosting liability coverage, this option provides added security and convenience."""
        wrapped_text3 = wrap_text(text3, width=85)
        textobject3 = c.beginText()
        textobject3.setTextOrigin(40, 365)
        for line in wrapped_text3.split('\n'):
            textobject3.textLine(line)
        c.drawText(textobject3)
        
        c.drawString(40, 320, "Let us know if you'd like to take advantage of this valuable service!")
        
        # Add Terms & Conditions section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 280, "Terms & Conditions")
        
        # Terms & Conditions text
        c.setFont("Helvetica", 10)
        terms_conditions = [
            "Any changes to the agreed scope of work may result in additional charges.",
            "If a no-show occurs, you will receive a full refund.",
            "However, if you cancel or reschedule without insurance, a 30% cancellation fee will apply."
        ]
        
        y_position = 260
        for term in terms_conditions:
            c.drawString(40, y_position, term)
            y_position -= 20

        # New third page content
        c.showPage()

        # Refund Flexibility Section on third page
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 750, "Refund Flexibility")
        c.setFont("Helvetica", 10)
        wrapped_text4 = wrap_text("Instead of receiving in-store credit for unused services, you’ll be eligible for a full refund of the unused portion of your invoice.", width=85)
        textobject4 = c.beginText()
        textobject4.setTextOrigin(40, 730)
        for line in wrapped_text4.split('\n'):
            textobject4.textLine(line)
        c.drawText(textobject4)

        # Additional Insured Status
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 700, "Additional Insured Status")
        c.setFont("Helvetica", 10)
        wrapped_text5 = wrap_text("Your business or entity will be added as an Additional Insured on our $5,000,000 liability insurance policy, ensuring extra protection during your service period.", width=85)
        textobject5 = c.beginText()
        textobject5.setTextOrigin(40, 680)
        for line in wrapped_text5.split('\n'):
            textobject5.textLine(line)
        c.drawText(textobject5)

        # No Credit Card Fees
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 650, "No Credit Card Fees")
        c.setFont("Helvetica", 10)
        c.drawString(40, 635, "Opting for this insurance also waives all credit card processing fees associated with your invoice.")

        # How It Works
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 600, "How It Works:")
        c.setFont("Helvetica", 10)
        text3 = """Simply check the "Add Insurance" box on your invoice to unlock these exclusive benefits. Whether you're safeguarding 
        your investment or boosting liability coverage, this option provides added security and convenience."""
        wrapped_text3 = wrap_text(text3, width=85)
        textobject3 = c.beginText()
        textobject3.setTextOrigin(40, 580)
        for line in wrapped_text3.split('\n'):
            textobject3.textLine(line)
        c.drawText(textobject3)

        c.drawString(40, 520, "Let us know if you'd like to take advantage of this valuable service!")

        # Additional Note
        c.setFont("Helvetica", 10)
        c.drawString(40, 500, "Estimate does not secure services! Please call or email (sales@fastguardservice.com) if you would like to move forward.")
        c.drawString(40, 485, "FEEL FREE TO CONTACT US AT 844.254.8273")

        # Credit Card Fee and Debit Card Note
        c.drawString(40, 460, "** There is 3.5% fee for credit card payments. This fee is equivalent to what we pay to accept credit cards.")
        c.drawString(40, 445, "** Please note that there is no fee for using a debit card.")

        # Service and Refund Information
        c.setFont("Helvetica", 10)
        service_refund_text = """FGS has a minimum of 6 hours per shift per guard for Service Nationwide. All of our Services are billed in advance before service is
        rendered via Credit Card or Debit Card. REFUND time frame is 7 - 10 business days."""
        wrapped_service_refund = wrap_text(service_refund_text, width=90)
        textobject6 = c.beginText()
        textobject6.setTextOrigin(40, 420)
        for line in wrapped_service_refund.split('\n'):
            textobject6.textLine(line)
        c.drawText(textobject6)

        # Federal Holidays and Time & a Half Information
        c.setFont("Helvetica", 10)
        holidays_text = """The following Federal Holidays are billed at time and a half: New Year's Day, Memorial Day, Independence Day, Labor Day, Veterans Day,
        Thanksgiving Day, & Christmas Day."""
        wrapped_holidays = wrap_text(holidays_text, width=85)
        textobject7 = c.beginText()
        textobject7.setTextOrigin(40, 380)
        for line in wrapped_holidays.split('\n'):
            textobject7.textLine(line)
        c.drawText(textobject7)            
                
        c.save()
    
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        raise ValueError(f"Error creating PDF: {str(e)}")



def generate_quotation(record_id):

    """Function to generate a quotation PDF for a specific record_id."""
    try:
      
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data,estimate_number 
            FROM uploaded_leads 
            WHERE record_id = %s
        """, (record_id,))
        result = cursor.fetchone()

        if not result:
            return {"error": f"No data found for record_id {record_id}"}, 404

        lead_data, estimate_number = result

        ai_response = generate_ai_response(lead_data,record_id)


  
        # Generate PDF as binary data
        pdf_binary = create_quotation_pdf(ai_response,estimate_number)

        

        if pdf_binary:

            cursor.execute("""
                UPDATE uploaded_leads
                SET quotation_pdf = %s
                WHERE record_id = %s
            """, (psycopg2.Binary(pdf_binary), record_id))
            conn.commit()

            update_lead(cursor, conn, lead_data, record_id)

            print(f"Processed lead {record_id}, created and stored PDF in DB")
            return {"message": "Quotation generated and PDF stored in DB successfully."}, 200

        else:
            return {"error": "Failed to generate PDF."}, 500

    except ValueError as ve:
        return {"error": str(ve)}, 500
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500

    finally:
        # Close the database connection
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



#====================Get Quotation==================

from flask import Flask, send_file, jsonify, request
import psycopg2
import io

@app.route("/get-pdf/<int:record_id>", methods=["GET"])
def get_pdf(record_id):
    """Retrieve PDF for a given lead record_id."""
    try:
     
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT quotation_pdf 
            FROM uploaded_leads 
            WHERE record_id::varchar = %s
            """, (str(record_id),))

   
        result = cursor.fetchone()

   
        if not result or result[0] is None:
            return jsonify({"error": "PDF not found for this lead"}), 404

        pdf_data = result[0]
        
    
        pdf_file = io.BytesIO(pdf_data)
        
        return send_file(pdf_file, mimetype="application/pdf", as_attachment=True, download_name=f"quotation_{record_id}.pdf")

    except Exception as e:
        return jsonify({"error": f"Error fetching PDF: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()





#=====================Send Quotation======================


def upload_pdf_binary_to_zoho(pdf_binary):
    """Uploads a PDF binary to Zoho and returns the file ID."""
    try:
        access_token = get_valid_access_token()
        upload_url = "https://www.zohoapis.com/crm/v7/files"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

        # Use BytesIO to handle the binary data
        with BytesIO(pdf_binary) as file:
            files = {"file": ("quotation.pdf", file, "application/pdf")}
            response = requests.post(upload_url, headers=headers, files=files)

        if response.status_code == 200:
            return response.json()["data"][0]["details"]["id"]
        else:
            raise ValueError(f"Failed to upload PDF: {response.text}")
    except Exception as e:
        raise ValueError(f"Error uploading PDF to Zoho: {e}")


# send mail with attachment and approval button when user click then we get user's email

import requests

def send_mail_with_attachment(recipient_name, recipient_email, lead_id, file_id):
    print('---11111111111111111----',recipient_email,recipient_name,lead_id,file_id)
    """Sends an email with a PDF attachment using Zoho."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Fetch `data` and `pricing` for the given email
        query = """
            SELECT pricing,estimate_number
            FROM uploaded_leads 
            WHERE record_id = %s
        """
        cursor.execute(query, (lead_id,))
        
        result = cursor.fetchone()
        # print(result,'---result<<<<<<<<<<<<<<<<<<<<')
        if result:
            pricing_data, estimate_number = result
            # pricing_data = result[0] 
            # print(pricing_data) # Extract dictionary
            total_price = pricing_data.get('Total', 0)  
            formatted_total = f"{total_price:,.2f}"
            print(formatted_total,estimate_number)  
        else:
            formatted_total = "$0.00" 
            print(result) 

        access_token = get_valid_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
        }

        # Updated HTML content
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <!-- Header with estimate number -->
            <div style="background-color: #4a90e2; color: white; padding: 20px; text-align: center;">
                Estimate #{{estimate_number}}
            </div>

            <!-- Main content -->
            <div style="padding: 20px;">
                <p>Dear {{recipient_name}},</p>

                <p style="line-height: 1.6; color: #333;">
                Thank you for choosing Fast Guard Service for your security needs, we appreciate the 
                opportunity to earn your business. Attached you will find your estimate. We will need to know if 
                you plan to move forward with us as soon as possible to keep your desired shift(s) available on 
                our schedule. To approve this estimate simply click the view estimate link below and click accept 
                on the upper right-hand side of the estimate. After clicking accept, an invoice will be emailed to 
                you where you can then process payment and lock your spot on the schedule. Your estimate can 
                also be printed and downloaded as a PDF from the "view estimate" link below (a pdf copy is 
                attached as well).
                </p>

                <!-- Estimate box -->
                <div style="background-color: #f9f9f9; border: 1px solid #e0e0e0; padding: 20px; margin: 20px 0; border-radius: 4px;">
                    <!-- Amount section -->
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="text-transform: uppercase; color: #333; font-size: 14px; margin-bottom: 5px;">
                            ESTIMATE AMOUNT
                        </div>
                        <div style="color: #ff0000; font-size: 24px; font-weight: bold;">
                            ${{formatted_total}}
                        </div>
                    </div>

                    <!-- Details table -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                            <td style="padding: 8px; color: #333; text-align: center;">Estimate No: {{estimate_number}}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; color: #333;  text-align: center;">Estimate Date: 02.13.2025</td>
                        </tr>
                    </table>

                    <!-- View estimate button -->
                    <div style="text-align: center;">
                        <a href="{{backend_url}}/approve?email={{recipient_email}}&record_id={{lead_id}}"
                        style="display: inline-block; padding: 10px 30px; background-color: #76d275; 
                                color: white; text-decoration: none; border-radius: 4px; font-size: 14px;
                                text-transform: uppercase;">
                            Approve
                        </a>
                    </div>
                </div>

                <!-- Signature -->
                <p style="color: #666; margin-top: 30px;">
                    Regards,<br>
                    Roderick Payne<br>
                    Fast Guard Service World Wide<br>
                    Direct Line: (888) - 558-2020
                </p>
            </div>
        </div>
        """

        
        html_content = html_content.replace("{{recipient_name}}", recipient_name)
        html_content = html_content.replace("{{recipient_email}}", recipient_email)
        html_content = html_content.replace("{{formatted_total}}", formatted_total)
        html_content = html_content.replace("{{estimate_number}}", estimate_number)
        html_content = html_content.replace("{{backend_url}}", BACKEND_URL)
        html_content = html_content.replace("{{lead_id}}", lead_id)

       
        url = f"https://www.zohoapis.com/crm/v7/Leads/{lead_id}/actions/send_mail"

       
        payload = {
            "data": [
                {

                    "from": {"user_name": "Sales", "email": "rod@fastguardservice.com"},
                    "to": [{"user_name": recipient_name, "email": recipient_email}],
                    "reply_to": {"user_name": "Sales", "email": "rod@fastguardservice.com"},
                    "subject": "Quotation for Security Services",
                    "content": html_content, 
                    "mail_format": "html",
                    "attachments": [{"id": file_id}],
                }
            ]
        }
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

      
        response = requests.post(url, headers=headers, json=payload)
        print(response.json(),"sucesssssss==============================")

        response_data = response.json()

        if response.status_code == 200:
            # print('"Lead submitted, quotation generated and sent successfully"')
            return jsonify({
                    "message": "Lead submitted successfully",
                    # "record_id": record_id
            }), 201
        else:
            error_message = response_data.get("data", [{}])[0].get("message", "Unknown error occurred")
            
            if "javax.mail.MessagingException" in error_message:
                print("Invalid Email ID")
                return {"success": False, "error": "Invalid email ID. Please check your email."}
            else:
                return {"success": False, "error": f"Failed to send email .Please again fill the form: {error_message}"}

        # else:
        #     raise ValueError(f"Failed to send email: {response.text}")

    except Exception as e:
        raise ValueError(f"Error sending email. Please again fill the form: {e}")

# update approve status on database
def update_approve_status(record_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        update_query = """
        UPDATE uploaded_leads 
        SET approve_status = 'yes' 
        WHERE record_id = %s
        """
        cursor.execute(update_query, (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error updating approve_status: {e}")

    


@app.route("/approve", methods=["GET"])
def approve_quotation():
    """Handle approval request from email button and process lead details."""
    email = request.args.get("email")
    record_id = request.args.get("record_id")
    print('eeeeeeeeeeeeeeee',email,record_id)

    if not email or not record_id:
        return jsonify({"error": "Email and Record ID are required"}), 400
    # lead = get_lead_by_record_id(record_id)

    # print('llllllllllllll',lead)

    try:
        lead = get_lead_by_record_id(record_id)
        # Fetch the latest lead details

        if not lead:
            return jsonify({"error": "Lead not found"}), 404
    
        update_approve_status(record_id)

        # record_id = lead[0]  # Already have this from request.args, but confirming it matches
        # email = lead[1]      # Verify it matches the email from the URL if needed
        # data = lead[2]       # JSON data containing First_Name, Last_Name, etc.
        record_id = lead[1]
        email = lead[3]      # Email is at index 3
        data = lead[7]       # JSON data is at index 7
        # print('454545454545454',record_id,email,data)
        First_name = data.get('First_Name', '')
        Last_name = data.get('Last_Name', '')


        # update_approve_status(lead_id)
        

        # Send invoice email
        send_invoice_with_attachment(
            email=email,
            lead_id=record_id,
            First_name=First_name,
            Last_name=Last_name,
        )


        return render_template_string("""
            <h2>Quotation Approved Successfully!</h2>
            <p>An invoice has been sent to {{ email }}.</p>
            <a href="https://mail.google.com/mail/u/0/?tab=rm&ogbl#inbox">Go Back</a>
        """, email=email)

    except Exception as e:
        return jsonify({
            "error": f"Error processing approval: {str(e)}"
        }), 500

def get_lead_by_record_id(record_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            SELECT * FROM uploaded_leads
            WHERE record_id = %s
        """
        cursor.execute(query, (record_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error fetching lead by record_id: {e}")
        return None

# send invoice mail

def get_latest_lead_by_email(email):
    
    try:

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        

        query = """
            SELECT record_id, email, data FROM uploaded_leads
            WHERE email = %s
            ORDER BY created_at DESC;
            
        """

        cursor.execute(query, (email,))
        
        result = cursor.fetchone()

        
        return result
        
    except Exception as e:
        print(f"Error fetching lead: {e}")
        return None
        
    finally:

        cursor.close()
        conn.close()



# invoice start
def send_invoice_with_attachment(email, lead_id, First_name, Last_name):
    print(email,lead_id,First_name,Last_name)
    """Sends an invoice email with the updated UI using Zoho."""
    try:
        

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        
        query = """
            SELECT pricing, invoice_number
            FROM uploaded_leads 
            WHERE record_id = %s
        """
        cursor.execute(query, (lead_id,))
        
        result = cursor.fetchone()
        if result:
            pricing_data ,invoice_number = result 
            total_price = pricing_data.get('Total', 0)  
            formatted_total = f"{total_price:,.2f}"
            print(formatted_total,invoice_number)  
        else:
            formatted_total = "$0.00"  
            print(result)  
        

        access_token = get_valid_access_token()

        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json",
        }

        
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <!-- Header with invoice number -->
            <div style="background-color: #d4af37; color: white; padding: 20px; text-align: center; font-size: 18px;">
                Invoice #{{invoice_number}}
            </div>

            <!-- Main content -->
            <div style="padding: 20px;">
                <p>Dear {{First_name}},</p>

                <p style="line-height: 1.6; color: #333;">
                    Thank you for your business. Your invoice can be viewed, printed & downloaded as a PDF, and
                    paid online via the "View Invoice" link below. Once your invoice is paid, all communications are to
                    be conducted through 
                    <a href="mailto:scheduling@fastguardservice.com" style="color: #007bff; text-decoration: none;">
                        scheduling@fastguardservice.com
                    </a> 
                    or call 844.254.8273 (option 2) for scheduling updates.
                </p>

                <!-- Invoice box -->
                <div style="background-color: #fffde7; border: 1px solid #e0e0e0; padding: 20px; margin: 20px 0; border-radius: 4px; text-align: center;">
                    <!-- Amount section -->
                    <div style="text-transform: uppercase; color: #333; font-size: 14px; margin-bottom: 10px;">
                        INVOICE AMOUNT
                    </div>
                    <div style="color: #ff0000; font-size: 24px; font-weight: bold;">
                        ${{formatted_total}}
                    </div>

                    <!-- Details table -->
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <tr>
                            <td style="padding: 8px; color: #333; text-align: center;"><strong>Invoice No:</strong> {{invoice_number}}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; color: #333; text-align: center;"><strong>Invoice Date:</strong> 02.13.2025</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; color: #333; text-align: center;"><strong>Due Date:</strong> 02.13.2025</td>
                        </tr>
                    </table>

                    <!-- View Invoice button -->
                    <div style="margin-top: 20px;">
                        <a href="{{backend_url}}/view_invoice?email={{email}}&record_id={{lead_id}}"
                           style="display: inline-block; padding: 12px 30px; background-color: #4CAF50; 
                                  color: white; text-decoration: none; border-radius: 5px; font-size: 14px;
                                  font-weight: bold;">
                            VIEW INVOICE
                        </a>
                        
                    </div>
                </div>

                <!-- Signature -->
                <p style="color: #666; margin-top: 30px;">
                    Regards,<br>
                    Roderick Payne<br>
                    Fast Guard Service World Wide<br>
                    Direct Line: (888) - 558-2020
                </p>
            </div>
        </div>
        """


        html_content = html_content.replace("{{First_name}}", First_name)
        html_content = html_content.replace("{{email}}", email)
        html_content = html_content.replace("{{formatted_total}}", formatted_total)
        html_content = html_content.replace("{{invoice_number}}", invoice_number)
        html_content = html_content.replace("{{backend_url}}", BACKEND_URL)
        html_content = html_content.replace("{{lead_id}}", lead_id)

        url = f"https://www.zohoapis.com/crm/v7/Leads/{lead_id}/actions/send_mail"


        payload = {
            "data": [ 
                {
                   "from": {"user_name": "Sales", "email": "rod@fastguardservice.com"},
                    "to": [
                        {
                            "user_name": First_name,
                            "email": email
                        }
                    ],
                    "reply_to": {
                        "user_name": "Sales",
                        "email": "rod@fastguardservice.com"
                    },
                    "subject": "Invoice for Security Services",
                    "content": html_content,
                    "mail_format": "html"
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"Email sent successfully to {email}")
            return True
        else:
            error_message = f"Failed to send email: {response.text}"
            print(error_message)
            raise ValueError(error_message)

    except Exception as e:
        error_message = f"Error sending email: {str(e)}"
        print(error_message)
        raise ValueError(error_message)


# now added one line here below

@app.route("/view_invoice", methods=["GET"])
def view_invoice():
    """Retrieve lead data, generate/store PDF if missing, and return the PDF."""
    email = request.args.get("email")
    record_id = request.args.get("record_id")


    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    
    try:
   
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()


  
        query = """
            SELECT data, pricing, invoice_number
            FROM uploaded_leads 
            WHERE record_id = %s
        """
        cursor.execute(query, (record_id,))
        
        result = cursor.fetchone()

        
        if not result:
            return jsonify({"error": "No record found for this email"}), 404

        invoice_data = {"data": result[0], "pricing": result[1],"invoice_number":result[2]}
       

        pdf_binary = create_invoice_pdf(invoice_data)


        if pdf_binary:
          
            cursor.execute("""
                UPDATE uploaded_leads
                SET invoice_pdf = %s
                WHERE record_id = %s
            """, (psycopg2.Binary(pdf_binary), record_id))
            conn.commit()


            pdf_file = io.BytesIO(pdf_binary)


            return send_file(
                pdf_file, 
                mimetype="application/pdf", 
                as_attachment=True, 
                download_name=f"quotation_{email}.pdf"
            )

        return jsonify({"error": "Failed to generate PDF"}), 500

    except Exception as e:
        return jsonify({"error": f"Error fetching record: {str(e)}"}), 500

    finally:
        # Close DB connections
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def wrap_text(text, width):
    """Wrap text to the specified width."""
    return textwrap.fill(text, width)

def create_invoice_pdf(invoice_data):
    print('<<<<<<<<<<<<<<<5555555',invoice_data)

    """Generate a PDF quotation based on AI response and return as binary."""
    try:

        ai_responsess = json.loads(invoice_data) if isinstance(invoice_data, str) else invoice_data
        ai_response = ai_responsess.get('data', {})
        print("00000000000",ai_response)
        pricing = ai_responsess.get('pricing', {})
        invoice_number = ai_responsess.get('invoice_number',{})
        # print(invoice_number,'====')


        # Create a BytesIO object to hold the PDF as binary
        buffer = BytesIO()

        # Create PDF canvas
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add logo
        logo_path = "logo.png"  # Update this path to your logo file location
        c.drawImage(logo_path, 40, 710, width=140, height=60, mask='auto')
        
        # Company Header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 695, "Fast Guard Service World Wide")
        c.setFont("Helvetica", 10)
        c.drawString(40, 680, "844-254-8273")
        c.drawString(40, 665, "https://fastguardservice.com/")
        c.drawString(40, 650, "925 S 21 AVE")
        c.drawString(40, 635, "HOLLYWOOD, Florida, 33020")
        
        # Estimate Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(450, 730, "Invoice")
        c.setFont("Helvetica", 10)
        c.drawString(450, 715, invoice_number)
        

        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 605, "Bill To")
        c.setFont("Helvetica", 10)
        c.drawString(40, 590, f"{ai_response.get('First_Name', '')} {ai_response.get('Last_Name', '')}")
        c.drawString(40, 575, f"{ai_response.get('Company_Name', '')}")
        # c.drawString(40, 560, f"{ai_response.get('Street', '')}")
        # c.drawString(40, 545, f"{ai_response.get('City', '')}, {ai_response.get('State', '')} {ai_response.get('Zip_Code', '')}")
        # c.drawString(40, 530, ai_response.get('Country', ''))
        c.drawString(40,560, ai_response.get('Company_Address'))
        
        # Service Address
        # c.setFont("Helvetica", 10)
        # # c.drawString(40, 495, f"Service Address:{ai_response.get('Location_Serviced','')}")
        # c.drawString(40, 495, "Service Address")  
        # c.drawString(40, 475, ai_response.get('Location_Serviced', ''))
        # c.setFont("Helvetica", 10)
        # job_location = wrap_text(ai_response.get('Job_Location', ''), width=40)
        # c.drawString(40, 480, job_location)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 495, "Service Address")

        c.setFont("Helvetica", 10)
        job_location = ai_response.get('Location_Serviced', '')

        # Wrap text to ensure it fits properly
        wrapped_text = wrap_text(job_location, width=40)

        # Create a text object for multi-line support
        text_object = c.beginText(40, 480)  # Set starting position
        text_object.setFont("Helvetica", 10)

        # Add each line separately
        for line in wrapped_text.split("\n"):
            text_object.textLine(line)

        c.drawText(text_object)
        
        # Estimate Details
        c.drawString(450, 510, "Estimate Date:")
        c.drawString(530, 510, datetime.now().strftime("%d.%m.%Y"))
        c.drawString(450, 495, "Reference#:")
        c.drawString(530, 495, "Service Past")

        # Prepare table data with proper line breaks
        duties = wrap_text(ai_response.get('Specific_Duties', ''), width=50)
        description = (
            f"Number of Guards: {pricing.get('No_of_Guards', '')} "
            f"Security Type: {ai_response.get('Security_Type', '')}\n"
            f"Duration: {pricing.get('Count', '')} Days\n"
            f"Date: {ai_response.get('Start_Date', '')} - {ai_response.get('End_Date', '')}\n"
            f"Duties: {ai_response.get('Job_Description','')}\n"
            f"Location:\n{format_location(ai_response.get('Location_Serviced', ''))}"
        )
        
        # Create table data with column headers
        data = [
            ['#', 'Item & Description', 'Duration', 'Count', 'Hourly\nRate', 'Number of\nguards', 'Total\nhours', 'Amount'],
            ['1', description, 'Daily', 
             str(pricing.get('Count', '')), 
             f"${pricing.get('Hourly_Rate', '')}",
             str(pricing.get('No_of_Guards', '')),
            #  str(pricing.get('Hourly_Rate', '')),
             str(pricing.get('Total_Hours', '')),
             f"${pricing.get('Subtotal', '0.00')}"]
        ]
        
        # Set column widths
        col_widths = [20, 240, 45, 35, 45, 45, 45, 45]
        table = Table(data, colWidths=col_widths)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, 1), 'CENTER'),
            ('ALIGN', (1, 1), (1, 1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEADING', (1, 1), (1, 1), 12),
        ])
        table.setStyle(style)
        
        # Draw table on the canvas
        table.wrapOn(c, 40, 40)
        table.drawOn(c, 40, 300)
        
    

        total_hours = pricing.get('Total_Hours', 0)  
        total_amount = pricing.get('Subtotal', 0)   
        total_taxable_amount = pricing.get('Subtotal', 0)
        florida_tax = pricing.get('Florida (7%)', 0)  
        total = pricing.get('Total', 0)  

        # Add Total Hours
        c.setFont("Helvetica", 10)
        c.drawString(40, 100, f"Total Hours: {total_hours}")
     
        c.drawString(400, 100, "Sub Total")
        c.drawString(520, 100, f"{total_amount:,.2f}")

        c.drawString(400, 85, "Total Taxable Amount")
        c.drawString(520, 85, f"{total_amount:,.2f}")

        # Add Florida Tax (7%), adjust y-position further down
        c.drawString(400, 70, "Florida (7%)")
        c.drawString(520, 70, f"{florida_tax:,.2f}")


        # Add Total after Florida Tax
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, 60, "Total")
        c.drawString(520, 60, f"{total:,.2f}$")
        
        # Thank you note
        c.setFont("Helvetica", 10)
        c.drawString(40, 40, "Thank you!")

        # Start new page for Notes
        c.showPage()
        
        # Notes section on new page
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 750, "Notes")
        
        # Referral program text
        c.setFont("Helvetica", 10)
        start_y = 750 -20
        section_spacing =20

        # Referral Program Text
        text = ("We're thrilled to introduce a referral program that rewards you for recommending our services. "
        "For every contract of 40 hours or more, you'll receive 8 free hours of security service or a 5% cash reward. "
        "Would you like to participate and start saving on your security needs while helping others?")

        wrapped_text = wrap_text(text, width=85)
        textobject = c.beginText()
        textobject.setTextOrigin(40, start_y)
        c.setFont("Helvetica", 10)

        for line in wrapped_text.split('\n'):
            textobject.textLine(line)
        c.drawText(textobject)

        # Update Y position after Referral Program
        current_y = start_y - (len(wrapped_text.split('\n')) * 12) - section_spacing  

        # Free Security Camera Offer Text
        text2 = ("For a limited time, we're providing a FREE 4G security camera with any service of 40 hours or more. "
                "Would you like to learn more about how this can protect your property and save you time and money? "
                "Let's schedule a quick call to discuss your specific needs.")

        wrapped_text2 = wrap_text(text2, width=85)
        textobject2 = c.beginText()
        textobject2.setTextOrigin(40, current_y)
        for line in wrapped_text2.split('\n'):
            textobject2.textLine(line)
        c.drawText(textobject2)

        # Update Y position after Security Camera Offer
        current_y -= (len(wrapped_text2.split('\n')) * 12) + section_spacing  

        # Legal Disclaimer
        legal_text = ("Any dispute or enforcement of this invoice shall be construed and governed exclusively by "
                    "and in accordance with the laws of the State of Florida, Broward County, Florida.")

        wrapped_legal = wrap_text(legal_text, width=85)
        textobject_legal = c.beginText()
        textobject_legal.setTextOrigin(40, current_y)
        for line in wrapped_legal.split('\n'):
            textobject_legal.textLine(line)
        c.drawText(textobject_legal)

        # Update Y position after Legal Disclaimer
        current_y -= (len(wrapped_legal.split('\n')) * 12) + section_spacing  

        # Terms & Conditions Header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, current_y, "Terms & Conditions")

        # Terms & Conditions Content
        c.setFont("Helvetica", 10)
        terms_conditions = [
            "Any changes to the agreed scope of work may result in additional charges.",
            "If a no-show occurs, you will receive a full refund.",
            "However, if you cancel or reschedule without insurance, a 30% cancellation fee will apply."
        ]

        current_y -= 20  # Additional spacing
        for term in terms_conditions:
            c.drawString(40, current_y, term)
            current_y -= 18  # Proper line spacing

        # Update Y position for Insurance Section
        current_y -= section_spacing  

        # Add Insurance Section
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, current_y, "Add Insurance to Your Invoice")

        c.setFont("Helvetica", 10)
        current_y -= 20
        c.drawString(40, current_y, "Would you like to enhance your peace of mind with our optional insurance? Here's what it includes:")

        # Refund Flexibility Section
        current_y -= section_spacing
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, current_y, "1. Refund Flexibility")

        c.setFont("Helvetica", 10)
        current_y -= 15
        c.drawString(55, current_y, "Instead of receiving in-store credit for unused services, you'll be eligible for a full refund of the unused portion of")
        current_y -= 15
        c.drawString(55, current_y, "your invoice.")

        # Additional Insured Status Section
        current_y -= section_spacing
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, current_y, "2. Additional Insured Status")

        c.setFont("Helvetica", 10)
        current_y -= 15
        c.drawString(55, current_y, "Your business or entity will be added as an Additional Insured on our $5,000,000 liability insurance policy,")
        current_y -= 15
        c.drawString(55, current_y, "ensuring extra protection during your service period.")

        # No Credit Card Fees Section
        current_y -= section_spacing
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, current_y, "3. No Credit Card Fees")

        c.setFont("Helvetica", 10)
        current_y -= 15
        c.drawString(55, current_y, "Opting for this insurance also waives all credit card processing fees associated with your invoice.")

        # How It Works Section
        current_y -= section_spacing
        c.setFont("Helvetica", 10)
        c.drawString(40, current_y, "How It Works:")

        text3 = """Simply check the "Add Insurance" box on your invoice to unlock these exclusive benefits. Whether you're safeguarding 
                your investment or boosting liability coverage, this option provides added security and convenience."""

        wrapped_text3 = wrap_text(text3, width=85)
        textobject3 = c.beginText()
        textobject3.setTextOrigin(40, current_y - 20)
        for line in wrapped_text3.split('\n'):
            textobject3.textLine(line)
        c.drawText(textobject3)

        current_y -= 60
        c.drawString(40, current_y, "Let us know if you'd like to take advantage of this valuable service!")

        # Additional Note
        current_y -= section_spacing
        c.setFont("Helvetica", 10)
        c.drawString(40, current_y, "Estimate does not secure services! Please call or email (sales@fastguardservice.com) if you would like to move forward.")
        current_y -= 15
        c.drawString(40, current_y, "FEEL FREE TO CONTACT US AT 844.254.8273")

        # Credit Card Fee Note
        current_y -= section_spacing
        c.drawString(40, current_y, "** There is 3.5% fee for credit card payments. This fee is equivalent to what we pay to accept credit cards.")
        current_y -= 15
        c.drawString(40, current_y, "** Please note that there is no fee for using a debit card.")

        # Service & Refund Information
        current_y -= section_spacing
        service_refund_text = """FGS has a minimum of 6 hours per shift per guard for Service Nationwide. All of our Services are billed in advance before service is
        rendered via Credit Card or Debit Card. REFUND time frame is 7 - 10 business days."""

        wrapped_service_refund = wrap_text(service_refund_text, width=90)
        textobject6 = c.beginText()
        textobject6.setTextOrigin(40, current_y)
        for line in wrapped_service_refund.split('\n'):
            textobject6.textLine(line)
        c.drawText(textobject6)

        # Federal Holidays Section
        current_y -= section_spacing+20
        holidays_text = """The following Federal Holidays are billed at time and a half: New Year's Day, Memorial Day, Independence Day, Labor Day, Veterans Day,
        Thanksgiving Day, & Christmas Day."""

        wrapped_holidays = wrap_text(holidays_text, width=85)
        textobject7 = c.beginText()
        textobject7.setTextOrigin(40, current_y)
        for line in wrapped_holidays.split('\n'):
            textobject7.textLine(line)
        c.drawText(textobject7)
                
        c.save()
    
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        raise ValueError(f"Error creating PDF: {str(e)}")






def attach_file_to_lead(lead_id, file_path):
    """Attaches a file to a lead in Zoho CRM."""
    try:
        access_token = get_valid_access_token()
        url = f"https://www.zohoapis.com/crm/v3/Leads/{lead_id}/Attachments"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        with open(file_path, "rb") as file:
            response = requests.post(url, headers=headers, files={"file": file})
        if response.status_code == 200:
            return True
        else:
            raise ValueError(f"Failed to attach file: {response.text}")
    except Exception as e:
        raise ValueError(f"Error attaching file: {e}")


def process_lead(record_id):
    print('processssssssssss leaddddddddd',record_id)
    """Processes a lead: upload PDF from the database, send email, and attach file."""
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # fetch lead data and pdf binary 
        cursor.execute(
            "SELECT data, quotation_pdf, email FROM uploaded_leads WHERE record_id = %s;", (record_id,)
        )
        result = cursor.fetchone()

        print("--------------------------",result)

        if not result or not result[0] or not result[1]:
            raise ValueError(f"No lead or PDF found with record_id {record_id}")

        lead_data = result[0]  
        pdf_binary = result[1] 
        email=result[2] 


        file_id = upload_pdf_binary_to_zoho(pdf_binary)
        print('fileeeeee_iddddd',file_id)


        # print("---------FILE ID------------",file_id)
        if not file_id:
            raise ValueError(f"Failed to upload PDF for lead {record_id}")

        lead_data["quotation_file_id"] = file_id

        cursor.execute(
            """
            UPDATE uploaded_leads
            SET data = %s
            WHERE record_id = %s;
            """,
            [Json(lead_data), record_id],
        )
        conn.commit()


        recipient_name = f"{lead_data.get('First_Name', '')} {lead_data.get('Last_Name', '')}".strip()
        # print(recipient_name,'----')

        if send_mail_with_attachment(recipient_name, email, record_id, file_id):
            return {"message": "Quotation sent successfully."}, 200
        else:
            raise ValueError(f"Failed to send email for lead {record_id}")


    except Exception as e:
        return {"error": f"Error processing lead {record_id}: {e}"}, 500
    finally:
        if conn:
            cursor.close()
            conn.close()



def send_quotation(record_id):
    """Function to process and send a quotation based on the record_id."""

    # print("record_id", record_id)
    
    try:

        if not record_id:
            return {"error": "Missing record_id"}, 400


        result = process_lead(record_id)

        print('resssssssssss',result)

        

        if isinstance(result, tuple):
            response_data, status_code = result
            if "error" in response_data:  # Check for "error" key
                return response_data, status_code

  
            return response_data, status_code


        return {"error": "Unexpected error occurred."}, 500

    except Exception as e:

        print("Error:", str(e))
        return {"error": "Error occured on generate quotation", "details": str(e)}, 500





# leads which are qualify
@app.route('/qualify', methods=['GET'])
def get_qualified_leads():
    try:

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        

        cursor.execute("""
            SELECT data, pricing 
            FROM uploaded_leads
            WHERE Lead_Status = 'Qualify'
            ORDER BY created_at DESC
        """)
        
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        

        result = [{"data": lead["data"], "pricing": lead["pricing"]} for lead in leads]
        
        return jsonify({
            "success": True,
            "count": len(result),
            "qualified_leads": result
        }), 200
        
    except Exception as e:
        print(f"Error fetching qualified leads: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch qualified leads",
            "details": str(e)
        }), 500


# lead which are not qualify
@app.route('/not_qualify', methods=['GET'])
def get_not_qualified_leads():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory = psycopg2.extras)
        

        cursor.execute("""
            SELECT data, pricing 
            FROM uploaded_leads
            WHERE Lead_Status <> 'Qualify'
            ORDER BY created_at DESC
        """)
        
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        

        result = [{"data": lead["data"], "pricing": lead["pricing"]} for lead in leads]
        
        return jsonify({
            "success": True,
            "count": len(result),
            "not_qualified_leads": result
        }), 200
        
    except Exception as e:
        print(f"Error fetching not qualified leads: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch not qualified leads",
            "details": str(e)
        }), 500


def format_location(location, max_length=40):
    if not location:
        return ""
    # Split by commas and process each part
    parts = [part.strip() for part in location.split(',')]
    formatted_lines = []
    current_line = ""

    for part in parts:
        # If adding the next part exceeds max_length, start a new line
        if len(current_line) + len(part) + 2 > max_length and current_line:
            formatted_lines.append(current_line)
            current_line = part
        else:
            current_line = f"{current_line}{part}," if current_line else f"{part},"
    
    # Add the last line if it exists
    if current_line:
        formatted_lines.append(current_line.rstrip(','))

    return "\n".join(formatted_lines)

# if __name__ == "__main__":
#     app.run(debug=True)


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000)
