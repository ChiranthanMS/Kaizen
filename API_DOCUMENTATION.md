# Travel Expense Auditing API Documentation

## Overview

This is a comprehensive FastAPI backend for a travel expense auditing software with role-based access control, PostgreSQL storage, OCR functionality, and advanced analytics.

## Features

- **Role-based Authentication**: Employee and Manager roles with JWT tokens
- **OCR Processing**: Extract text and financial data from bill images/PDFs
- **PostgreSQL Storage**: Structured bill data storage with relationships
- **Manager Dashboard**: Comprehensive team management and approval workflows
- **Analytics & Reporting**: Expense trends, category breakdowns, anomaly detection
- **Policy Validation**: Extensible policy framework for expense validation
- **Modular Architecture**: Separate services for auth, OCR, database, analytics

## Base URL

```
http://localhost:8000
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### Authentication Endpoints

#### POST `/register`
Register a new user with role-based access.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "employee",  // or "manager"
  "full_name": "John Doe",
  "department": "Sales",
  "manager_id": "123"  // Required for employees
}
```

**Response:**
```json
{
  "access_token": "",
  "token_type": "bearer",
  "message": "User registered successfully as employee! Please login with your credentials."
}
```

#### POST `/login`
Login with email/username and password.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "message": "Welcome, Employee John Doe!"
}
```

### Bill Processing Endpoints

#### POST `/bills/process-bill`
Process and store a bill image/PDF (Employee only).

**Request:**
- Content-Type: `multipart/form-data`
- File: Image or PDF file (max 10MB)

**Response:**
```json
{
  "success": true,
  "bill_id": 123,
  "message": "Bill processed and stored successfully! Bill ID: 123",
  "bill_data": {
    "id": 123,
    "employee_id": 456,
    "amount": 45.67,
    "date": "2024-01-15",
    "vendor": "Restaurant ABC",
    "category": "food",
    "status": "pending"
  }
}
```

#### GET `/bills/my-bills`
Get bills uploaded by current employee.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "bills": [...],
  "total_count": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

#### GET `/bills/view-bills`
View bills based on user role:
- Employees: only their own bills
- Managers: all bills from their team

#### POST `/bills/parse-precise`
**NEW**: Precise financial document parser that converts OCR text into clean JSON following exact schema requirements.

**Request:**
- Content-Type: `multipart/form-data`
- File: Image or PDF file (max 10MB)

**Response:**
Returns clean JSON following exact schema (no wrapper objects):
```json
{
  "date": "2024-01-15",
  "vendor": "Burger Palace",
  "bill_type": "food",
  "currency": "USD",
  "subtotal": 22.5,
  "tax_rate_percent": 8.5,
  "tax_amount": 1.91,
  "total_amount": 24.41,
  "discount_amount": null,
  "remarks": "Thank you for visiting!",
  "line_items": [
    {
      "description": "Cheeseburger",
      "quantity": 2.0,
      "unit_price": 8.5,
      "total_price": 17.0
    }
  ]
}
```

**Bill Type Classification:**
- `"rent"`: Hotels, accommodation, lodging, apartments
- `"travel"`: Taxi, flights, transport, fuel, parking
- `"food"`: Restaurants, cafes, dining, groceries

#### POST `/bills/parse-text-precise`
**NEW**: Parse raw text using precise parser (no OCR, text processing only).

**Request Body:**
```json
{
  "text": "BURGER PALACE\nDate: 2024-01-15\n2x Burger $8.50 $17.00\nTotal: $17.00"
}
```

**Response:**
Same clean JSON format as `/bills/parse-precise`

### Manager Endpoints

#### GET `/manager/team-overview`
Get overview of all employees under the manager (Manager only).

**Response:**
```json
[
  {
    "employee_id": 456,
    "employee_name": "John Doe",
    "employee_email": "john@example.com",
    "department": "Sales",
    "total_bills": 15,
    "total_amount": 1250.50,
    "pending_bills": 3,
    "approved_bills": 10,
    "rejected_bills": 2,
    "last_submission": "2024-01-15T10:30:00"
  }
]
```

#### GET `/manager/pending-bills`
Get all pending bills for approval (Manager only).

#### POST `/manager/bills/{bill_id}/approve`
Approve a bill (Manager only).

**Request Body (optional):**
```json
{
  "remarks": "Approved - valid business expense"
}
```

#### POST `/manager/bills/{bill_id}/reject`
Reject a bill (Manager only).

**Request Body (optional):**
```json
{
  "remarks": "Rejected - missing receipt details"
}
```

### Analytics Endpoints

#### GET `/analytics/expense-trends`
Get expense trends over time.

**Query Parameters:**
- `days`: Number of days to analyze (1-365, default: 30)

**Response:**
```json
{
  "period": "2023-12-16 to 2024-01-15",
  "trends": [
    {
      "expense_date": "2024-01-15",
      "bill_count": 5,
      "total_amount": 234.56,
      "avg_amount": 46.91
    }
  ],
  "summary": {
    "total_days": 30,
    "total_bills": 45,
    "total_amount": 2345.67,
    "avg_daily_amount": 78.19
  }
}
```

#### GET `/analytics/category-breakdown`
Get breakdown of expenses by category.

#### GET `/analytics/employee-rankings`
Get employee expense rankings (Manager only).

#### GET `/analytics/approval-metrics`
Get approval/rejection metrics (Manager only).

#### GET `/analytics/monthly-summary`
Get monthly expense summary.

#### GET `/analytics/anomalies`
Detect expense anomalies (unusually high amounts).

#### GET `/analytics/dashboard-summary`
Get comprehensive dashboard summary combining multiple analytics.

### Health Check Endpoints

#### GET `/`
Basic API health check.

#### GET `/bills/health`
Bill processing service health check.

#### GET `/analytics/health`
Analytics service health check.

## Data Models

### User Model
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "role": "employee|manager",
  "full_name": "string",
  "department": "string",
  "manager_id": "string",
  "created_at": "datetime"
}
```

### Bill Model
```json
{
  "id": "integer",
  "employee_id": "integer",
  "filename": "string",
  "file_type": "string",
  "date": "date",
  "vendor": "string",
  "category": "string",
  "amount": "decimal",
  "subtotal": "decimal",
  "tax": "decimal",
  "discount": "decimal",
  "currency": "string",
  "remarks": "string",
  "raw_text": "string",
  "confidence_score": "decimal",
  "processing_time": "decimal",
  "status": "pending|approved|rejected|under_review",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied. Required roles: manager"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

## Supported File Types

- **Images**: JPG, JPEG, PNG, BMP, TIFF, GIF
- **Documents**: PDF
- **Max Size**: 10MB per file

## Expense Categories

- food
- transport
- lodging
- fuel
- entertainment
- office_supplies
- communication
- medical
- miscellaneous

## Bill Status Values

- **pending**: Awaiting manager approval
- **approved**: Approved by manager
- **rejected**: Rejected by manager
- **under_review**: Under additional review

## Rate Limits

- File uploads: 10MB max size
- API requests: Standard rate limiting applied
- Database queries: Optimized with pagination

## Security Features

- JWT token authentication
- Role-based access control
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection prevention
- File type validation

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'employee',
    department VARCHAR(50),
    manager_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bills Table
```sql
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(10),
    date DATE,
    vendor VARCHAR(200),
    category VARCHAR(50),
    amount DECIMAL(10, 2),
    subtotal DECIMAL(10, 2),
    tax DECIMAL(10, 2),
    discount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    remarks TEXT,
    raw_text TEXT,
    confidence_score DECIMAL(3, 2),
    processing_time DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

```env
# MongoDB (for user credentials)
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/auth_db

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here

# Email Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM=your_email@domain.com

# OCR Configuration
OCR_SPACE_API_KEY=your_ocr_space_api_key

# PostgreSQL Configuration
POSTGRES_URL=postgresql://user:pass@host:5432/database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=travel_expense_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

## Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Set Environment Variables:**
   - Copy `.env.example` to `.env`
   - Update with your actual credentials

3. **Setup Databases:**
   - MongoDB for user authentication
   - PostgreSQL for bill data storage

4. **Run the Application:**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Frontend Integration

The system includes React components for:

- **Employee Dashboard** (`/upload-bill`): Bill upload and management
- **Manager Dashboard** (`/team-bills`): Team oversight and approvals
- **Authentication**: Role-based login/registration
- **Analytics**: Charts and reports

## Extensibility

The system is designed for easy extension:

### Policy Framework
Add custom expense policies by extending the `ExpensePolicy` class:

```python
class CustomPolicy(ExpensePolicy):
    def validate(self, bill_data, user_data):
        # Custom validation logic
        return violations
```

### Analytics
Add new analytics by extending the `AnalyticsService`:

```python
async def custom_analysis(self, params):
    # Custom analytics logic
    return results
```

### Approval Workflows
Extend the manager routes for multi-level approvals:

```python
@router.post("/bills/{bill_id}/escalate")
async def escalate_approval(bill_id: int):
    # Escalation logic
    pass
```

## Testing

Run tests with:
```bash
pytest backend/tests/
```

## Deployment

The application is ready for deployment on:
- **Cloud Platforms**: AWS, GCP, Azure
- **Container Platforms**: Docker, Kubernetes
- **Database Services**: Supabase, AWS RDS, Google Cloud SQL

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review error messages and status codes
3. Check logs for detailed error information
4. Ensure all environment variables are properly set