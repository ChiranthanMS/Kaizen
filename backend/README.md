# Travel Expense API Backend

A comprehensive FastAPI-based backend for travel expense management with OCR capabilities, user authentication, and bill processing.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- PostgreSQL (optional, for advanced features)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```

3. **Start the server:**
   ```bash
   python start_server.py
   ```
   
   Or manually:
   ```bash
   python main.py
   ```

4. **Test the API:**
   ```bash
   python test_server.py
   ```

## 📋 Features

### ✅ Fixed Issues
- **Authentication System**: JWT-based authentication with role-based access control
- **Database Integration**: MongoDB primary storage with PostgreSQL support
- **OCR Processing**: Multiple OCR engines (Tesseract, OCR.space, Google Vision)
- **Bill Processing**: AI-powered bill analysis and expense categorization
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Configured for frontend integration

### 🔧 Recent Fixes
1. **Deprecated FastAPI Events**: Replaced `@app.on_event` with modern lifespan handlers
2. **Authentication Dependencies**: Unified auth system using proper dependency injection
3. **Circular Imports**: Fixed circular import issues in PostgreSQL routes
4. **JWT Token Handling**: Consistent token creation and validation
5. **Route Dependencies**: Updated all routes to use centralized auth dependencies
6. **OAuth2 Configuration**: Proper OAuth2PasswordBearer setup
7. **Error Messages**: Improved error messages and validation

## 🛠 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /google-login` - Google OAuth login
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset confirmation
- `GET /profile` - Get user profile
- `GET /google-client-id` - Get Google client ID

### OCR & Bill Processing
- `POST /ocr/extract-text` - Extract text from images/PDFs
- `POST /bills/process-bill` - Full bill processing (OCR + parsing)
- `POST /bills/extract-text-only` - OCR only
- `POST /bills/parse-text` - Parse text for financial data
- `GET /bills/categories` - Get expense categories

### Health Checks
- `GET /` - API health check
- `GET /ocr/health` - OCR service health
- `GET /bills/health` - Bill processing health

## 🔐 Authentication

The API uses JWT tokens for authentication. Include the token in requests:

```bash
Authorization: Bearer <your-jwt-token>
```

### User Roles
- **Employee**: Can process their own bills and expenses
- **Manager**: Can view and manage team expenses

## 📊 Database Schema

### MongoDB Collections
- `users` - User accounts and profiles
- `password_resets` - Password reset tokens

### PostgreSQL Tables (Optional)
- `app_users` - User data sync from MongoDB
- `app_bills` - Processed bills and expenses

## 🔧 Configuration

### Environment Variables

```env
# Database
MONGO_URI=mongodb://localhost:27017/
POSTGRES_URL=postgresql://user:pass@localhost:5432/db

# Authentication
JWT_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id

# Email
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM=your-email@domain.com

# OCR Services
OCR_SPACE_API_KEY=your-ocr-space-key
GOOGLE_VISION_API_KEY=your-google-vision-key
GEMINI_API_KEY=your-gemini-key
```

## 🧪 Testing

Run the test suite:
```bash
python test_server.py
```

This will test:
- Health endpoints
- User registration
- User login
- Protected routes

## 📝 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MONGO_URI in .env
   - Ensure MongoDB is running
   - Server will use in-memory storage as fallback

2. **PostgreSQL Connection Failed**
   - Check POSTGRES_URL in .env
   - PostgreSQL features will be disabled but server continues

3. **OCR Not Working**
   - Check OCR_SPACE_API_KEY in .env
   - Verify file formats (jpg, png, pdf)
   - Check file size limits (10MB max)

4. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Logs
Server logs provide detailed information about:
- Database connections
- Route loading status
- Authentication attempts
- OCR processing
- Error details

## 🔄 Development

### Project Structure
```
backend/
├── main.py                 # FastAPI app and main routes
├── start_server.py         # Server startup script
├── test_server.py          # API testing script
├── database.py             # Database connections
├── requirements.txt        # Python dependencies
├── models/                 # Pydantic models
├── routes/                 # API route modules
├── services/               # Business logic services
└── dependencies/           # Dependency injection
```

### Adding New Features
1. Create models in `models/`
2. Add business logic in `services/`
3. Create routes in `routes/`
4. Update dependencies in `dependencies/`
5. Include router in `main.py`

## 📄 License

This project is part of the Travel Expense Management System.