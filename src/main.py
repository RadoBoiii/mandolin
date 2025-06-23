import os
import argparse
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from document_processor.pdf_reader import PDFReader
from document_processor.ocr_processor import OCRProcessor
from document_processor.form_analyzer import FormAnalyzer
from data_extractor.referral_extractor import ReferralExtractor
from data_extractor.form_field_mapper import FormFieldMapper
from form_filler.pdf_filler import PDFFiller
from form_filler.report_generator import ReportGenerator, FormReport, MissingField

class PAFormFillingPipeline:
    """Main pipeline for automating PA form filling."""
    
    def __init__(self, input_dir: str, output_dir: str, tesseract_cmd: Optional[str] = None):
        """
        Initialize the pipeline.
        
        Args:
            input_dir: Directory containing input data
            output_dir: Directory to save output files
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.tesseract_cmd = tesseract_cmd
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "filled_forms").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        
        # Initialize components
        self.pdf_reader = PDFReader(tesseract_cmd)
        self.ocr_processor = OCRProcessor(tesseract_cmd)
        self.form_analyzer = FormAnalyzer()
        self.referral_extractor = ReferralExtractor()
        self.form_field_mapper = FormFieldMapper()
        self.pdf_filler = PDFFiller()
        self.report_generator = ReportGenerator(str(self.output_dir / "reports"))
        
    def process_patient(self, patient_dir: Path) -> Dict:
        """
        Process a single patient's documents.
        
        Args:
            patient_dir: Directory containing patient's documents
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Get patient ID from directory name
            patient_id = patient_dir.name
            
            # Find PA form and referral package
            pa_form_path = next(patient_dir.glob("PA.pdf"))
            referral_path = next(patient_dir.glob("referral_package.pdf"))
            
            # Process PA form
            form_data = self.form_analyzer.analyze_form(str(pa_form_path))
            
            # Process referral package
            referral_data = self.ocr_processor.process_document(str(referral_path))
            extracted_info = self.referral_extractor.extract_info(referral_data)
            
            # Map extracted information to form fields
            field_mappings = self.form_field_mapper.map_fields(
                form_data['fields'],
                extracted_info
            )
            
            # Fill the form
            output_form_path = self.output_dir / "filled_forms" / f"{patient_id}_filled_PA.pdf"
            fill_success = self.pdf_filler.fill_form(
                str(pa_form_path),
                field_mappings,
                str(output_form_path)
            )
            
            # Generate report
            missing_fields = self.form_field_mapper.get_missing_fields(
                form_data['fields'],
                field_mappings
            )
            
            report_paths = self.report_generator.generate_report(
                patient_id=patient_id,
                form_name="PA",
                missing_fields=missing_fields,
                confidence_scores=extracted_info.confidence_scores,
                warnings=[] if fill_success else ["Failed to fill form"]
            )
            
            return {
                'patient_id': patient_id,
                'success': fill_success and len(missing_fields) == 0,
                'filled_form_path': str(output_form_path) if fill_success else None,
                'report_paths': report_paths,
                'missing_fields': missing_fields
            }
            
        except Exception as e:
            print(f"Error processing patient {patient_dir.name}: {str(e)}")
            return {
                'patient_id': patient_dir.name,
                'success': False,
                'error': str(e)
            }
    
    def run(self) -> None:
        """Run the pipeline on all patients in the input directory."""
        results = []
        
        # Process each patient directory
        for patient_dir in self.input_dir.iterdir():
            if patient_dir.is_dir():
                result = self.process_patient(patient_dir)
                results.append(result)
                
        # Convert results to FormReport objects
        form_reports = []
        for result in results:
            if 'error' in result:
                # Create a report for failed processing
                report = FormReport(
                    patient_id=result['patient_id'],
                    form_name="PA",
                    timestamp=datetime.now().isoformat(),
                    missing_fields=[],
                    confidence_scores={},
                    warnings=[result['error']],
                    success=False
                )
            else:
                # Create a report from successful processing
                report = FormReport(
                    patient_id=result['patient_id'],
                    form_name="PA",
                    timestamp=datetime.now().isoformat(),
                    missing_fields=[MissingField(**field) for field in result['missing_fields']],
                    confidence_scores=result.get('confidence_scores', {}),
                    warnings=[] if result['success'] else ["Failed to fill form"],
                    success=result['success']
                )
            form_reports.append(report)
                
        # Generate summary report
        self.report_generator.generate_summary_report(form_reports)
        
        # Print summary
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        print(f"\nProcessing complete:")
        print(f"Total patients processed: {total}")
        print(f"Successfully filled forms: {successful}")
        print(f"Forms with missing information: {total - successful}")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="PA Form Filling Automation Pipeline")
    parser.add_argument("--input_dir", required=True, help="Directory containing input data")
    parser.add_argument("--output_dir", required=True, help="Directory to save output files")
    parser.add_argument("--tesseract_cmd", help="Path to tesseract executable")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = PAFormFillingPipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        tesseract_cmd=args.tesseract_cmd
    )
    
    pipeline.run()

if __name__ == "__main__":
    main() 