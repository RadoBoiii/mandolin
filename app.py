from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Import our existing workflow functions
from pa_form_automation_workflow import (
    extract_text_from_pdf,
    extract_info_with_openai,
    map_to_pa_form_fields
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('output/filled_forms', exist_ok=True)
os.makedirs('output/reports', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-env')
def test_env():
    """Test endpoint to check if environment variables are loaded"""
    api_key = os.getenv('OPENAI_API_KEY')
    return jsonify({
        'api_key_found': bool(api_key),
        'api_key_preview': f"{api_key[:10]}...{api_key[-4:]}" if api_key and len(api_key) > 14 else "Not found or too short"
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        result = process_pdf_file(filepath)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': 'Processing failed',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500

def process_pdf_file(filepath):
    """Process a PDF file through the automation workflow"""
    try:
        # Step 1: Extract text from PDF
        print(f"Processing: {filepath}")
        extracted_text = extract_text_from_pdf(filepath)
        
        if not extracted_text.strip():
            return {
                'error': 'No text could be extracted from the PDF. The file might be corrupted or contain only images.',
                'extracted_text': ''
            }
        
        print(f"Extracted text length: {len(extracted_text)}")
        
        # Step 2: Extract structured info with OpenAI
        print("Extracting structured info with OpenAI...")
        try:
            info_json = extract_info_with_openai(extracted_text)
            print(f"OpenAI response: {info_json}")
        except Exception as openai_error:
            print(f"OpenAI extraction failed: {str(openai_error)}")
            return {
                'error': f'OpenAI extraction failed: {str(openai_error)}',
                'extracted_text': extracted_text[:1000] + '...' if len(extracted_text) > 1000 else extracted_text
            }
        
        # Step 3: Map to PA form fields
        try:
            pa_fields = map_to_pa_form_fields(info_json)
            print(f"Mapped fields: {pa_fields}")
        except Exception as mapping_error:
            print(f"Field mapping failed: {str(mapping_error)}")
            return {
                'error': f'Field mapping failed: {str(mapping_error)}',
                'extracted_text': extracted_text[:1000] + '...' if len(extracted_text) > 1000 else extracted_text,
                'structured_info': str(info_json)
            }
        
        # Step 4: Generate report
        try:
            report = generate_processing_report(filepath, extracted_text, info_json, pa_fields)
        except Exception as report_error:
            print(f"Report generation failed: {str(report_error)}")
            report = f"Report generation failed: {str(report_error)}"
        
        return {
            'success': True,
            'filename': os.path.basename(filepath),
            'extracted_text': extracted_text[:1000] + '...' if len(extracted_text) > 1000 else extracted_text,
            'structured_info': info_json,
            'pa_form_fields': pa_fields,
            'report': report
        }
    
    except Exception as e:
        print(f"Unexpected error in process_pdf_file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Error processing PDF: {str(e)}")

def generate_processing_report(filepath, extracted_text, info_json, pa_fields):
    """Generate a processing report"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Safely parse JSON
        if isinstance(info_json, str):
            try:
                structured_data = json.loads(info_json)
            except json.JSONDecodeError:
                structured_data = {"error": "Failed to parse JSON", "raw": info_json}
        else:
            structured_data = info_json
    except Exception:
        structured_data = {"error": "Unknown format", "raw": str(info_json)}
    
    report = f"""
# PA Form Automation Processing Report

**File Processed:** {os.path.basename(filepath)}
**Processing Time:** {timestamp}

## Extracted Information

### Structured Data
```json
{json.dumps(structured_data, indent=2)}
```

### PA Form Fields
"""
    
    for field, value in pa_fields.items():
        report += f"- **{field}:** {value}\n"
    
    report += f"""
## Raw Extracted Text
```
{extracted_text[:500]}...
```

---
*Report generated by PA Form Automation System*
"""
    
    # Save report to file
    report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join('output/reports', report_filename)
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    return report

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Check environment on startup
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✓ OpenAI API key loaded: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("✗ WARNING: OpenAI API key not found!")
        print("Make sure you have a .env file with OPENAI_API_KEY=your-key")
    
    app.run(debug=True, host='0.0.0.0', port=5001)