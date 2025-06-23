"""
PA Form Automation Workflow Script
- Lists PDFs in the Input Data directory
- Extracts text from PDF using Fitz (PyMuPDF) and Tesseract OCR
- Uses OpenAI to extract structured information
- Maps extracted info to PA form fields
- Prints what would be filled in the PA form (placeholder for actual PDF filling)
"""

import os
from glob import glob
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import pdfplumber
import openai
import json
from dotenv import load_dotenv

load_dotenv()

# 1. List all PDFs in the Input Data directory and organize by patient
def list_pdfs(input_data_dir='Input Data'):
    pdf_files = glob(os.path.join(input_data_dir, '**', '*.pdf'), recursive=True)
    print(f'Found {len(pdf_files)} PDF files:')
    
    # Organize by patient
    patients = {}
    for pdf in pdf_files:
        # Extract patient name from path (e.g., "Input Data/Adbulla/referral_package.pdf" -> "Adbulla")
        patient_name = os.path.basename(os.path.dirname(pdf))
        if patient_name not in patients:
            patients[patient_name] = []
        patients[patient_name].append(pdf)
    
    # Print organized by patient
    for patient, files in patients.items():
        print(f'\nPatient: {patient}')
        for i, pdf in enumerate(files):
            file_type = "Referral Package" if "referral" in os.path.basename(pdf).lower() else "PA Form"
            print(f'  [{len(patients)}*{i}] {file_type}: {os.path.basename(pdf)}')
    
    return pdf_files, patients

def select_pdf_to_process(patients):
    """Let user select which PDF to process"""
    print("\nSelect a PDF to process:")
    print("Format: [patient_index][file_index] (e.g., 01 for first patient, first file)")
    
    patient_list = list(patients.keys())
    for i, patient in enumerate(patient_list):
        print(f"  [{i}] {patient}")
    
    try:
        choice = input("Enter your choice (e.g., 01): ").strip()
        if len(choice) >= 2:
            patient_idx = int(choice[0])
            file_idx = int(choice[1])
            if patient_idx < len(patient_list) and file_idx < len(patients[patient_list[patient_idx]]):
                selected_pdf = patients[patient_list[patient_idx]][file_idx]
                print(f"Selected: {selected_pdf}")
                return selected_pdf
    except (ValueError, IndexError):
        pass
    
    # Default to first referral package
    print("Using default: first referral package found")
    for patient, files in patients.items():
        for pdf in files:
            if "referral" in os.path.basename(pdf).lower():
                return pdf
    
    # Fallback to first file
    return list(patients.values())[0][0]

# 2. Extract text from a PDF using Fitz and fallback to Tesseract OCR
def extract_text_from_pdf(pdf_path):
    text = ''
    # Try Fitz (PyMuPDF)
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    # If text is too sparse, fallback to OCR
    if len(text.strip()) < 100:
        print('Fitz extraction sparse, using OCR...')
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                img = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text
    return text

# 3. Use OpenAI to extract structured information from the referral package
def extract_info_with_openai(text, prompt=None, model='gpt-3.5-turbo'):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    if prompt is None:
        prompt = (
            "Extract the following fields from the text: Patient Name, DOB, MRN, Diagnosis, Insurance Plan, Insurance ID, Previous Medications, Treatment Plan, Recent Labs."
            " Return as a JSON object."
        )
    messages = [
        {"role": "system", "content": "You are a medical data extraction assistant."},
        {"role": "user", "content": prompt + '\n\n' + text}
    ]
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=512)
    return response.choices[0].message.content

# 4. Map extracted info to PA form fields
def map_to_pa_form_fields(info_json):
    info = json.loads(info_json) if isinstance(info_json, str) else info_json
    pa_form_fields = {
        'First Name': info.get('Patient Name', '').split()[0] if info.get('Patient Name') else '',
        'Last Name': info.get('Patient Name', '').split()[-1] if info.get('Patient Name') else '',
        'DOB': info.get('DOB', ''),
        'MRN': info.get('MRN', ''),
        'Diagnosis': info.get('Diagnosis', ''),
        'Insurance Plan': info.get('Insurance Plan', ''),
        'Insurance ID': info.get('Insurance ID', ''),
        'Previous Medications': info.get('Previous Medications', []),
        'Treatment Plan': info.get('Treatment Plan', ''),
        'Recent Labs': info.get('Recent Labs', {}),
    }
    return pa_form_fields

# 5. Print what would be filled in the PA form (placeholder for actual PDF filling)
def print_pa_form_fields(pa_form_fields):
    print('\n=== PA FORM FIELDS TO FILL ===')
    for k, v in pa_form_fields.items():
        print(f'{k}: {v}')
    print('============================\n')

if __name__ == "__main__":
    # Step 1: List PDFs organized by patient
    pdf_files, patients = list_pdfs()
    if not pdf_files:
        print('No PDF files found. Exiting.')
        exit(1)

    # Step 2: Select a PDF to process
    pdf_path = select_pdf_to_process(patients)
    print(f'\nExtracting from: {pdf_path}\n')
    extracted_text = extract_text_from_pdf(pdf_path)
    print(f'Extracted text (first 500 chars):\n{extracted_text[:500]}\n')

    # Step 3: Use OpenAI to extract structured info
    print('Extracting structured info with OpenAI...')
    info_json = extract_info_with_openai(extracted_text)
    print(f'OpenAI extracted info:\n{info_json}\n')

    # Step 4: Map to PA form fields
    pa_fields = map_to_pa_form_fields(info_json)

    # Step 5: Print what would be filled in the PA form
    print_pa_form_fields(pa_fields)
    print('Workflow complete!') 