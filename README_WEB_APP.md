# PA Form Automation Web Application

A modern web application for automating the processing of referral packages and extracting patient information for PA (Prior Authorization) forms.

## Features

- **Drag & Drop File Upload**: Easy PDF upload with drag-and-drop functionality
- **Real-time Processing**: Live progress updates during file processing
- **AI-Powered Extraction**: Uses OpenAI to extract structured information from PDFs
- **Modern UI**: Clean, responsive interface built with Tailwind CSS
- **Report Generation**: Automatic generation of processing reports
- **Multiple Output Formats**: JSON, structured data, and markdown reports

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Tesseract OCR (for image-based PDF processing)

### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd mandolin
   ```

2. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Or create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Running the Application

### Option 1: Using the run script
```bash
python run_app.py
```

### Option 2: Direct Flask run
```bash
python app.py
```

### Option 3: Using Flask CLI
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

The application will start on `http://localhost:5000`

## Usage

1. **Open your browser** and navigate to `http://localhost:5000`

2. **Upload a PDF file** by either:
   - Dragging and dropping a PDF file onto the upload area
   - Clicking "Browse Files" to select a file

3. **Wait for processing** - The application will:
   - Extract text from the PDF
   - Use OpenAI to extract structured information
   - Map the information to PA form fields
   - Generate a processing report

4. **Review results** - The application displays:
   - **PA Form Fields**: Extracted information mapped to form fields
   - **Structured Information**: Raw JSON data from OpenAI
   - **Text Preview**: First 1000 characters of extracted text

5. **Download reports** - Click "Download Report" to save a markdown report

## File Structure

```
mandolin/
├── app.py                          # Main Flask application
├── run_app.py                      # Application startup script
├── pa_form_automation_workflow.py  # Core processing logic
├── templates/
│   └── index.html                  # Web interface
├── static/                         # Static assets (CSS, JS)
├── uploads/                        # Temporary file uploads
├── output/
│   ├── filled_forms/               # Generated filled forms
│   └── reports/                    # Processing reports
└── requirements.txt                # Python dependencies
```

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - File upload and processing endpoint
- `GET /health` - Health check endpoint

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `FLASK_ENV` - Set to 'development' for debug mode
- `FLASK_APP` - Set to 'app.py' for Flask CLI

### Application Settings

You can modify these settings in `app.py`:

- `MAX_CONTENT_LENGTH` - Maximum file upload size (default: 16MB)
- `UPLOAD_FOLDER` - Directory for temporary file uploads
- `SECRET_KEY` - Flask secret key for sessions

## Troubleshooting

### Common Issues

1. **"No text could be extracted from the PDF"**
   - The PDF might be image-based or corrupted
   - Ensure Tesseract OCR is properly installed
   - Try with a different PDF file

2. **OpenAI API errors**
   - Verify your API key is correct
   - Check your OpenAI account has sufficient credits
   - Ensure the API key has the necessary permissions

3. **File upload errors**
   - Check file size (max 16MB)
   - Ensure file is a valid PDF
   - Verify upload directory permissions

4. **Port already in use**
   - Change the port in `app.py` or `run_app.py`
   - Kill existing processes using the port

### Debug Mode

To enable debug mode for more detailed error messages:

```bash
export FLASK_ENV=development
python app.py
```

## Security Considerations

- The application processes sensitive medical documents
- Uploaded files are automatically deleted after processing
- Consider implementing authentication for production use
- Use HTTPS in production environments
- Regularly update dependencies for security patches

## Production Deployment

For production deployment, consider:

1. **Web Server**: Use Gunicorn or uWSGI with Nginx
2. **Environment**: Set `FLASK_ENV=production`
3. **Security**: Implement proper authentication and HTTPS
4. **Monitoring**: Add logging and monitoring
5. **Backup**: Implement regular backups of processed data

Example Gunicorn deployment:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 