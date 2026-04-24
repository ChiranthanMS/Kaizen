# Trip Submission Flow Demo Instructions

## Prerequisites
1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:3000`
3. PostgreSQL database connected and tables created
4. At least one manager and one employee user registered

## Demo Flow

### Step 1: Employee Creates Trip Request
1. **Login as Employee**
   - Navigate to `http://localhost:3000/login`
   - Login with employee credentials

2. **Access Trip Dashboard**
   - Go to Trip Budget Dashboard
   - Click "➕ Create Trip Request"

3. **Create Trip**
   ```
   Trip Purpose: Client Meeting in Mumbai
   Destination: Mumbai
   Start Date: Tomorrow
   End Date: Day after tomorrow
   ```
   - System automatically calculates budget based on designation
   - Trip status: PENDING

### Step 2: Manager Approves Trip
1. **Login as Manager**
   - Navigate to `http://localhost:3000/login`
   - Login with manager credentials

2. **Access Manager Dashboard**
   - Go to Manager Dashboard
   - Click "Trip Approvals" tab

3. **Approve Trip**
   - Review trip details and budget
   - Click "Approve Trip"
   - Trip status: APPROVED

### Step 3: Employee Activates Trip
1. **Switch back to Employee**
   - Go to Trip Budget Dashboard
   - Find approved trip
   - Click "🚀 Activate Trip"
   - Trip status: ACTIVE

### Step 4: Employee Submits Expenses During Trip
1. **Upload Bills**
   - Go to Enhanced Bill Upload (`/upload`)
   - Upload restaurant bill (₹500)
   - Upload hotel bill (₹2000)
   - Upload taxi bill (₹300)

2. **Verify Budget Tracking**
   - Bills automatically associated with active trip
   - Real-time budget validation
   - Category-wise budget tracking visible

### Step 5: Employee Completes Trip
1. **Complete Trip**
   - Go back to Trip Budget Dashboard
   - Find active trip
   - Click "✅ Complete Trip"
   - Confirm completion
   - Trip status: COMPLETED

### Step 6: Employee Submits Trip for Approval
1. **Submit for Approval**
   - Find completed trip
   - Click "📤 Submit for Approval"
   - Add optional notes for manager
   - All trip bills submitted together
   - Trip status: SUBMITTED

### Step 7: Manager Reviews Trip Submission
1. **Switch to Manager**
   - Go to Manager Dashboard
   - Click "Trip Submissions" tab

2. **Review Submission**
   - See pending trip submission
   - Click "👁️ View Details"
   - Review complete trip summary:
     - Trip details (purpose, destination, dates)
     - Budget allocation vs actual spending
     - All associated bills in one view
     - Budget utilization percentage

### Step 8: Manager Approves/Rejects
1. **Approve All Bills**
   - Add optional comments
   - Click "✅ Approve All Bills"
   - All trip bills approved collectively

2. **Or Reject with Reason**
   - Click "❌ Reject All Bills"
   - Provide rejection reason
   - All trip bills rejected together

## Key Features to Demonstrate

### 1. Automatic Bill Association
- Show how bills uploaded during active trip are automatically linked
- Demonstrate trip_id association in database

### 2. Real-time Budget Validation
- Upload bill that exceeds category budget
- Show warning message and budget tracking

### 3. Collective Approval
- Show how all trip bills are grouped together
- Demonstrate single approval for entire trip

### 4. Budget Utilization Tracking
- Show real-time budget usage calculations
- Demonstrate visual indicators for budget compliance

### 5. Complete Audit Trail
- Show trip lifecycle from creation to approval
- Demonstrate status tracking and timestamps

## API Testing with Postman/curl

### Create Trip Request
```bash
curl -X POST "http://localhost:8000/trip-budget/create-trip" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_purpose": "Client Meeting",
    "destination_city": "Mumbai",
    "start_date": "2024-01-20",
    "end_date": "2024-01-22"
  }'
```

### Get Pending Trip Submissions (Manager)
```bash
curl -X GET "http://localhost:8000/trip-budget/pending-trip-submissions" \
  -H "Authorization: Bearer MANAGER_TOKEN"
```

### Approve Trip Submission
```bash
curl -X POST "http://localhost:8000/trip-budget/approve-trip-submission" \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": 1,
    "comments": "Approved - expenses are reasonable"
  }'
```

## Database Verification

### Check Trip Submissions
```sql
SELECT * FROM app_trip_submissions ORDER BY submitted_at DESC;
```

### Check Bills with Trip Association
```sql
SELECT id, filename, amount, trip_id, trip_status 
FROM app_bills 
WHERE trip_id IS NOT NULL 
ORDER BY created_at DESC;
```

### Check Trip Budget Utilization
```sql
SELECT 
    ts.trip_id,
    ts.employee_name,
    ts.allocated_budget,
    ts.total_amount,
    ts.budget_utilization,
    COUNT(b.id) as actual_bills
FROM app_trip_submissions ts
LEFT JOIN app_bills b ON b.trip_id = ts.trip_id
GROUP BY ts.id, ts.trip_id, ts.employee_name, ts.allocated_budget, ts.total_amount, ts.budget_utilization;
```

## Expected Results

### Successful Demo Shows:
1. ✅ Seamless trip creation and approval workflow
2. ✅ Automatic bill association during active trips
3. ✅ Real-time budget validation and tracking
4. ✅ Collective trip submission and approval
5. ✅ Complete audit trail and status tracking
6. ✅ Manager dashboard with comprehensive trip overview
7. ✅ Employee dashboard with clear trip status
8. ✅ Database integrity and proper data relationships

### Performance Metrics:
- Trip creation: < 1 second
- Bill upload with validation: < 2 seconds
- Trip submission: < 1 second
- Manager approval: < 1 second
- Real-time budget updates: Immediate

## Troubleshooting

### Common Issues:
1. **Bills not associating with trip**: Check if trip is in ACTIVE status
2. **Budget validation failing**: Verify trip budget allocation
3. **Submission not appearing**: Check manager_id mapping
4. **Frontend not updating**: Refresh page or check API responses

### Debug Commands:
```bash
# Check backend logs
tail -f backend/logs/app.log

# Check database connections
psql -h localhost -U postgres -d your_database

# Verify API endpoints
curl -X GET "http://localhost:8000/docs"
```

This demo showcases a complete, production-ready trip expense management system with real-time budget validation, automatic bill association, and streamlined approval workflows.