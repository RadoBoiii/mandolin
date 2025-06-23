from typing import Dict, List, Optional
import os
from datetime import datetime
import json
from dataclasses import dataclass, asdict

@dataclass
class MissingField:
    """Class representing a missing form field."""
    name: str
    type: str
    reason: str
    description: Optional[str] = None
    suggested_value: Optional[str] = None

@dataclass
class FormReport:
    """Class representing a form filling report."""
    patient_id: str
    form_name: str
    timestamp: str
    missing_fields: List[MissingField]
    confidence_scores: Dict[str, float]
    warnings: List[str]
    success: bool

class ReportGenerator:
    """Class for generating missing information reports."""
    
    def __init__(self, output_dir: str):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(self, patient_id: str, form_name: str,
                       missing_fields: List[Dict], confidence_scores: Dict[str, float],
                       warnings: Optional[List[str]] = None) -> str:
        """
        Generate a missing information report.
        
        Args:
            patient_id: Patient identifier
            form_name: Name of the form
            missing_fields: List of missing field dictionaries
            confidence_scores: Dictionary of confidence scores
            warnings: Optional list of warnings
            
        Returns:
            Path to the generated report
        """
        # Create report object
        report = FormReport(
            patient_id=patient_id,
            form_name=form_name,
            timestamp=datetime.now().isoformat(),
            missing_fields=[MissingField(**field) for field in missing_fields],
            confidence_scores=confidence_scores,
            warnings=warnings or [],
            success=len(missing_fields) == 0
        )
        
        # Generate report in multiple formats
        report_paths = {
            'json': self._generate_json_report(report),
            'markdown': self._generate_markdown_report(report),
            'text': self._generate_text_report(report)
        }
        
        return report_paths
    
    def _generate_json_report(self, report: FormReport) -> str:
        """
        Generate a JSON report.
        
        Args:
            report: FormReport object
            
        Returns:
            Path to the JSON report
        """
        report_path = os.path.join(
            self.output_dir,
            f"{report.patient_id}_{report.form_name}_report.json"
        )
        
        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
            
        return report_path
    
    def _generate_markdown_report(self, report: FormReport) -> str:
        """
        Generate a Markdown report.
        
        Args:
            report: FormReport object
            
        Returns:
            Path to the Markdown report
        """
        report_path = os.path.join(
            self.output_dir,
            f"{report.patient_id}_{report.form_name}_report.md"
        )
        
        with open(report_path, 'w') as f:
            f.write(f"# Form Filling Report\n\n")
            f.write(f"**Patient ID:** {report.patient_id}\n")
            f.write(f"**Form Name:** {report.form_name}\n")
            f.write(f"**Timestamp:** {report.timestamp}\n")
            f.write(f"**Status:** {'Success' if report.success else 'Missing Information'}\n\n")
            
            if report.missing_fields:
                f.write("## Missing Fields\n\n")
                for field in report.missing_fields:
                    f.write(f"### {field.name}\n")
                    f.write(f"- Type: {field.type}\n")
                    f.write(f"- Reason: {field.reason}\n")
                    if field.description:
                        f.write(f"- Description: {field.description}\n")
                    if field.suggested_value:
                        f.write(f"- Suggested Value: {field.suggested_value}\n")
                    f.write("\n")
                    
            if report.warnings:
                f.write("## Warnings\n\n")
                for warning in report.warnings:
                    f.write(f"- {warning}\n")
                f.write("\n")
                
            f.write("## Confidence Scores\n\n")
            for field, score in report.confidence_scores.items():
                f.write(f"- {field}: {score:.2f}\n")
                
        return report_path
    
    def _generate_text_report(self, report: FormReport) -> str:
        """
        Generate a plain text report.
        
        Args:
            report: FormReport object
            
        Returns:
            Path to the text report
        """
        report_path = os.path.join(
            self.output_dir,
            f"{report.patient_id}_{report.form_name}_report.txt"
        )
        
        with open(report_path, 'w') as f:
            f.write("FORM FILLING REPORT\n")
            f.write("==================\n\n")
            f.write(f"Patient ID: {report.patient_id}\n")
            f.write(f"Form Name: {report.form_name}\n")
            f.write(f"Timestamp: {report.timestamp}\n")
            f.write(f"Status: {'Success' if report.success else 'Missing Information'}\n\n")
            
            if report.missing_fields:
                f.write("MISSING FIELDS\n")
                f.write("-------------\n\n")
                for field in report.missing_fields:
                    f.write(f"Field: {field.name}\n")
                    f.write(f"Type: {field.type}\n")
                    f.write(f"Reason: {field.reason}\n")
                    if field.description:
                        f.write(f"Description: {field.description}\n")
                    if field.suggested_value:
                        f.write(f"Suggested Value: {field.suggested_value}\n")
                    f.write("\n")
                    
            if report.warnings:
                f.write("WARNINGS\n")
                f.write("--------\n\n")
                for warning in report.warnings:
                    f.write(f"- {warning}\n")
                f.write("\n")
                
            f.write("CONFIDENCE SCORES\n")
            f.write("----------------\n\n")
            for field, score in report.confidence_scores.items():
                f.write(f"{field}: {score:.2f}\n")
                
        return report_path
    
    def generate_summary_report(self, reports: List[FormReport]) -> str:
        """
        Generate a summary report of multiple form filling reports.
        
        Args:
            reports: List of FormReport objects
            
        Returns:
            Path to the summary report
        """
        summary_path = os.path.join(self.output_dir, "summary_report.md")
        
        with open(summary_path, 'w') as f:
            f.write("# Form Filling Summary Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # Summary statistics
            total_forms = len(reports)
            successful_forms = sum(1 for r in reports if r.success)
            forms_with_missing = total_forms - successful_forms
            
            f.write("## Summary Statistics\n\n")
            f.write(f"- Total Forms Processed: {total_forms}\n")
            f.write(f"- Successfully Filled: {successful_forms}\n")
            f.write(f"- Forms with Missing Information: {forms_with_missing}\n\n")
            
            # Detailed report
            f.write("## Detailed Report\n\n")
            for report in reports:
                f.write(f"### {report.form_name} ({report.patient_id})\n")
                f.write(f"- Status: {'Success' if report.success else 'Missing Information'}\n")
                f.write(f"- Missing Fields: {len(report.missing_fields)}\n")
                f.write(f"- Warnings: {len(report.warnings)}\n")
                f.write("\n")
                
        return summary_path 