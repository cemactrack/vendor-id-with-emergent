import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
from typing import List, Dict, Optional, Tuple, Any
import logging
import tempfile
from pathlib import Path
import asyncio
import concurrent.futures
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class OCRProcessor:
    """Advanced OCR processor for document text extraction"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize OCR processor with optional Tesseract path"""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.logger = logger
        self.temp_dir = tempfile.gettempdir()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    
    def preprocess_image(self, image: np.ndarray, document_type: str = "default") -> np.ndarray:
        """Apply preprocessing to improve OCR accuracy based on document type"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Document type specific preprocessing
            if document_type == "business_registration":
                return self._preprocess_business_document(gray)
            elif document_type == "tax_document":
                return self._preprocess_tax_document(gray)
            else:
                return self._preprocess_generic_document(gray)
                
        except Exception as e:
            self.logger.error(f"Error in image preprocessing: {str(e)}")
            return image
    
    def _preprocess_business_document(self, gray: np.ndarray) -> np.ndarray:
        """Preprocessing optimized for business registration documents"""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Deskew the image
        return self._deskew_image(cleaned)
    
    def _preprocess_tax_document(self, gray: np.ndarray) -> np.ndarray:
        """Preprocessing optimized for tax documents"""
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 15, 10
        )
        
        return self._deskew_image(thresh)
    
    def _preprocess_generic_document(self, gray: np.ndarray) -> np.ndarray:
        """Generic preprocessing for all document types"""
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return self._deskew_image(thresh)
    
    def _deskew_image(self, image: np.ndarray, angle_tolerance: float = 0.5) -> np.ndarray:
        """Correct image skew using contour analysis"""
        try:
            coords = np.column_stack(np.where(image > 0))
            if len(coords) == 0:
                return image
                
            angle = cv2.minAreaRect(coords)[-1]
            
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Only correct if angle is significant
            if abs(angle) > angle_tolerance:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Deskewing failed: {str(e)}")
            return image
    
    def extract_text_with_confidence(self, image: np.ndarray, document_type: str = "default") -> Dict[str, Any]:
        """Extract text with confidence scores and metadata"""
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image, document_type)
            
            # Configure Tesseract based on document type
            config = self._get_tesseract_config(document_type)
            
            # Extract text with detailed data
            data = pytesseract.image_to_data(
                processed_image, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            # Process the extracted data
            return self._process_tesseract_output(data, processed_image, config)
            
        except Exception as e:
            self.logger.error(f"Error in text extraction: {str(e)}")
            return {
                'text': '',
                'words': [],
                'word_confidences': [],
                'overall_confidence': 0,
                'word_count': 0,
                'error': str(e)
            }
    
    def _get_tesseract_config(self, document_type: str) -> str:
        """Get Tesseract configuration based on document type"""
        base_config = "--oem 3 --psm 6"
        
        if document_type == "business_registration":
            return f"{base_config} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()- /"
        elif document_type == "tax_document":
            return f"{base_config} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()- /$"
        else:
            return base_config
    
    def _process_tesseract_output(self, data: Dict, processed_image: np.ndarray, config: str) -> Dict[str, Any]:
        """Process Tesseract output data into structured format"""
        # Filter out low-confidence results
        min_confidence = 30
        words = []
        confidences = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > min_confidence:
                text = data['text'][i].strip()
                if text:
                    words.append(text)
                    confidences.append(int(data['conf'][i]))
        
        # Calculate overall confidence
        overall_confidence = np.mean(confidences) if confidences else 0
        
        # Extract full text
        full_text = pytesseract.image_to_string(processed_image, config=config).strip()
        
        return {
            'text': full_text,
            'words': words,
            'word_confidences': confidences,
            'overall_confidence': float(overall_confidence),
            'word_count': len(words),
            'high_confidence_words': [w for i, w in enumerate(words) if confidences[i] > 80],
            'processing_metadata': {
                'tesseract_config': config,
                'image_dimensions': processed_image.shape,
                'total_detected_elements': len(data['text'])
            }
        }
    
    async def process_pdf(self, pdf_bytes: bytes, document_type: str = "default") -> List[Dict[str, Any]]:
        """Process PDF document and extract text from all pages asynchronously"""
        try:
            # Convert PDF pages to images in thread pool
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                self._executor, 
                convert_from_bytes, 
                pdf_bytes, 
                300  # DPI
            )
            
            results = []
            for page_num, pil_image in enumerate(images, 1):
                # Convert PIL image to OpenCV format
                opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                # Extract text with confidence
                result = await loop.run_in_executor(
                    self._executor,
                    self.extract_text_with_confidence,
                    opencv_image,
                    document_type
                )
                result['page_number'] = page_num
                
                self.logger.info(f"Processed PDF page {page_num} with confidence {result['overall_confidence']:.2f}")
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise ValueError(f"PDF processing failed: {str(e)}")
    
    async def process_image(self, image_bytes: bytes, document_type: str = "default") -> Dict[str, Any]:
        """Process single image file asynchronously"""
        try:
            # Load image from bytes in thread pool
            loop = asyncio.get_event_loop()
            
            def load_and_convert_image():
                image = Image.open(io.BytesIO(image_bytes))
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            opencv_image = await loop.run_in_executor(self._executor, load_and_convert_image)
            
            # Extract text with confidence
            result = await loop.run_in_executor(
                self._executor,
                self.extract_text_with_confidence,
                opencv_image,
                document_type
            )
            result['page_number'] = 1
            
            self.logger.info(f"Processed image with confidence {result['overall_confidence']:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            raise ValueError(f"Image processing failed: {str(e)}")

class DocumentOCRService:
    """Service for OCR document processing with database integration"""
    
    def __init__(self, mongo_url: str):
        """Initialize the OCR service with database connection"""
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client.vendor_ecosystem
        self.ocr_processor = OCRProcessor()
        self.logger = logger
    
    async def process_document_for_vendor(
        self, 
        vendor_id: str, 
        document_id: str, 
        file_content: bytes, 
        file_type: str, 
        document_type: str
    ) -> Dict[str, Any]:
        """Process document and store OCR results"""
        try:
            processing_id = str(uuid.uuid4())
            
            # Start processing
            start_time = datetime.now(timezone.utc)
            
            # Process based on file type
            if file_type.lower() == 'pdf':
                ocr_results = await self.ocr_processor.process_pdf(file_content, document_type)
            else:
                ocr_result = await self.ocr_processor.process_image(file_content, document_type)
                ocr_results = [ocr_result]
            
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - start_time).total_seconds()
            
            # Calculate overall metrics
            overall_confidence = float(np.mean([page['overall_confidence'] for page in ocr_results]))
            total_words = sum([page['word_count'] for page in ocr_results])
            combined_text = '\n\n'.join([page['text'] for page in ocr_results])
            
            # Create processing record
            processing_record = {
                'processing_id': processing_id,
                'vendor_id': vendor_id,
                'document_id': document_id,
                'document_type': document_type,
                'file_type': file_type,
                'processing_timestamp': start_time,
                'processing_time_seconds': processing_time,
                'overall_confidence': overall_confidence,
                'total_words_extracted': total_words,
                'page_count': len(ocr_results),
                'combined_text': combined_text,
                'page_results': ocr_results,
                'status': 'completed'
            }
            
            # Store in database
            await self.db.ocr_processing_results.insert_one(processing_record)
            
            # Update document record with OCR results
            await self.db.vendor_documents.update_one(
                {'document_id': document_id, 'vendor_id': vendor_id},
                {
                    '$set': {
                        'ocr_processed': True,
                        'ocr_processing_id': processing_id,
                        'ocr_confidence': float(overall_confidence),
                        'ocr_text_preview': combined_text[:500],  # First 500 chars
                        'ocr_processed_at': start_time
                    }
                }
            )
            
            self.logger.info(f"OCR processing completed for document {document_id}")
            
            return {
                'processing_id': processing_id,
                'status': 'success',
                'overall_confidence': float(overall_confidence),
                'total_words': total_words,
                'page_count': len(ocr_results),
                'processing_time': processing_time,
                'text_preview': combined_text[:200]
            }
            
        except Exception as e:
            self.logger.error(f"OCR processing failed for document {document_id}: {str(e)}")
            
            # Store error record
            error_record = {
                'processing_id': str(uuid.uuid4()),
                'vendor_id': vendor_id,
                'document_id': document_id,
                'document_type': document_type,
                'file_type': file_type,
                'processing_timestamp': datetime.now(timezone.utc),
                'status': 'failed',
                'error_message': str(e)
            }
            
            await self.db.ocr_processing_results.insert_one(error_record)
            
            raise ValueError(f"OCR processing failed: {str(e)}")
    
    async def get_ocr_results(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR processing results by processing ID"""
        try:
            result = await self.db.ocr_processing_results.find_one(
                {'processing_id': processing_id}
            )
            if result:
                # Remove MongoDB ObjectId to avoid serialization issues
                result.pop('_id', None)
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving OCR results: {str(e)}")
            return None
    
    async def get_document_ocr_results(self, vendor_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR results for a specific document"""
        try:
            result = await self.db.ocr_processing_results.find_one(
                {
                    'vendor_id': vendor_id,
                    'document_id': document_id,
                    'status': 'completed'
                }
            )
            if result:
                # Remove MongoDB ObjectId to avoid serialization issues
                result.pop('_id', None)
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving document OCR results: {str(e)}")
            return None
    
    async def validate_extracted_data(
        self, 
        vendor_id: str, 
        document_id: str, 
        expected_fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate extracted OCR data against expected vendor information"""
        try:
            # Get OCR results
            ocr_results = await self.get_document_ocr_results(vendor_id, document_id)
            
            if not ocr_results:
                return {
                    'validation_status': 'failed',
                    'error': 'No OCR results found for document'
                }
            
            combined_text = ocr_results['combined_text']
            validation_results = {}
            
            # Validate each expected field
            for field_name, expected_value in expected_fields.items():
                validation_results[field_name] = self._validate_field(
                    combined_text, field_name, expected_value
                )
            
            # Calculate overall validation score
            field_scores = [
                result['match_score'] 
                for result in validation_results.values() 
                if 'match_score' in result
            ]
            
            overall_validation_score = np.mean(field_scores) if field_scores else 0
            
            validation_record = {
                'validation_id': str(uuid.uuid4()),
                'vendor_id': vendor_id,
                'document_id': document_id,
                'ocr_processing_id': ocr_results['processing_id'],
                'validation_timestamp': datetime.now(timezone.utc),
                'expected_fields': expected_fields,
                'field_validations': validation_results,
                'overall_validation_score': float(overall_validation_score),
                'validation_passed': bool(overall_validation_score > 0.7)  # Convert numpy bool to Python bool
            }
            
            # Store validation results
            await self.db.ocr_validation_results.insert_one(validation_record)
            
            return validation_record
            
        except Exception as e:
            self.logger.error(f"Error validating extracted data: {str(e)}")
            raise ValueError(f"Validation failed: {str(e)}")
    
    def _validate_field(self, text: str, field_name: str, expected_value: str) -> Dict[str, Any]:
        """Validate a specific field against expected value"""
        from difflib import SequenceMatcher
        
        # Basic fuzzy matching
        similarity = SequenceMatcher(None, text.lower(), expected_value.lower()).ratio()
        
        # Check if expected value appears in text (case insensitive)
        contains_value = expected_value.lower() in text.lower()
        
        return {
            'field_name': field_name,
            'expected_value': expected_value,
            'found_in_text': bool(contains_value),  # Convert numpy bool to Python bool
            'match_score': float(similarity),
            'validation_passed': bool(similarity > 0.7 or contains_value)  # Convert numpy bool to Python bool
        }
    
    async def get_vendor_ocr_summary(self, vendor_id: str) -> Dict[str, Any]:
        """Get OCR processing summary for a vendor"""
        try:
            # Get all OCR results for vendor
            cursor = self.db.ocr_processing_results.find({'vendor_id': vendor_id})
            results = await cursor.to_list(length=None)
            
            if not results:
                return {
                    'vendor_id': vendor_id,
                    'total_documents': 0,
                    'processed_documents': 0,
                    'average_confidence': 0
                }
            
            completed_results = [r for r in results if r['status'] == 'completed']
            
            summary = {
                'vendor_id': vendor_id,
                'total_documents': len(results),
                'processed_documents': len(completed_results),
                'failed_documents': len(results) - len(completed_results),
                'average_confidence': float(np.mean([r['overall_confidence'] for r in completed_results])) if completed_results else 0,
                'total_words_extracted': sum([r['total_words_extracted'] for r in completed_results]),
                'average_processing_time': float(np.mean([r['processing_time_seconds'] for r in completed_results])) if completed_results else 0,
                'document_types_processed': list(set([r['document_type'] for r in completed_results]))
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating OCR summary: {str(e)}")
            raise ValueError(f"Summary generation failed: {str(e)}")