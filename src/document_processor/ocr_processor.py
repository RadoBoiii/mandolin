import os
from typing import Dict, List, Optional, Tuple
import pytesseract
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path

class OCRProcessor:
    """Class for processing OCR on referral package documents."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the OCR processor.
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
    def process_document(self, pdf_path: str) -> Dict:
        """
        Process a PDF document using OCR.
        
        Args:
            pdf_path: Path to the PDF document
            
        Returns:
            Dictionary containing processed text and metadata
        """
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        document_data = {
            'pages': [],
            'metadata': {
                'total_pages': len(images),
                'document_type': self._detect_document_type(images[0])
            }
        }
        
        for page_num, image in enumerate(images):
            page_data = self._process_page(image, page_num + 1)
            document_data['pages'].append(page_data)
            
        return document_data
    
    def _process_page(self, image: Image.Image, page_num: int) -> Dict:
        """
        Process a single page image using OCR.
        
        Args:
            image: PIL Image object
            page_num: Page number
            
        Returns:
            Dictionary containing processed page data
        """
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Preprocess image
        preprocessed = self._preprocess_image(cv_image)
        
        # Perform OCR
        text = pytesseract.image_to_string(preprocessed)
        
        # Extract structured data
        data = pytesseract.image_to_data(preprocessed, output_type=pytesseract.Output.DICT)
        
        # Process results
        words = []
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                words.append({
                    'text': data['text'][i],
                    'confidence': data['conf'][i],
                    'bbox': (
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    )
                })
        
        return {
            'page_number': page_num,
            'text': text,
            'words': words,
            'regions': self._detect_regions(preprocessed)
        }
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Deskew
        deskewed = self._deskew_image(denoised)
        
        return deskewed
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew an image to correct rotation.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Deskewed image
        """
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = 90 + angle
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def _detect_regions(self, image: np.ndarray) -> List[Dict]:
        """
        Detect different regions in the document (text, tables, etc.).
        
        Args:
            image: OpenCV image array
            
        Returns:
            List of detected regions
        """
        regions = []
        
        # Convert to binary
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50 and h > 50:  # Filter small regions
                regions.append({
                    'type': self._classify_region(image[y:y+h, x:x+w]),
                    'bbox': (x, y, x+w, y+h)
                })
                
        return regions
    
    def _classify_region(self, region: np.ndarray) -> str:
        """
        Classify a region as text, table, or other.
        
        Args:
            region: OpenCV image array of the region
            
        Returns:
            String indicating region type
        """
        # Add logic to classify region type
        # This is a simple implementation - can be enhanced with ML
        if self._is_table(region):
            return 'table'
        elif self._is_signature(region):
            return 'signature'
        else:
            return 'text'
    
    def _is_table(self, region: np.ndarray) -> bool:
        """
        Check if a region is likely a table.
        
        Args:
            region: OpenCV image array of the region
            
        Returns:
            Boolean indicating if region is a table
        """
        # Convert to binary
        _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find horizontal and vertical lines
        horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((1, 20)))
        vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((20, 1)))
        
        # Count intersections
        intersections = cv2.bitwise_and(horizontal, vertical)
        intersection_count = cv2.countNonZero(intersections)
        
        return intersection_count > 10
    
    def _is_signature(self, region: np.ndarray) -> bool:
        """
        Check if a region is likely a signature.
        
        Args:
            region: OpenCV image array of the region
            
        Returns:
            Boolean indicating if region is a signature
        """
        # Convert to binary
        _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Calculate features
        area = cv2.countNonZero(binary)
        perimeter = cv2.arcLength(cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][0], True)
        
        # Signature-like regions typically have high perimeter-to-area ratio
        return perimeter / (area + 1e-6) > 0.1
    
    def _detect_document_type(self, first_page: Image.Image) -> str:
        """
        Detect the type of document based on its content.
        
        Args:
            first_page: PIL Image of the first page
            
        Returns:
            String indicating document type
        """
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(first_page), cv2.COLOR_RGB2BGR)
        
        # Extract text
        text = pytesseract.image_to_string(cv_image)
        
        # Simple keyword-based classification
        text_lower = text.lower()
        if 'insurance' in text_lower and 'card' in text_lower:
            return 'insurance_card'
        elif 'medical' in text_lower and 'history' in text_lower:
            return 'medical_history'
        elif 'test' in text_lower and 'results' in text_lower:
            return 'test_results'
        else:
            return 'unknown' 