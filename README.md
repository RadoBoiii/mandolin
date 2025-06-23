# Prior Authorization (PA) Form Filling Automation

This project automates the process of filling Prior Authorization (PA) forms using information extracted from referral packages. The system uses OCR, NLP, and PDF processing to extract relevant information and populate PA forms accurately.

## Features

- Automated extraction of information from referral packages using OCR
- Intelligent form field detection and mapping
- Support for both widget-based and non-widget-based PDF forms
- Generation of missing information reports
- Modular and extensible architecture

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd mandolin
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt-get install tesseract-ocr`
- Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Project Structure

```
mandolin/
├── src/                    # Source code
│   ├── document_processor/ # PDF and OCR processing
│   ├── data_extractor/    # Information extraction
│   ├── form_filler/       # Form filling logic
│   └── utils/             # Utility functions
├── tests/                 # Test cases
├── docs/                  # Documentation
└── output_examples/       # Example outputs
```

## Usage

1. Place your input data in the following structure:
```
Input Data/
├── Patient_A/
│   ├── PA.pdf
│   └── referral_package.pdf
├── Patient_B/
│   ├── PA.pdf
│   └── referral_package.pdf
```

2. Run the pipeline:
```bash
python src/main.py --input_dir "Input Data" --output_dir "Output"
```

## Implementation Details

### Document Processing
- Uses OCR (Tesseract) for text extraction from scanned documents
- Implements PDF processing for both widget-based and non-widget forms
- Handles high-resolution images and multi-page documents

### Information Extraction
- Extracts key information from referral packages
- Maps extracted data to corresponding form fields
- Handles conditional logic for form field population

### Form Filling
- Supports both interactive and non-interactive PDF forms
- Generates missing information reports
- Maintains form structure and formatting

## Limitations

1. OCR accuracy depends on image quality
2. Complex form layouts may require manual verification
3. Some fields may require human judgment for interpretation

## Contributing

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Submit a pull request

## License

[Your License Here]
