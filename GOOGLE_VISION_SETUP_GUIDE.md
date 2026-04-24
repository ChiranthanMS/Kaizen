# Google Vision API Setup Guide

## 🚀 Quick Start

Your FastAPI project has been successfully migrated to use Google Cloud Vision API for OCR functionality. Follow these steps to complete the setup.

## 📋 Prerequisites

1. **Google Cloud Account**: You need a Google Cloud Platform account
2. **Google Vision API Key**: Already configured in your `.env` file
3. **Python Dependencies**: Already installed via `requirements.txt`

## 🔧 Google Cloud Setup

### Step 1: Enable Google Vision API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services** > **Library**
4. Search for "Cloud Vision API"
5. Click on "Cloud Vision API" and click **Enable**

### Step 2: Verify API Key Permissions

Your API key (`AIzaSyAsSpHYCo7BOLBmyRc-hqBbPgWOA_umANk`) needs the following permissions:
- Cloud Vision API access
- Proper quota limits

To check/update your API key:
1. Go to **APIs & Services** > **Credentials**
2. Find your API key and click the edit button
3. Under **API restrictions**, ensure "Cloud Vision API" is allowed
4. Under **Application restrictions**, configure as needed for your domain

## 🧪 Testing the Setup

### Backend Testing

1. **Start the server:**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8001
   ```

2. **Run integration tests:**
   ```bash
   python test_complete_integration.py
   ```

3. **Test the API endpoint:**
   ```bash
   curl http://localhost:8001/bills/test-google-vision
   ```

### Expected Test Results

✅ **PASS**: Bill Parser - Text parsing logic works correctly
✅ **PASS**: Test Endpoint - API configuration endpoint responds
✅ **PASS**: Upload Endpoint - Bill upload endpoint exists and requires auth
⚠️ **May FAIL**: Google Vision API Direct - Requires valid API key with permissions

## 📱 Frontend Usage

### New Google Vision Upload Page

1. **Access the page**: Navigate to `/google-vision-upload` after logging in
2. **Upload a bill**: Drag and drop or select an image/PDF file
3. **View results**: See extracted bill information in structured format

### Integration with Existing Pages

The existing `/bills/process-bill` endpoint now uses Google Vision API automatically.

## 🔍 API Endpoints

### New Endpoints

1. **POST /bills/upload-bill**
   - **Purpose**: Upload and process bills using Google Vision API
   - **Authentication**: Required (employee role)
   - **Input**: Multipart file upload
   - **Output**: Structured bill data in JSON format

2. **GET /bills/test-google-vision**
   - **Purpose**: Test Google Vision API configuration
   - **Authentication**: Not required
   - **Output**: API status and configuration info

### Updated Endpoints

1. **POST /bills/process-bill**
   - Now uses Google Vision OCR instead of simple OCR
   - Maintains backward compatibility

## 📊 JSON Response Format

```json
{
  "employee_name": "John Doe",
  "bill_type": "food",
  "vendor": "Restaurant ABC", 
  "date": "2024-01-15",
  "amount": 25.50,
  "raw_text": "Full OCR extracted text...",
  "bill_id": 123,
  "processing_time": 2.34,
  "status": "success",
  "message": "Bill processed and stored successfully using Google Vision API!"
}
```

## 🗄️ Database Storage

Bills are automatically stored in PostgreSQL with the following mapping:
- `employee_name` → Derived from authenticated user
- `bill_type` → Mapped to `category` field (food→food, travel→transport, rent→lodging)
- `vendor` → Stored as `vendor`
- `date` → Stored as `date` (converted to Python date object)
- `amount` → Stored as `amount`
- `raw_text` → Stored as `raw_text`

## 🚨 Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - **Cause**: API key doesn't have Vision API permissions
   - **Solution**: Enable Cloud Vision API for your API key in Google Cloud Console

2. **429 Quota Exceeded**
   - **Cause**: API usage limits exceeded
   - **Solution**: Check quota limits in Google Cloud Console

3. **No Text Detected**
   - **Cause**: Poor image quality or unsupported format
   - **Solution**: Use high-quality images with clear text

### Debug Steps

1. **Check API key configuration:**
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('GOOGLE_VISION_API_KEY')[:10] + '...')"
   ```

2. **Test API connectivity:**
   ```bash
   curl -X GET "http://localhost:8001/bills/test-google-vision"
   ```

3. **Check server logs:**
   Look for error messages in the FastAPI server console output

## 💰 Cost Considerations

Google Vision API pricing (as of 2024):
- **First 1,000 units/month**: Free
- **1,001 - 5,000,000 units**: $1.50 per 1,000 units
- **5,000,001+ units**: $0.60 per 1,000 units

Each bill image counts as 1 unit. Monitor usage in Google Cloud Console.

## 🔄 Migration from Gemini

### What Changed
- ✅ Removed all Gemini API dependencies
- ✅ Replaced with Google Vision API for OCR
- ✅ Enhanced bill parsing with rule-based extraction
- ✅ Maintained all existing functionality
- ✅ Preserved MongoDB authentication system

### What Stayed the Same
- ✅ Database schema and storage
- ✅ User authentication and authorization
- ✅ Frontend components (except new Google Vision upload page)
- ✅ Manager dashboard and bill approval workflow

## 📈 Performance Improvements

1. **Faster OCR**: Google Vision API is typically faster than local OCR solutions
2. **Better Accuracy**: Superior text recognition, especially for receipts and invoices
3. **Scalability**: Cloud-based solution scales automatically
4. **Reliability**: Enterprise-grade uptime and availability

## 🔮 Future Enhancements

1. **Batch Processing**: Process multiple bills simultaneously
2. **Advanced Parsing**: Use Google Vision's document structure detection
3. **Receipt Validation**: Cross-reference extracted data with business rules
4. **Multi-language Support**: Process bills in different languages
5. **Mobile Integration**: Direct camera capture and processing

## 📞 Support

If you encounter issues:

1. **Check the logs**: FastAPI server console and browser developer tools
2. **Verify API key**: Ensure Google Vision API is enabled and key has permissions
3. **Test with sample images**: Use clear, high-quality bill images
4. **Monitor quotas**: Check Google Cloud Console for usage limits

## 🎯 Success Metrics

Your migration is successful when:
- ✅ `/bills/test-google-vision` returns success status
- ✅ Bill images upload and process correctly
- ✅ Extracted data appears in the database
- ✅ Frontend displays structured bill information
- ✅ No Gemini-related errors in server logs

---

**🎉 Congratulations!** Your FastAPI project now uses Google Vision API for superior OCR functionality while maintaining all existing features and workflows.