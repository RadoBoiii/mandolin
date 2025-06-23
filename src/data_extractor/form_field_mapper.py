from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

@dataclass
class FieldMapping:
    """Class representing a mapping between extracted data and form field."""
    form_field: str
    extracted_field: str
    confidence: float
    value: any
    validation_passed: bool

class FormFieldMapper:
    """Class for mapping extracted data to form fields."""
    
    def __init__(self):
        """Initialize the form field mapper."""
        self.field_mappings = {
            'patient': {
                'name': ['patient_name', 'member_name', 'name'],
                'dob': ['date_of_birth', 'dob', 'birth_date'],
                'gender': ['gender', 'sex'],
                'id': ['patient_id', 'member_id', 'id_number']
            },
            'medical': {
                'diagnosis': ['diagnosis', 'condition', 'icd_code'],
                'medication': ['medication', 'drug', 'prescription'],
                'dosage': ['dosage', 'amount', 'quantity'],
                'frequency': ['frequency', 'schedule', 'interval']
            },
            'insurance': {
                'provider': ['insurance_provider', 'carrier', 'payer'],
                'policy': ['policy_number', 'group_number'],
                'member_id': ['member_id', 'subscriber_id']
            },
            'provider': {
                'name': ['provider_name', 'physician_name', 'doctor_name'],
                'npi': ['npi', 'provider_id'],
                'phone': ['phone', 'telephone'],
                'fax': ['fax']
            }
        }
        
        self.validation_rules = {
            'date': r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',
            'phone': r'^\d{3}[-.]?\d{3}[-.]?\d{4}$',
            'npi': r'^\d{10}$',
            'id': r'^[A-Z0-9-]+$'
        }
        
    def map_fields(self, form_fields: List[Dict], extracted_info: Dict) -> List[FieldMapping]:
        """
        Map extracted information to form fields.
        
        Args:
            form_fields: List of form field dictionaries
            extracted_info: Dictionary of extracted information
            
        Returns:
            List of FieldMapping objects
        """
        mappings = []
        
        for form_field in form_fields:
            # Find best matching extracted field
            best_match = self._find_best_match(form_field['name'], extracted_info)
            
            if best_match:
                # Validate the value
                validation_passed = self._validate_value(
                    form_field['type'],
                    best_match['value']
                )
                
                # Create mapping
                mapping = FieldMapping(
                    form_field=form_field['name'],
                    extracted_field=best_match['field'],
                    confidence=best_match['confidence'],
                    value=best_match['value'],
                    validation_passed=validation_passed
                )
                
                mappings.append(mapping)
                
        return mappings
    
    def _find_best_match(self, form_field: str, extracted_info: Dict) -> Optional[Dict]:
        """
        Find the best matching extracted field for a form field.
        
        Args:
            form_field: Form field name
            extracted_info: Dictionary of extracted information
            
        Returns:
            Dictionary containing best match information or None
        """
        best_match = None
        highest_confidence = 0
        
        # Flatten extracted info
        flat_info = self._flatten_extracted_info(extracted_info)
        
        # Try exact match first
        if form_field.lower() in flat_info:
            return {
                'field': form_field,
                'value': flat_info[form_field.lower()],
                'confidence': 1.0
            }
            
        # Try fuzzy matching
        for category, fields in self.field_mappings.items():
            for extracted_field, possible_matches in fields.items():
                # Calculate similarity scores
                scores = process.extract(
                    form_field,
                    possible_matches,
                    scorer=fuzz.ratio
                )
                
                # Get best score
                best_score = max(score for _, score in scores)
                
                if best_score > highest_confidence:
                    highest_confidence = best_score
                    best_match = {
                        'field': extracted_field,
                        'value': extracted_info[category].get(extracted_field),
                        'confidence': best_score / 100.0
                    }
                    
        return best_match if highest_confidence > 70 else None
    
    def _flatten_extracted_info(self, extracted_info: Dict) -> Dict:
        """
        Flatten nested extracted information dictionary.
        
        Args:
            extracted_info: Nested dictionary of extracted information
            
        Returns:
            Flattened dictionary
        """
        flat_info = {}
        
        for category, info in extracted_info.items():
            if isinstance(info, dict):
                for field, value in info.items():
                    flat_info[f"{category}_{field}".lower()] = value
                    
        return flat_info
    
    def _validate_value(self, field_type: str, value: any) -> bool:
        """
        Validate a field value against its type.
        
        Args:
            field_type: Type of the field
            value: Value to validate
            
        Returns:
            Boolean indicating if validation passed
        """
        if not value:
            return False
            
        # Convert value to string for validation
        value_str = str(value).lower()
        
        # Check against validation rules
        if field_type in self.validation_rules:
            return bool(re.match(self.validation_rules[field_type], value_str))
            
        # Type-specific validation
        if field_type == 'checkbox':
            return isinstance(value, bool)
        elif field_type == 'number':
            return isinstance(value, (int, float))
        elif field_type == 'date':
            return bool(re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', value_str))
            
        return True
    
    def get_missing_fields(self, form_fields: List[Dict], mappings: List[FieldMapping]) -> List[Dict]:
        """
        Get list of required fields that are missing or invalid.
        
        Args:
            form_fields: List of form field dictionaries
            mappings: List of field mappings
            
        Returns:
            List of missing field dictionaries
        """
        missing_fields = []
        
        # Get mapped field names
        mapped_fields = {mapping.form_field for mapping in mappings}
        
        for field in form_fields:
            if field['required'] and (
                field['name'] not in mapped_fields or
                not any(m.form_field == field['name'] and m.validation_passed for m in mappings)
            ):
                missing_fields.append({
                    'name': field['name'],
                    'type': field['type'],
                    'reason': 'missing' if field['name'] not in mapped_fields else 'invalid'
                })
                
        return missing_fields 