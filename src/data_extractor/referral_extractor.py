from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
import spacy
from transformers import pipeline

@dataclass
class ExtractedInfo:
    """Class representing extracted information from a referral package."""
    patient_info: Dict
    medical_info: Dict
    insurance_info: Dict
    provider_info: Dict
    confidence_scores: Dict

class ReferralExtractor:
    """Class for extracting information from referral packages."""
    
    def __init__(self):
        """Initialize the referral extractor."""
        # Load spaCy model for NER
        self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize transformers pipeline for question answering
        self.qa_pipeline = pipeline("question-answering")
        
        # Define field patterns
        self.field_patterns = {
            'patient': {
                'name': r'(?:patient|member)\s*name:?\s*([^\n]+)',
                'dob': r'(?:date of birth|dob|birth date):?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                'gender': r'(?:gender|sex):?\s*([MF]|male|female)',
                'id': r'(?:patient|member)\s*(?:id|number|#):?\s*([A-Z0-9-]+)'
            },
            'medical': {
                'diagnosis': r'(?:diagnosis|condition|icd):?\s*([^\n]+)',
                'medication': r'(?:medication|drug|prescription):?\s*([^\n]+)',
                'dosage': r'(?:dosage|amount|quantity):?\s*([^\n]+)',
                'frequency': r'(?:frequency|schedule|interval):?\s*([^\n]+)'
            },
            'insurance': {
                'provider': r'(?:insurance|carrier|payer):?\s*([^\n]+)',
                'policy': r'(?:policy|group)\s*(?:number|#):?\s*([A-Z0-9-]+)',
                'member_id': r'(?:member|subscriber)\s*(?:id|number|#):?\s*([A-Z0-9-]+)'
            },
            'provider': {
                'name': r'(?:provider|physician|doctor)\s*name:?\s*([^\n]+)',
                'npi': r'npi:?\s*(\d{10})',
                'phone': r'(?:phone|telephone|tel):?\s*(\d{3}[-.]?\d{3}[-.]?\d{4})',
                'fax': r'fax:?\s*(\d{3}[-.]?\d{3}[-.]?\d{4})'
            }
        }
        
    def extract_info(self, document_data: Dict) -> ExtractedInfo:
        """
        Extract information from a referral package.
        
        Args:
            document_data: Dictionary containing processed document data
            
        Returns:
            ExtractedInfo object containing extracted information
        """
        # Combine all text from pages
        full_text = self._combine_text(document_data['pages'])
        
        # Extract information using different methods
        patient_info = self._extract_patient_info(full_text)
        medical_info = self._extract_medical_info(full_text)
        insurance_info = self._extract_insurance_info(full_text)
        provider_info = self._extract_provider_info(full_text)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(
            patient_info, medical_info, insurance_info, provider_info
        )
        
        return ExtractedInfo(
            patient_info=patient_info,
            medical_info=medical_info,
            insurance_info=insurance_info,
            provider_info=provider_info,
            confidence_scores=confidence_scores
        )
    
    def _combine_text(self, pages: List[Dict]) -> str:
        """
        Combine text from all pages.
        
        Args:
            pages: List of page data dictionaries
            
        Returns:
            Combined text string
        """
        return '\n'.join(page['text'] for page in pages)
    
    def _extract_patient_info(self, text: str) -> Dict:
        """
        Extract patient information.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of patient information
        """
        info = {}
        
        # Extract using regex patterns
        for field, pattern in self.field_patterns['patient'].items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[field] = match.group(1).strip()
                
        # Use NER for additional extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and 'name' not in info:
                info['name'] = ent.text
            elif ent.label_ == 'DATE' and 'dob' not in info:
                info['dob'] = ent.text
                
        return info
    
    def _extract_medical_info(self, text: str) -> Dict:
        """
        Extract medical information.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of medical information
        """
        info = {}
        
        # Extract using regex patterns
        for field, pattern in self.field_patterns['medical'].items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[field] = match.group(1).strip()
                
        # Use NER for additional extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'DISEASE' and 'diagnosis' not in info:
                info['diagnosis'] = ent.text
                
        return info
    
    def _extract_insurance_info(self, text: str) -> Dict:
        """
        Extract insurance information.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of insurance information
        """
        info = {}
        
        # Extract using regex patterns
        for field, pattern in self.field_patterns['insurance'].items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[field] = match.group(1).strip()
                
        return info
    
    def _extract_provider_info(self, text: str) -> Dict:
        """
        Extract provider information.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of provider information
        """
        info = {}
        
        # Extract using regex patterns
        for field, pattern in self.field_patterns['provider'].items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[field] = match.group(1).strip()
                
        # Use NER for additional extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and 'name' not in info:
                info['name'] = ent.text
            elif ent.label_ == 'PHONE' and 'phone' not in info:
                info['phone'] = ent.text
                
        return info
    
    def _calculate_confidence_scores(self, patient_info: Dict, medical_info: Dict,
                                   insurance_info: Dict, provider_info: Dict) -> Dict:
        """
        Calculate confidence scores for extracted information.
        
        Args:
            patient_info: Patient information dictionary
            medical_info: Medical information dictionary
            insurance_info: Insurance information dictionary
            provider_info: Provider information dictionary
            
        Returns:
            Dictionary of confidence scores
        """
        scores = {}
        
        # Calculate scores based on extraction method and data quality
        for category, info in [
            ('patient', patient_info),
            ('medical', medical_info),
            ('insurance', insurance_info),
            ('provider', provider_info)
        ]:
            for field, value in info.items():
                # Base score on extraction method
                if field in self.field_patterns[category]:
                    scores[f"{category}_{field}"] = 0.8  # Regex match
                else:
                    scores[f"{category}_{field}"] = 0.6  # NER extraction
                    
                # Adjust score based on data quality
                if value:
                    if self._is_valid_format(category, field, value):
                        scores[f"{category}_{field}"] += 0.1
                    if self._is_consistent_with_context(category, field, value):
                        scores[f"{category}_{field}"] += 0.1
                        
        return scores
    
    def _is_valid_format(self, category: str, field: str, value: str) -> bool:
        """
        Check if a value matches expected format.
        
        Args:
            category: Information category
            field: Field name
            value: Field value
            
        Returns:
            Boolean indicating if format is valid
        """
        if field == 'dob':
            return bool(re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', value))
        elif field in ['phone', 'fax']:
            return bool(re.match(r'\d{3}[-.]?\d{3}[-.]?\d{4}', value))
        elif field == 'npi':
            return bool(re.match(r'\d{10}', value))
        return True
    
    def _is_consistent_with_context(self, category: str, field: str, value: str) -> bool:
        """
        Check if a value is consistent with its context.
        
        Args:
            category: Information category
            field: Field name
            value: Field value
            
        Returns:
            Boolean indicating if value is consistent
        """
        # Add logic to check consistency
        # For example, check if dates are reasonable, names are properly formatted, etc.
        return True 