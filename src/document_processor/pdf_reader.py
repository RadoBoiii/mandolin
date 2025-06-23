import os
from typing import Dict, List, Optional, Tuple
import pdfplumber
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import numpy as np
import cv2

class PDFReader:
    """Utility class for reading and processing PDF documents."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the PDF reader.
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
    def read_pa_form(self, pdf_path: str) -> Dict:
        """
        Read a PA form PDF and extract its structure and fields.
        
        Args:
            pdf_path: Path to the PA form PDF
            
        Returns:
            Dictionary containing form structure and field information
        """
        form_data = {
            'fields': [],
            'is_widget_based': False,
            'pages': []
        }
        
        # Check if it's a widget-based form
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            form_data['is_widget_based'] = '/AcroForm' in pdf.trailer['/Root']
            
        # Extract form fields and structure
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_data = {
                    'page_number': page_num + 1,
                    'text_blocks': [],
                    'form_fields': []
                }
                
                # Extract text blocks using words and lines
                words = page.extract_words()
                lines = page.extract_lines()
                
                # Group words into blocks based on proximity
                current_block = []
                current_y = None
                y_threshold = 5  # pixels
                
                for word in words:
                    if current_y is None:
                        current_y = word['top']
                        current_block.append(word)
                    elif abs(word['top'] - current_y) <= y_threshold:
                        current_block.append(word)
                    else:
                        # Create a block from current words
                        if current_block:
                            block_text = ' '.join(w['text'] for w in current_block)
                            block_bbox = (
                                min(w['x0'] for w in current_block),
                                min(w['top'] for w in current_block),
                                max(w['x1'] for w in current_block),
                                max(w['bottom'] for w in current_block)
                            )
                            page_data['text_blocks'].append({
                                'text': block_text,
                                'bbox': block_bbox
                            })
                        current_block = [word]
                        current_y = word['top']
                
                # Add the last block if any
                if current_block:
                    block_text = ' '.join(w['text'] for w in current_block)
                    block_bbox = (
                        min(w['x0'] for w in current_block),
                        min(w['top'] for w in current_block),
                        max(w['x1'] for w in current_block),
                        max(w['bottom'] for w in current_block)
                    )
                    page_data['text_blocks'].append({
                        'text': block_text,
                        'bbox': block_bbox
                    })
                
                # Extract form fields if widget-based
                if form_data['is_widget_based']:
                    form_fields = page.extract_form_fields()
                    for field_name, field_value in form_fields.items():
                        page_data['form_fields'].append({
                            'name': field_name,
                            'value': field_value
                        })
                
                form_data['pages'].append(page_data)
                
        return form_data
    
    def read_referral_package(self, pdf_path: str) -> Dict:
        """
        Read a referral package PDF and extract text using OCR.
        
        Args:
            pdf_path: Path to the referral package PDF
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        package_data = {
            'pages': [],
            'metadata': {}
        }
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        for page_num, image in enumerate(images):
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Perform OCR
            text = pytesseract.image_to_string(thresh)
            
            # Extract structured data using pytesseract
            data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
            
            page_data = {
                'page_number': page_num + 1,
                'text': text,
                'words': [],
                'confidence': []
            }
            
            # Process OCR results
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    page_data['words'].append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        )
                    })
            
            package_data['pages'].append(page_data)
            
        return package_data
    
    def extract_form_fields(self, pdf_path: str) -> List[Dict]:
        """
        Extract form fields from a PDF document.
        
        Args:
            pdf_path: Path to the PDF document
            
        Returns:
            List of dictionaries containing field information
        """
        fields = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                form_fields = page.extract_form_fields()
                for field_name, field_value in form_fields.items():
                    fields.append({
                        'name': field_name,
                        'value': field_value,
                        'type': self._determine_field_type(field_name, field_value)
                    })
                    
        return fields
    
    def _determine_field_type(self, field_name: str, field_value: any) -> str:
        """
        Determine the type of a form field based on its name and value.
        
        Args:
            field_name: Name of the form field
            field_value: Value of the form field
            
        Returns:
            String indicating the field type
        """
        # Add logic to determine field type based on name patterns and values
        if isinstance(field_value, bool):
            return 'checkbox'
        elif any(keyword in field_name.lower() for keyword in ['date', 'dob']):
            return 'date'
        elif any(keyword in field_name.lower() for keyword in ['phone', 'fax']):
            return 'phone'
        elif any(keyword in field_name.lower() for keyword in ['email']):
            return 'email'
        else:
            return 'text' 