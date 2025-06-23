from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
import pdfplumber
import PyPDF2

@dataclass
class FormField:
    """Class representing a form field."""
    name: str
    type: str
    value: any
    required: bool
    dependencies: List[str]
    validation_rules: List[str]
    bbox: Optional[Tuple[float, float, float, float]] = None

class FormAnalyzer:
    """Class for analyzing PA forms and detecting fields."""
    
    def __init__(self):
        """Initialize the form analyzer."""
        self.field_patterns = {
            'date': r'date|dob|birth',
            'name': r'name|patient|provider',
            'id': r'id|number|account',
            'phone': r'phone|fax|contact',
            'email': r'email|e-mail',
            'address': r'address|location',
            'diagnosis': r'diagnosis|condition|icd',
            'medication': r'medication|drug|prescription',
            'dosage': r'dosage|amount|quantity',
            'frequency': r'frequency|schedule|interval'
        }
        
    def analyze_form(self, pdf_path: str) -> Dict:
        """
        Analyze a PA form and extract its structure.
        
        Args:
            pdf_path: Path to the PA form PDF
            
        Returns:
            Dictionary containing form analysis results
        """
        form_data = {
            'fields': [],
            'sections': [],
            'dependencies': {},
            'validation_rules': {}
        }
        
        # Check if it's a widget-based form
        is_widget_based = self._is_widget_based(pdf_path)
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text blocks
                text_blocks = page.extract_text_blocks()
                
                # Extract form fields
                if is_widget_based:
                    form_fields = page.extract_form_fields()
                    for field_name, field_value in form_fields.items():
                        field = self._analyze_field(field_name, field_value, text_blocks)
                        form_data['fields'].append(field)
                
                # Extract sections
                sections = self._extract_sections(text_blocks)
                form_data['sections'].extend(sections)
                
                # Extract dependencies and validation rules
                dependencies, validation_rules = self._extract_rules(text_blocks)
                form_data['dependencies'].update(dependencies)
                form_data['validation_rules'].update(validation_rules)
                
        return form_data
    
    def _is_widget_based(self, pdf_path: str) -> bool:
        """
        Check if the PDF is a widget-based form.
        
        Args:
            pdf_path: Path to the PDF
            
        Returns:
            Boolean indicating if the form is widget-based
        """
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            return '/AcroForm' in pdf.trailer['/Root']
    
    def _analyze_field(self, field_name: str, field_value: any, text_blocks: List[Dict]) -> FormField:
        """
        Analyze a form field and extract its properties.
        
        Args:
            field_name: Name of the field
            field_value: Value of the field
            text_blocks: List of text blocks from the page
            
        Returns:
            FormField object with field properties
        """
        # Determine field type
        field_type = self._determine_field_type(field_name, field_value)
        
        # Check if field is required
        required = self._is_required_field(field_name, text_blocks)
        
        # Find field dependencies
        dependencies = self._find_field_dependencies(field_name, text_blocks)
        
        # Extract validation rules
        validation_rules = self._extract_validation_rules(field_name, text_blocks)
        
        # Find field bounding box
        bbox = self._find_field_bbox(field_name, text_blocks)
        
        return FormField(
            name=field_name,
            type=field_type,
            value=field_value,
            required=required,
            dependencies=dependencies,
            validation_rules=validation_rules,
            bbox=bbox
        )
    
    def _determine_field_type(self, field_name: str, field_value: any) -> str:
        """
        Determine the type of a form field.
        
        Args:
            field_name: Name of the field
            field_value: Value of the field
            
        Returns:
            String indicating field type
        """
        field_name_lower = field_name.lower()
        
        # Check field value type
        if isinstance(field_value, bool):
            return 'checkbox'
        elif isinstance(field_value, (int, float)):
            return 'number'
            
        # Check field name patterns
        for field_type, pattern in self.field_patterns.items():
            if re.search(pattern, field_name_lower):
                return field_type
                
        return 'text'
    
    def _is_required_field(self, field_name: str, text_blocks: List[Dict]) -> bool:
        """
        Check if a field is required.
        
        Args:
            field_name: Name of the field
            text_blocks: List of text blocks from the page
            
        Returns:
            Boolean indicating if the field is required
        """
        # Look for required indicators in nearby text
        for block in text_blocks:
            text = block['text'].lower()
            if field_name.lower() in text:
                return any(indicator in text for indicator in ['required', 'mandatory', '*'])
        return False
    
    def _find_field_dependencies(self, field_name: str, text_blocks: List[Dict]) -> List[str]:
        """
        Find dependencies for a field.
        
        Args:
            field_name: Name of the field
            text_blocks: List of text blocks from the page
            
        Returns:
            List of dependent field names
        """
        dependencies = []
        
        # Look for conditional statements
        for block in text_blocks:
            text = block['text'].lower()
            if 'if' in text and field_name.lower() in text:
                # Extract dependent field names
                matches = re.findall(r'if\s+([a-zA-Z0-9_]+)', text)
                dependencies.extend(matches)
                
        return list(set(dependencies))
    
    def _extract_validation_rules(self, field_name: str, text_blocks: List[Dict]) -> List[str]:
        """
        Extract validation rules for a field.
        
        Args:
            field_name: Name of the field
            text_blocks: List of text blocks from the page
            
        Returns:
            List of validation rules
        """
        rules = []
        
        # Look for validation instructions
        for block in text_blocks:
            text = block['text'].lower()
            if field_name.lower() in text:
                # Extract validation rules
                if 'format' in text:
                    rules.append('format')
                if 'length' in text:
                    rules.append('length')
                if 'range' in text:
                    rules.append('range')
                    
        return rules
    
    def _find_field_bbox(self, field_name: str, text_blocks: List[Dict]) -> Optional[Tuple[float, float, float, float]]:
        """
        Find the bounding box of a field.
        
        Args:
            field_name: Name of the field
            text_blocks: List of text blocks from the page
            
        Returns:
            Tuple of (x0, y0, x1, y1) coordinates or None
        """
        for block in text_blocks:
            if field_name.lower() in block['text'].lower():
                return block['bbox']
        return None
    
    def _extract_sections(self, text_blocks: List[Dict]) -> List[Dict]:
        """
        Extract sections from the form.
        
        Args:
            text_blocks: List of text blocks from the page
            
        Returns:
            List of section dictionaries
        """
        sections = []
        current_section = None
        
        for block in text_blocks:
            text = block['text'].strip()
            
            # Check if this is a section header
            if text.isupper() or text.endswith(':'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': text,
                    'content': [],
                    'bbox': block['bbox']
                }
            elif current_section:
                current_section['content'].append({
                    'text': text,
                    'bbox': block['bbox']
                })
                
        if current_section:
            sections.append(current_section)
            
        return sections
    
    def _extract_rules(self, text_blocks: List[Dict]) -> Tuple[Dict, Dict]:
        """
        Extract dependencies and validation rules from the form.
        
        Args:
            text_blocks: List of text blocks from the page
            
        Returns:
            Tuple of (dependencies, validation_rules) dictionaries
        """
        dependencies = {}
        validation_rules = {}
        
        for block in text_blocks:
            text = block['text'].lower()
            
            # Extract dependencies
            if 'if' in text:
                matches = re.findall(r'if\s+([a-zA-Z0-9_]+)\s+then\s+([a-zA-Z0-9_]+)', text)
                for condition, dependent in matches:
                    if condition not in dependencies:
                        dependencies[condition] = []
                    dependencies[condition].append(dependent)
                    
            # Extract validation rules
            if 'must' in text or 'should' in text:
                field_matches = re.findall(r'([a-zA-Z0-9_]+)\s+(?:must|should)', text)
                for field in field_matches:
                    if field not in validation_rules:
                        validation_rules[field] = []
                    validation_rules[field].append(text)
                    
        return dependencies, validation_rules 