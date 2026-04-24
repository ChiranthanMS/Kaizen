-- Database Migration Script for Trip Submission Flow
-- Run this script to add the required columns and tables

-- 1. Add trip-related columns to existing app_bills table
ALTER TABLE app_bills ADD COLUMN IF NOT EXISTS trip_id VARCHAR(100);
ALTER TABLE app_bills ADD COLUMN IF NOT EXISTS trip_status VARCHAR(20) DEFAULT 'individual';

-- 2. Create trip submissions table
CREATE TABLE IF NOT EXISTS app_trip_submissions (
    id SERIAL PRIMARY KEY,
    trip_id VARCHAR(100) NOT NULL,
    employee_id INTEGER NOT NULL,
    employee_name VARCHAR(255),
    trip_purpose TEXT,
    destination_city VARCHAR(100),
    start_date DATE,
    end_date DATE,
    duration_days INTEGER,
    actual_bills_count INTEGER DEFAULT 0,
    actual_total_amount DECIMAL(10,2) DEFAULT 0.00,
    allocated_budget DECIMAL(10,2) DEFAULT 0.00,
    budget_utilization DECIMAL(5,2) DEFAULT 0.00,
    manager_id INTEGER,
    submission_status VARCHAR(20) DEFAULT 'pending',
    submission_notes TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER,
    review_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bills_trip_id ON app_bills(trip_id);
CREATE INDEX IF NOT EXISTS idx_bills_trip_status ON app_bills(trip_status);
CREATE INDEX IF NOT EXISTS idx_trip_submissions_employee ON app_trip_submissions(employee_id);
CREATE INDEX IF NOT EXISTS idx_trip_submissions_manager ON app_trip_submissions(manager_id);
CREATE INDEX IF NOT EXISTS idx_trip_submissions_status ON app_trip_submissions(submission_status);
CREATE INDEX IF NOT EXISTS idx_trip_submissions_trip_id ON app_trip_submissions(trip_id);

-- 4. Add foreign key constraints (optional, but recommended)
-- Note: Uncomment these if you want to enforce referential integrity
-- ALTER TABLE app_trip_submissions ADD CONSTRAINT fk_trip_submissions_employee 
--     FOREIGN KEY (employee_id) REFERENCES app_users(id) ON DELETE CASCADE;
-- ALTER TABLE app_trip_submissions ADD CONSTRAINT fk_trip_submissions_manager 
--     FOREIGN KEY (manager_id) REFERENCES app_users(id) ON DELETE SET NULL;

-- 5. Update existing bills to have proper trip_status
UPDATE app_bills SET trip_status = 'individual' WHERE trip_status IS NULL;

-- 6. Create a view for easy trip submission queries
CREATE OR replace VIEW trip_submission_summary AS
SELECT 
    ts.*,
    COUNT(b.id) as bill_count,
    COALESCE(SUM(b.amount), 0) as calculated_total_amount
FROM app_trip_submissions ts
LEFT JOIN app_bills b ON b.trip_id = ts.trip_id
GROUP BY ts.id;

-- 7. Verify the changes
SELECT 'Migration completed successfully!' as status;

-- Check if columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'app_bills' 
AND column_name IN ('trip_id', 'trip_status');

-- Check if trip_submissions table was created
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'app_trip_submissions';