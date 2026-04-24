# Bill Processing Examples

## Sample JSON Responses

Here are examples of what the bill processing system returns for different types of expenses:

### 1. Restaurant Bill Example

**Input:** Restaurant receipt image
**Output:**
```json
{
  "success": true,
  "filename": "restaurant_receipt.jpg",
  "file_type": "jpg",
  "financial_data": {
    "date": "2025-01-15",
    "vendor": "Mario's Italian Restaurant",
    "category": "food",
    "amount": 45.75,
    "subtotal": 38.50,
    "tax": 7.25,
    "discount": null,
    "currency": "USD",
    "remarks": "Business dinner with client"
  },
  "confidence_score": 0.92,
  "processing_time": 2.34,
  "warnings": []
}
```

### 2. Hotel Bill Example

**Input:** Hotel invoice PDF
**Output:**
```json
{
  "success": true,
  "filename": "hotel_invoice.pdf",
  "file_type": "pdf",
  "financial_data": {
    "date": "2025-01-14",
    "vendor": "Grand Plaza Hotel",
    "category": "lodging",
    "amount": 450.75,
    "subtotal": 395.00,
    "tax": 55.75,
    "discount": null,
    "currency": "USD",
    "remarks": "Conference accommodation"
  },
  "confidence_score": 0.88,
  "processing_time": 3.12,
  "warnings": [
    "Tax amount seems unusually high"
  ]
}
```

### 3. Taxi Receipt Example

**Input:** Taxi receipt photo
**Output:**
```json
{
  "success": true,
  "filename": "taxi_receipt.png",
  "file_type": "png",
  "financial_data": {
    "date": "2025-01-15",
    "vendor": "Yellow Cab Company",
    "category": "transport",
    "amount": 28.50,
    "subtotal": 25.00,
    "tax": 3.50,
    "discount": null,
    "currency": "USD",
    "remarks": null
  },
  "confidence_score": 0.85,
  "processing_time": 1.89,
  "warnings": []
}
```

### 4. Gas Station Receipt Example

**Input:** Fuel receipt image
**Output:**
```json
{
  "success": true,
  "filename": "gas_receipt.jpg",
  "file_type": "jpg",
  "financial_data": {
    "date": "2025-01-13",
    "vendor": "Shell Gas Station",
    "category": "fuel",
    "amount": 65.40,
    "subtotal": 60.00,
    "tax": 5.40,
    "discount": null,
    "currency": "USD",
    "remarks": "Company vehicle refuel"
  },
  "confidence_score": 0.90,
  "processing_time": 2.01,
  "warnings": []
}
```

### 5. Office Supplies Receipt Example

**Input:** Office supply store receipt
**Output:**
```json
{
  "success": true,
  "filename": "office_supplies.jpg",
  "file_type": "jpg",
  "financial_data": {
    "date": "2025-01-12",
    "vendor": "Staples Office Supplies",
    "category": "office_supplies",
    "amount": 127.89,
    "subtotal": 115.35,
    "tax": 12.54,
    "discount": null,
    "currency": "USD",
    "remarks": "Printer paper and ink cartridges"
  },
  "confidence_score": 0.87,
  "processing_time": 2.67,
  "warnings": []
}
```

### 6. Failed Processing Example

**Input:** Blurry or unreadable image
**Output:**
```json
{
  "success": false,
  "filename": "blurry_receipt.jpg",
  "file_type": "jpg",
  "raw_text": "some partial text...",
  "financial_data": null,
  "confidence_score": null,
  "processing_time": 1.45,
  "error": "Insufficient text extracted from the image. Please ensure the image contains clear, readable text.",
  "warnings": []
}
```

## API Usage Examples

### Using cURL

```bash
# Process a bill
curl -X POST "http://localhost:8000/bills/process-bill" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@restaurant_receipt.jpg"

# Get supported categories
curl -X GET "http://localhost:8000/bills/categories" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Health check
curl -X GET "http://localhost:8000/bills/health" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Using JavaScript/Axios

```javascript
// Process a bill
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await axios.post('/bills/process-bill', formData, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  }
});

console.log(response.data);
```

### Using Python/Requests

```python
import requests

# Process a bill
url = "http://localhost:8000/bills/process-bill"
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("receipt.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()

print(f"Amount: ${result['financial_data']['amount']}")
print(f"Category: {result['financial_data']['category']}")
```

## Confidence Score Interpretation

- **0.8 - 1.0**: High confidence - All major fields extracted successfully
- **0.6 - 0.79**: Medium confidence - Most fields extracted, some may be missing
- **0.4 - 0.59**: Low confidence - Basic information extracted, manual review recommended
- **0.0 - 0.39**: Very low confidence - Extraction likely unreliable

## Category Classification

The system automatically classifies expenses into these categories:

1. **food** - Restaurants, cafes, meals, catering
2. **transport** - Taxis, buses, trains, flights, parking
3. **lodging** - Hotels, motels, accommodation
4. **fuel** - Gas stations, fuel purchases
5. **entertainment** - Movies, concerts, events
6. **office_supplies** - Stationery, equipment, software
7. **communication** - Phone, internet, data plans
8. **medical** - Healthcare, pharmacy, medical services
9. **miscellaneous** - Other expenses not fitting above categories

## Error Handling

Common error scenarios and responses:

### File Too Large
```json
{
  "detail": "File size too large. Maximum size allowed is 10MB."
}
```

### Unsupported File Type
```json
{
  "detail": "Unsupported file type. Allowed types: jpg, jpeg, png, bmp, tiff, gif, pdf"
}
```

### Authentication Error
```json
{
  "detail": "Could not validate credentials"
}
```

### OCR Processing Failed
```json
{
  "success": false,
  "error": "OCR extraction failed: No text could be extracted from the image"
}
```

## Integration Tips

1. **Always check the `success` field** before processing financial data
2. **Use confidence scores** to determine if manual review is needed
3. **Handle warnings** to improve data quality
4. **Implement retry logic** for network timeouts
5. **Validate extracted amounts** against business rules
6. **Store raw text** for audit trails and manual review