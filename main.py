# from flask import app
# import streamlit as st
# import requests
# import os

# BACKEND_URL = os.getenv("BACKEND_URL")

# st.title("Security Service Request Form")

# # Basic Information
# data = {}
# data["Security_Need_Reason"] = st.text_input("Why Do You Feel You Need Security? *")
# data["Company_Name"] = st.text_input("Company Name *")
# data["Company_Address"] = st.text_input("Company Address *")
# data["Email"] = st.text_input("Email *")
# data["First_Name"] = st.text_input("First Name *")
# data["Last_Name"] = st.text_input("Last Name *")

# # Type of Security Needed (Multi-select)
# security_types = ["",
#     "Security Guards", "Unarmed Security", "Armed Security", "Event Security",
#     "Fire Watch Guards", "Bodyguards", "Private Investigators", "Courses/Classes",
#     "Employee Termination", "Executive Protection"
# ]
# data["Security_Type"] = st.selectbox("Type Of Security Needed? *", security_types)

# # Conditional Fields
# if "Armed Security" in data["Security_Type"] or "Employee Termination" in data["Security_Type"]:
#     data["Police_Report"] = st.selectbox("Have You Made A Police Report? Has There Been A Credible Threat? *", ["Yes", "No"])

# if "Fire Watch Guards" in data["Security_Type"]:
#     data["Floors_Num"] = st.number_input("How Many Floors Is The Location? *", min_value=1, step=1)

# # Location
# data["Location_Serviced"] = st.text_input("Location To Be Serviced? *")

# # Date & Time
# data["Start_Date"] = st.date_input("Start Date *", value=None)
# data["End_Date"] = st.date_input("End Date *", value=None)
# # Time selection
# data["Start_Time"] = st.time_input("Start Time *", value=None)
# data["End_Time"] = st.time_input("End Time *", value=None)


# #data["Daily_Hours_Coverage"] = st.text_input("Daily Hours of Coverage *")

# # Indoor or Outdoor
# data["Indoor_Or_Outdoor"] = st.radio("Is This Job Indoor Or Outdoor? *", ["Outdoor", "Indoor"])

# # state
# # Indoor or Outdoor
# # data["State"] =

# # Alcohol Presence
# data["Alcohol_Present"] = st.radio("Will There Be Alcohol? *", ["Yes", "No"])

# # Job Description
# data["Job_Description"] = st.text_area("What Is The Job Description That You Would Like The Guard To Perform? *")

# # How many guards you want 
# data["Guards"] = st.text_input("How many Guards you want? *")

# # Contact Number
# data["Mobile"] = st.text_input("Best Number To Contact You? *")

# # Add a note about required fields
# st.markdown("**Note:** Fields marked with * are required")

# # Submit Button
# if st.button("Submit"):
#     # Validate that all required fields are filled
#     empty_fields = [field for field, value in data.items() if not value]
#     if empty_fields:
#         st.error("Please fill in all required fields")
#     else:
#         # Send data to the API
#         response = requests.post("{BACKEND_URL}/submit_lead", json=data)
        
#         if response.status_code == 201:
#             st.success("Form submitted successfully!")
#         else:
#             st.error(f"Error submitting form. Status Code: {response.status_code}, Message: {response.text}")


# # Define API URLs
# get_lead_details_url = "{BACKEND_URL}/get_qualify_leads"
# generate_pdf_url = "{BACKEND_URL}/generate_quotation"
# get_pdf_url = "{BACKEND_URL}/get-pdf/"
# send_quotation_url = "{BACKEND_URL}/send_quotation"

# # Function to generate PDF
# def generate_pdf(record_id):
#     try:
#         payload = {"record_id": record_id}
#         response = requests.post(generate_pdf_url, json=payload)
#         if response.status_code == 200:
#             return True
#         else:
#             st.error("Failed to generate PDF")
#             return False
#     except Exception as e:
#         st.error(f"Error generating PDF: {e}")
#         return False

# # Function to fetch and provide the PDF download link
# def download_pdf(record_id):
#     try:
#         response = requests.get(f"{get_pdf_url}{record_id}")
#         if response.status_code == 200:
#             st.download_button(
#                 "Download Quote",
#                 response.content,
#                 file_name=f"quotation_{record_id}.pdf",
#                 mime="application/pdf"
#             )
#         else:
#             st.error("Failed to download PDF")
#     except Exception as e:
#         st.error(f"Error downloading PDF: {e}")

# # Function to fetch lead details from the API
# def get_lead_details():
#     try:
#         response = requests.get(get_lead_details_url)
#         if response.status_code == 200:
#             print(response.json())
#             return response.json()
#         else:
#             st.error("No leads in database")
#             return []
#     except Exception as e:
#         st.error(f"Error fetching lead details: {e}")
#         return []

# # Function to send the quotation
# def send_quotation(record_id, email):
#     try:
#         # Data payload to send to the backend
#         data = {
#             "record_id": record_id,
#             "email": email
#         }

#         # Send the POST request to the backend
#         response = requests.post(send_quotation_url, json=data)

#         # Handle response based on status code and content
#         if response.status_code == 200:
#             response_data = response.json()
#             print(response_data)
#             st.success(response_data)
#         elif response.status_code == 400:
#             response_data = response.json()
#             error = response_data.get("error", "Invalid input provided.")
#             st.warning(error)
#         elif response.status_code == 500:
#             response_data = response.json()
#             error = response_data.get("error", "An internal server error occurred.")
#             st.error(f"Error: {error}")
#         else:
#             st.error(f"Unexpected error: {response.status_code}")
#     except requests.exceptions.RequestException as e:
#         st.error(f"Error sending quotation: {e}")
#     except Exception as e:
#         st.error(f"Unexpected error: {e}")

# # Fetch lead details
# leads = get_lead_details()

# # Sidebar for displaying lead details
# if leads and "qualified_leads" in leads:
#     for lead in leads["qualified_leads"]:
#         email = lead["email"]
#         full_name = f"{lead['first_name']} {lead['last_name']}"
#         record_id = lead["record_id"]
        
#         # Create a unique key for the session state for this lead
#         pdf_generated_key = f"pdf_generated_{record_id}"
        
#         # Initialize session state for PDF generation status if not exists
#         if pdf_generated_key not in st.session_state:
#             st.session_state[pdf_generated_key] = False
        
#         with st.sidebar:
#             # Display lead details
#             st.subheader(f"Qualify Lead: {full_name}")
#             st.write(f"Record ID: {record_id}")
            
#             # View PDF button and logic
#             if st.button(f"Generate Quote", key=f"view_pdf_{record_id}"):
#                 if generate_pdf(record_id):
#                     st.session_state[pdf_generated_key] = True
            
#             # Show download button only if PDF was generated
#             if st.session_state[pdf_generated_key]:
#                 download_pdf(record_id)
            
#             # Button to send quotation
#             if st.button(f"Send Quote to {full_name}", key=f"send_quotation_{record_id}"):
#                 send_quotation(record_id, email)
            
#             # Add a separator between leads
#             st.markdown("---")

from app import app

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=5000)