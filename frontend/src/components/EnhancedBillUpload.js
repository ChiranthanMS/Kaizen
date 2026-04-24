import React, { useState, useRef } from 'react';
import axios from 'axios';

const EnhancedBillUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [processingStatus, setProcessingStatus] = useState(null);
  const fileInputRef = useRef(null);

  // Check processing status on component mount
  React.useEffect(() => {
    checkProcessingStatus();
  }, []);

  const checkProcessingStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/bills/processing-status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProcessingStatus(response.data);
    } catch (error) {
      console.error('Error checking processing status:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setResult(response.data);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Call the success callback if provided
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError(
        error.response?.data?.detail || 
        'An error occurred while processing the bill'
      );
    } finally {
      setUploading(false);
    }
  };

  const formatCurrency = (amount, currency = 'INR') => {
    if (!amount) return 'N/A';
    const symbol = currency === 'INR' ? '₹' : currency === 'USD' ? '$' : currency;
    return `${symbol}${parseFloat(amount).toFixed(2)}`;
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return '#4CAF50'; // Green
    if (score >= 0.6) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };

  const getParsingMethodBadge = (method) => {
    const badges = {
      'gemini_2_flash': { color: '#4CAF50', text: 'Gemini 2.0 Flash' },
      'regex_fallback': { color: '#FF9800', text: 'Regex Parser' },
      'gemini_regex_hybrid': { color: '#2196F3', text: 'Hybrid (AI + Regex)' },
      'enhanced': { color: '#9C27B0', text: 'Enhanced Pipeline' }
    };
    
    const badge = badges[method] || { color: '#757575', text: method || 'Unknown' };
    
    return (
      <span 
        style={{
          backgroundColor: badge.color,
          color: 'white',
          padding: '4px 8px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 'bold'
        }}
      >
        {badge.text}
      </span>
    );
  };

  return (
    <>
      {/* CSS Animations */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
          }
          
          @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(56, 142, 60, 0.3); }
            70% { box-shadow: 0 0 0 10px rgba(56, 142, 60, 0); }
            100% { box-shadow: 0 0 0 0 rgba(56, 142, 60, 0); }
          }
          
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(30px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
          }
        `}
      </style>
      
      <div style={{ 
        maxWidth: '900px', 
        margin: '0 auto', 
        padding: '20px',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
      <div style={{
        textAlign: 'center',
        marginBottom: '40px',
        background: 'linear-gradient(135deg, #388e3c 0%, #2e7d32 100%)',
        padding: '30px',
        borderRadius: '20px',
        color: 'white',
        boxShadow: '0 8px 32px rgba(56, 142, 60, 0.2)'
      }}>
        <h1 style={{ 
          margin: '0 0 10px 0', 
          fontSize: '2.5rem',
          fontWeight: '700',
          textShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          🚀 AI-Powered Bill Processing
        </h1>
        <p style={{ 
          margin: '0', 
          fontSize: '1.1rem', 
          opacity: '0.9',
          fontWeight: '300'
        }}>
          Upload your bills and let our AI extract data with 90%+ accuracy
        </p>
      </div>
      
      {/* Processing Status */}
      {processingStatus && (
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e8f5e8 100%)',
          border: '2px solid #4CAF50',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '30px',
          boxShadow: '0 4px 20px rgba(76, 175, 80, 0.1)',
          transition: 'all 0.3s ease'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <div style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: processingStatus.overall_status === 'healthy' ? '#4CAF50' : '#ff9800',
              marginRight: '12px',
              boxShadow: processingStatus.overall_status === 'healthy' ? '0 0 0 4px rgba(76, 175, 80, 0.2)' : '0 0 0 4px rgba(255, 152, 0, 0.2)'
            }}></div>
            <h3 style={{ 
              margin: '0', 
              color: '#2e7d32',
              fontSize: '1.3rem',
              fontWeight: '600'
            }}>
              🤖 AI Processing Status: {processingStatus.overall_status.toUpperCase()}
            </h3>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '16px',
            marginBottom: '16px'
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600', color: '#333' }}>📸 OCR Extraction</span>
                <span style={{ 
                  color: processingStatus.services.ocr_space?.available ? '#4CAF50' : '#f44336',
                  fontWeight: 'bold'
                }}>
                  {processingStatus.services.ocr_space?.available ? '✅ Ready' : '❌ Offline'}
                </span>
              </div>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600', color: '#333' }}>🧠 Gemini AI</span>
                <span style={{ 
                  color: processingStatus.services.gemini?.available ? '#4CAF50' : '#f44336',
                  fontWeight: 'bold'
                }}>
                  {processingStatus.services.gemini?.available ? '✅ Ready' : '❌ Offline'}
                </span>
              </div>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: '600', color: '#333' }}>🔍 Pattern Fallback</span>
                <span style={{ 
                  color: processingStatus.services.regex_fallback?.available ? '#4CAF50' : '#f44336',
                  fontWeight: 'bold'
                }}>
                  {processingStatus.services.regex_fallback?.available ? '✅ Ready' : '❌ Offline'}
                </span>
              </div>
            </div>
          </div>
          
          <div style={{
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid rgba(76, 175, 80, 0.2)'
          }}>
            <div style={{ 
              fontSize: '14px', 
              color: '#2e7d32',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{ marginRight: '8px' }}>🔄</span>
              Pipeline: {processingStatus.services.processing_pipeline}
            </div>
          </div>
        </div>
      )}

      {/* File Upload Area */}
      <div
        style={{
          border: `3px dashed ${dragActive ? '#4CAF50' : '#c8e6c9'}`,
          borderRadius: '20px',
          padding: '50px 40px',
          textAlign: 'center',
          background: dragActive 
            ? 'linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)' 
            : 'linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%)',
          marginBottom: '30px',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          boxShadow: dragActive 
            ? '0 8px 32px rgba(76, 175, 80, 0.2)' 
            : '0 4px 20px rgba(0, 0, 0, 0.05)',
          transform: dragActive ? 'scale(1.02)' : 'scale(1)',
          position: 'relative',
          overflow: 'hidden'
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onMouseEnter={(e) => {
          if (!dragActive) {
            e.currentTarget.style.borderColor = '#4CAF50';
            e.currentTarget.style.transform = 'scale(1.01)';
            e.currentTarget.style.boxShadow = '0 6px 24px rgba(76, 175, 80, 0.15)';
          }
        }}
        onMouseLeave={(e) => {
          if (!dragActive) {
            e.currentTarget.style.borderColor = '#c8e6c9';
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.05)';
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {/* Background decoration */}
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          fontSize: '24px',
          opacity: '0.1',
          transform: 'rotate(15deg)'
        }}>🤖</div>
        
        {file ? (
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              fontSize: '64px', 
              marginBottom: '16px',
              filter: 'drop-shadow(0 4px 8px rgba(76, 175, 80, 0.3))'
            }}>📄</div>
            <div style={{
              backgroundColor: 'rgba(76, 175, 80, 0.1)',
              padding: '16px 24px',
              borderRadius: '12px',
              border: '1px solid rgba(76, 175, 80, 0.2)',
              display: 'inline-block'
            }}>
              <p style={{ 
                margin: '0 0 8px 0', 
                fontSize: '18px', 
                color: '#2e7d32',
                fontWeight: '600'
              }}>
                ✅ {file.name}
              </p>
              <p style={{ 
                margin: '0', 
                fontSize: '14px', 
                color: '#4CAF50',
                fontWeight: '500'
              }}>
                📊 Size: {(file.size / 1024 / 1024).toFixed(2)} MB • Ready for AI processing
              </p>
            </div>
          </div>
        ) : (
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              fontSize: '72px', 
              marginBottom: '20px',
              filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1))',
              animation: dragActive ? 'bounce 0.6s ease-in-out' : 'none'
            }}>
              {dragActive ? '📤' : '📁'}
            </div>
            <h3 style={{ 
              margin: '0 0 12px 0', 
              fontSize: '24px', 
              color: '#2e7d32',
              fontWeight: '600'
            }}>
              {dragActive ? '🎯 Drop your bill here!' : '📤 Upload Your Bill'}
            </h3>
            <p style={{ 
              margin: '0 0 8px 0', 
              fontSize: '16px', 
              color: '#666',
              fontWeight: '400'
            }}>
              {dragActive ? 'Release to upload' : 'Drag and drop your bill here, or click to browse'}
            </p>
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '16px',
              marginTop: '16px',
              flexWrap: 'wrap'
            }}>
              <span style={{
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                color: '#2e7d32',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                border: '1px solid rgba(76, 175, 80, 0.2)'
              }}>🤖 AI-Powered</span>
              <span style={{
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                color: '#2e7d32',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                border: '1px solid rgba(76, 175, 80, 0.2)'
              }}>📸 JPG, PNG, PDF</span>
              <span style={{
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                color: '#2e7d32',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                border: '1px solid rgba(76, 175, 80, 0.2)'
              }}>📏 Max 10MB</span>
            </div>
          </div>
        )}
      </div>

      {/* Upload Button */}
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{
            background: uploading 
              ? 'linear-gradient(135deg, #bdbdbd 0%, #9e9e9e 100%)' 
              : 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
            color: 'white',
            border: 'none',
            padding: '16px 48px',
            borderRadius: '50px',
            fontSize: '18px',
            fontWeight: '600',
            cursor: uploading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: uploading 
              ? '0 4px 12px rgba(0, 0, 0, 0.1)' 
              : '0 6px 20px rgba(76, 175, 80, 0.3)',
            transform: uploading ? 'scale(0.98)' : 'scale(1)',
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
            position: 'relative',
            overflow: 'hidden'
          }}
          onMouseEnter={(e) => {
            if (!uploading && !e.target.disabled) {
              e.target.style.transform = 'scale(1.05)';
              e.target.style.boxShadow = '0 8px 25px rgba(76, 175, 80, 0.4)';
            }
          }}
          onMouseLeave={(e) => {
            if (!uploading && !e.target.disabled) {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = '0 6px 20px rgba(76, 175, 80, 0.3)';
            }
          }}
        >
          {uploading && (
            <span style={{
              display: 'inline-block',
              width: '20px',
              height: '20px',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              borderTop: '2px solid white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginRight: '12px'
            }}></span>
          )}
          {uploading ? '🤖 AI Processing...' : '🚀 Process with AI'}
        </button>
        
        {file && !uploading && (
          <p style={{
            marginTop: '16px',
            fontSize: '14px',
            color: '#4CAF50',
            fontWeight: '500'
          }}>
            ✨ Ready to extract data with 90%+ accuracy
          </p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          background: 'linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)',
          border: '2px solid #f44336',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '30px',
          boxShadow: '0 4px 20px rgba(244, 67, 54, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              backgroundColor: '#f44336',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '12px',
              fontSize: '14px'
            }}>❌</div>
            <h3 style={{ margin: '0', color: '#d32f2f', fontSize: '18px', fontWeight: '600' }}>
              Processing Error
            </h3>
          </div>
          <p style={{ margin: '0', color: '#d32f2f', fontSize: '16px', lineHeight: '1.5' }}>
            {error}
          </p>
        </div>
      )}

      {/* Results Display */}
      {result && result.success && (
        <div style={{
          background: 'linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)',
          border: '2px solid #4CAF50',
          borderRadius: '20px',
          padding: '32px',
          marginBottom: '30px',
          boxShadow: '0 8px 32px rgba(76, 175, 80, 0.2)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Success decoration */}
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            fontSize: '32px',
            opacity: '0.1',
            transform: 'rotate(-15deg)'
          }}>🎉</div>
          
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#4CAF50',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '16px',
              fontSize: '18px',
              boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)'
            }}>✅</div>
            <h2 style={{ 
              margin: '0', 
              color: '#2e7d32', 
              fontSize: '24px', 
              fontWeight: '700'
            }}>
              {result.message}
            </h2>
          </div>
          
          {/* Processing Information */}
          <div style={{ 
            marginBottom: '24px', 
            background: 'rgba(255, 255, 255, 0.8)', 
            padding: '20px', 
            borderRadius: '16px',
            border: '1px solid rgba(76, 175, 80, 0.2)',
            backdropFilter: 'blur(10px)'
          }}>
            <h3 style={{ 
              margin: '0 0 16px 0', 
              color: '#2e7d32', 
              fontSize: '18px', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{ marginRight: '8px' }}>📊</span>
              Processing Information
            </h3>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: '16px',
              marginBottom: '16px'
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid #e0e0e0',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', fontWeight: '600' }}>
                  METHOD
                </div>
                <div style={{ fontSize: '16px', fontWeight: '600' }}>
                  {getParsingMethodBadge(result.processing_info?.parsing_method)}
                </div>
              </div>
              
              <div style={{
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid #e0e0e0',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', fontWeight: '600' }}>
                  CONFIDENCE
                </div>
                <div style={{ 
                  fontSize: '20px', 
                  fontWeight: '700',
                  color: getConfidenceColor(result.processing_info?.confidence_score)
                }}>
                  {(result.processing_info?.confidence_score * 100).toFixed(1)}%
                </div>
              </div>
              
              <div style={{
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid #e0e0e0',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', fontWeight: '600' }}>
                  PROCESSING TIME
                </div>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#4CAF50' }}>
                  ⚡ {result.processing_info?.processing_time?.toFixed(2)}s
                </div>
              </div>
            </div>
            
            {result.processing_info?.validation_warnings?.length > 0 && (
              <div style={{
                backgroundColor: 'rgba(255, 152, 0, 0.1)',
                border: '1px solid rgba(255, 152, 0, 0.3)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '16px'
              }}>
                <div style={{ 
                  color: '#f57c00', 
                  fontWeight: '600',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <span style={{ marginRight: '8px' }}>⚠️</span>
                  Validation Warnings
                </div>
                <div style={{ color: '#f57c00', fontSize: '14px', marginTop: '4px' }}>
                  {result.processing_info.validation_warnings.join(', ')}
                </div>
              </div>
            )}
          </div>

          {/* Bill Data */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
            <div>
              <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Basic Information</h4>
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div><strong>Bill ID:</strong> {result.bill_data.id}</div>
                <div><strong>Date:</strong> {result.bill_data.date || 'N/A'}</div>
                <div><strong>Vendor:</strong> {result.bill_data.vendor || 'N/A'}</div>
                <div><strong>Category:</strong> {result.bill_data.category || 'N/A'}</div>
                <div><strong>Status:</strong> {result.bill_data.status}</div>
              </div>
            </div>

            <div>
              <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Financial Details</h4>
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div><strong>Amount:</strong> {formatCurrency(result.bill_data.amount, result.bill_data.currency)}</div>
                <div><strong>Subtotal:</strong> {formatCurrency(result.bill_data.subtotal, result.bill_data.currency)}</div>
                <div><strong>Tax:</strong> {formatCurrency(result.bill_data.tax, result.bill_data.currency)}</div>
                <div><strong>Discount:</strong> {formatCurrency(result.bill_data.discount, result.bill_data.currency)}</div>
                <div><strong>Currency:</strong> {result.bill_data.currency}</div>
              </div>
            </div>

            <div>
              <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Additional Details</h4>
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div><strong>Payment Method:</strong> {result.bill_data.payment_method || 'N/A'}</div>
                <div><strong>Invoice Number:</strong> {result.bill_data.invoice_number || 'N/A'}</div>
                {result.bill_data.travel_from && (
                  <div><strong>From:</strong> {result.bill_data.travel_from}</div>
                )}
                {result.bill_data.travel_to && (
                  <div><strong>To:</strong> {result.bill_data.travel_to}</div>
                )}
              </div>
            </div>
          </div>

          {result.bill_data.description && (
            <div style={{ marginTop: '15px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Description</h4>
              <p style={{ margin: '0', fontSize: '14px', color: '#666', fontStyle: 'italic' }}>
                {result.bill_data.description}
              </p>
            </div>
          )}
        </div>
      )}
      </div>
    </>
  );
};

export default EnhancedBillUpload;