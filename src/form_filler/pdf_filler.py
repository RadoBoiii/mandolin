from typing import Dict, List, Optional, Tuple
import os
from PyPDF2 import PdfReader, PdfWriter
import pdfrw
from pdfrw import PdfReader as PdfrwReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

class PDFFiller:
    """Class for filling PDF forms with extracted data."""
    
    def __init__(self):
        """Initialize the PDF filler."""
        self.supported_field_types = {
            'text': self._fill_text_field,
            'checkbox': self._fill_checkbox,
            'radio': self._fill_radio,
            'date': self._fill_date_field,
            'number': self._fill_number_field
        }
        
    def fill_form(self, form_path: str, field_mappings: List[Dict], output_path: str) -> bool:
        """
        Fill a PDF form with mapped field values.
        
        Args:
            form_path: Path to the PDF form
            field_mappings: List of field mapping dictionaries
            output_path: Path to save the filled form
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if it's a widget-based form
            is_widget_based = self._is_widget_based(form_path)
            
            if is_widget_based:
                return self._fill_widget_form(form_path, field_mappings, output_path)
            else:
                return self._fill_non_widget_form(form_path, field_mappings, output_path)
                
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            return False
    
    def _is_widget_based(self, pdf_path: str) -> bool:
        """
        Check if the PDF is a widget-based form.
        
        Args:
            pdf_path: Path to the PDF
            
        Returns:
            Boolean indicating if the form is widget-based
        """
        with open(pdf_path, 'rb') as file:
            pdf = PdfReader(file)
            return '/AcroForm' in pdf.trailer['/Root']
    
    def _fill_widget_form(self, form_path: str, field_mappings: List[Dict], output_path: str) -> bool:
        """
        Fill a widget-based PDF form.
        
        Args:
            form_path: Path to the PDF form
            field_mappings: List of field mapping dictionaries
            output_path: Path to save the filled form
            
        Returns:
            Boolean indicating success
        """
        try:
            # Read the PDF
            template_pdf = pdfrw.PdfReader(form_path)
            
            # Create a new PDF with the same pages
            output_pdf = pdfrw.PdfWriter()
            
            # Fill the form fields
            for page in template_pdf.pages:
                annotations = page['/Annots']
                if annotations:
                    for annotation in annotations:
                        if annotation['/Subtype'] == '/Widget':
                            field_name = annotation['/T']
                            if field_name:
                                # Find matching field mapping
                                mapping = next(
                                    (m for m in field_mappings if m['form_field'] == field_name),
                                    None
                                )
                                
                                if mapping:
                                    # Fill the field based on its type
                                    field_type = mapping.get('type', 'text')
                                    if field_type in self.supported_field_types:
                                        self.supported_field_types[field_type](
                                            annotation,
                                            mapping['value']
                                        )
                
                output_pdf.addpage(page)
            
            # Write the filled form
            output_pdf.write(output_path)
            return True
            
        except Exception as e:
            print(f"Error filling widget form: {str(e)}")
            return False
    
    def _fill_non_widget_form(self, form_path: str, field_mappings: List[Dict], output_path: str) -> bool:
        """
        Fill a non-widget PDF form.
        
        Args:
            form_path: Path to the PDF form
            field_mappings: List of field mapping dictionaries
            output_path: Path to save the filled form
            
        Returns:
            Boolean indicating success
        """
        try:
            # Read the template PDF
            template_pdf = PdfReader(form_path)
            output_pdf = PdfWriter()
            
            # Create a new PDF with the same pages
            for page in template_pdf.pages:
                output_pdf.add_page(page)
            
            # Create a new PDF with the filled fields
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Fill the fields
            for mapping in field_mappings:
                if 'bbox' in mapping:
                    x, y, _, _ = mapping['bbox']
                    value = str(mapping['value'])
                    
                    # Draw the text
                    can.drawString(x, y, value)
            
            can.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            
            # Create a new PDF with the filled fields
            new_pdf = PdfReader(packet)
            
            # Merge the filled fields with the template
            for page in range(len(output_pdf.pages)):
                output_pdf.pages[page].merge_page(new_pdf.pages[0])
            
            # Write the filled form
            with open(output_path, 'wb') as output_file:
                output_pdf.write(output_file)
                
            return True
            
        except Exception as e:
            print(f"Error filling non-widget form: {str(e)}")
            return False
    
    def _fill_text_field(self, annotation: pdfrw.objects.pdfdict.PdfDict, value: str) -> None:
        """
        Fill a text field.
        
        Args:
            annotation: PDF annotation object
            value: Field value
        """
        annotation.update(
            pdfrw.objects.pdfdict.PdfDict(
                V=value,
                AS=value
            )
        )
    
    def _fill_checkbox(self, annotation: pdfrw.objects.pdfdict.PdfDict, value: bool) -> None:
        """
        Fill a checkbox field.
        
        Args:
            annotation: PDF annotation object
            value: Field value
        """
        if value:
            annotation.update(
                pdfrw.objects.pdfdict.PdfDict(
                    V='/Yes',
                    AS='/Yes'
                )
            )
        else:
            annotation.update(
                pdfrw.objects.pdfdict.PdfDict(
                    V='/Off',
                    AS='/Off'
                )
            )
    
    def _fill_radio(self, annotation: pdfrw.objects.pdfdict.PdfDict, value: str) -> None:
        """
        Fill a radio button field.
        
        Args:
            annotation: PDF annotation object
            value: Field value
        """
        annotation.update(
            pdfrw.objects.pdfdict.PdfDict(
                V=value,
                AS=value
            )
        )
    
    def _fill_date_field(self, annotation: pdfrw.objects.pdfdict.PdfDict, value: str) -> None:
        """
        Fill a date field.
        
        Args:
            annotation: PDF annotation object
            value: Field value
        """
        # Format date if needed
        formatted_date = self._format_date(value)
        self._fill_text_field(annotation, formatted_date)
    
    def _fill_number_field(self, annotation: pdfrw.objects.pdfdict.PdfDict, value: str) -> None:
        """
        Fill a number field.
        
        Args:
            annotation: PDF annotation object
            value: Field value
        """
        # Format number if needed
        formatted_number = self._format_number(value)
        self._fill_text_field(annotation, formatted_number)
    
    def _format_date(self, date_str: str) -> str:
        """
        Format a date string.
        
        Args:
            date_str: Date string to format
            
        Returns:
            Formatted date string
        """
        # Add date formatting logic here
        return date_str
    
    def _format_number(self, number_str: str) -> str:
        """
        Format a number string.
        
        Args:
            number_str: Number string to format
            
        Returns:
            Formatted number string
        """
        # Add number formatting logic here
        return number_str 