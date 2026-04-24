# Travel Expense Auditing System

## Overview

This is a comprehensive travel expense auditing system built with FastAPI backend and React frontend. The system provides intelligent bill processing that extracts structured financial data from uploaded receipts and bills using OCR technology.

## 🚀 Features

### ✅ Completed Features

1. **User Authentication**
   - JWT-based authentication
   - User registration and login
   - Google OAuth integration
   - Password reset functionality

2. **OCR Text Extraction**
   - Support for images (JPG, PNG, BMP, TIFF, GIF)
   - PDF text extraction
   - Cloud-based OCR (OCR.space API)
   - Fallback OCR (EasyOCR)

3. **Intelligent Bill Processing**
   - Automatic financial data extraction
   - Expense categorization
   - Amount validation and calculation
   - Date and vendor identification
   - Confidence scoring

4. **Modern Web Interface**
   - Responsive React frontend
   - Drag-and-drop file upload
   - Real-time processing feedback
   - Structured data display
   - Export functionality

## 🏗️ System Architecture

### Backend (FastAPI)
```
backend/
├── main.py                     # Main application entry point
├── models/
│   ├── bill_models.py         # Bill processing data models
│   └── ocr_models.py          # OCR data models
├── services/
│   ├── bill_processing_service.py  # Intelligent bill processing
│   ├── ocr_service.py             # Full OCR service
│   └── ocr_service_simple.py     # Simple OCR service
├── routes/
│   ├── bill_routes.py         # Bill processing endpoints
│   ├── ocr_routes.py          # OCR endpoints
│   └── ocr_routes_simple.py   # Simple OCR endpoints
└── requirements.txt           # Python dependencies
```

### Frontend (React)
```
frontend/src/
├── App.js                     # Main app with routing
├── components/
│   ├── AuthPage.js           # Authentication interface
│   ├── ProfilePage.js        # User profile
│   ├── OCRPage.js           # OCR text extraction
│   ├── BillProcessingPage.js # Bill processing interface
│   └── ProtectedRoute.js    # Route protection
├── styles.css               # Application styles
└── package.json            # Node.js dependencies
```

## 📊 Bill Processing Capabilities

### Supported Data Extraction

1. **Financial Information**
   - Total amount
   - Subtotal (before tax)
   - Tax amount
   - Discount amount
   - Currency detection

2. **Metadata**
   - Transaction date
   - Vendor/store name
   - Expense category
   - Additional remarks

3. **Expense Categories**
   - Food & Dining
   - Transportation
   - Lodging
   - Fuel
   - Entertainment
   - Office Supplies
   - Communication
   - Medical
   - Miscellaneous

### Processing Intelligence

- **Pattern Recognition**: Uses regex patterns to identify financial data
- **Category Classification**: Keyword-based automatic categorization
- **Amount Validation**: Cross-validates totals, subtotals, and taxes
- **Confidence Scoring**: Provides accuracy confidence (0-1 scale)
- **Error Detection**: Identifies inconsistencies and potential issues

## 🔌 API Endpoints

### Authentication Endpoints
- `POST /register` - User registration
- `POST /login` - User login
- `POST /google-login` - Google OAuth login
- `GET /profile` - Get user profile
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password

### OCR Endpoints
- `POST /ocr/extract-text` - Extract text from image/PDF
- `GET /ocr/health` - OCR service health check

### Bill Processing Endpoints
- `POST /bills/process-bill` - Process bill and extract financial data
- `POST /bills/extract-text-only` - Extract text only (no processing)
- `POST /bills/parse-text` - Parse raw text for financial data
- `GET /bills/categories` - Get supported expense categories
- `GET /bills/health` - Bill processing service health check

## 📝 Sample API Response

### Successful Bill Processing
```json
{
  "success": true,
  "filename": "restaurant_receipt.jpg",
  "file_type": "jpg",
  "raw_text": "Mario's Italian Restaurant\nDate: 01/15/2025\nSubtotal: $38.50\nTax: $7.25\nTotal: $45.75\nThank you!",
  "financial_data": {
    "date": "2025-01-15",
    "vendor": "Mario's Italian Restaurant",
    "category": "food",
    "amount": 45.75,
    "subtotal": 38.50,
    "tax": 7.25,
    "discount": null,
    "currency": "USD",
    "remarks": null
  },
  "confidence_score": 0.92,
  "processing_time": 2.34,
  "warnings": []
}
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB database
- OCR.space API key (optional, for better accuracy)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Environment Configuration
```env
# Database
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/auth_db

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id

# Email
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM=your_email@domain.com

# OCR (Optional)
OCR_SPACE_API_KEY=your_ocr_space_api_key
```

## 🔒 Security Features

1. **JWT Authentication**: All bill processing endpoints require valid JWT tokens
2. **Input Validation**: File type, size, and content validation
3. **Rate Limiting**: Prevents abuse of OCR and processing services
4. **Error Handling**: Secure error messages without sensitive data exposure
5. **CORS Configuration**: Proper cross-origin resource sharing setup

## 📈 Performance Considerations

### Processing Optimization
- **Async Processing**: Non-blocking OCR and bill processing
- **Timeout Handling**: 60-second timeout for processing operations
- **Memory Management**: Efficient file handling without permanent storage
- **Caching**: Potential for result caching (future enhancement)

### Scalability
- **Modular Architecture**: Easy to scale individual components
- **API-based OCR**: Reduces server resource requirements
- **Database Optimization**: Efficient user and session management
- **Load Balancing Ready**: Stateless design supports horizontal scaling

## 🔮 Future Enhancements

### Planned Features
1. **Policy Validation**
   - Company travel policy enforcement
   - Spending limit validation
   - Category restrictions

2. **Approval Workflow**
   - Hierarchy-based approvals
   - Multi-level review process
   - Automated notifications

3. **Advanced Analytics**
   - Expense reporting and dashboards
   - Spending pattern analysis
   - Budget tracking

4. **Integration Capabilities**
   - Accounting software integration
   - ERP system connectivity
   - Mobile app development

### Technical Improvements
1. **Enhanced OCR**
   - Multi-language support
   - Handwriting recognition
   - Table extraction

2. **Machine Learning**
   - Improved category classification
   - Fraud detection
   - Spending anomaly detection

3. **Data Management**
   - Expense history storage
   - Advanced search capabilities
   - Data export options

## 🧪 Testing

### Manual Testing
1. **Authentication Flow**
   - Register new user
   - Login with credentials
   - Test Google OAuth
   - Password reset functionality

2. **Bill Processing**
   - Upload various receipt types
   - Test different file formats
   - Verify data extraction accuracy
   - Check error handling

3. **User Interface**
   - Responsive design testing
   - Cross-browser compatibility
   - Mobile device testing

### Automated Testing (Future)
- Unit tests for processing logic
- Integration tests for API endpoints
- End-to-end testing for user workflows
- Performance testing for large files

## 📞 Support and Maintenance

### Monitoring
- Application logs for debugging
- Performance metrics tracking
- Error rate monitoring
- User activity analytics

### Maintenance Tasks
- Regular dependency updates
- Security patch management
- Database optimization
- OCR API usage monitoring

## 📄 License and Compliance

- Ensure compliance with data protection regulations
- Implement proper data retention policies
- Regular security audits
- User privacy protection measures

---

## Quick Start Guide

1. **Clone the repository**
2. **Set up environment variables**
3. **Install dependencies** (backend and frontend)
4. **Start MongoDB** database
5. **Run backend server** on port 8000
6. **Run frontend server** on port 3000
7. **Access application** at http://localhost:3000
8. **Register/login** and start processing bills!

For detailed setup instructions, see the individual README files in the backend and frontend directories.