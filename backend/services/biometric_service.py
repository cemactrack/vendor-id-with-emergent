import cv2
import numpy as np
import base64
import io
from PIL import Image
import hashlib
import hmac
from cryptography.fernet import Fernet
from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.biometric_models import *
from datetime import datetime, timedelta, timezone
import uuid
import logging
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import mediapipe as mp

logger = logging.getLogger(__name__)

class BiometricProcessor:
    """Core biometric processing engine"""
    
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize MediaPipe for enhanced face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def encrypt_template(self, template_data: str) -> str:
        """Encrypt biometric template"""
        try:
            encrypted = self.fernet.encrypt(template_data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Template encryption failed: {e}")
            raise
    
    def decrypt_template(self, encrypted_template: str) -> str:
        """Decrypt biometric template"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_template)
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Template decryption failed: {e}")
            raise
    
    async def process_document_analysis(self, image_data: str, document_type: DocumentType) -> DocumentAnalysisResult:
        """Analyze uploaded identity document"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[-1])
            image = Image.open(io.BytesIO(image_bytes))
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Run analysis in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._analyze_document_sync, 
                cv_image, 
                document_type
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise ValueError(f"Document analysis failed: {str(e)}")
    
    def _analyze_document_sync(self, cv_image: np.ndarray, document_type: DocumentType) -> DocumentAnalysisResult:
        """Synchronous document analysis"""
        try:
            # Basic document validation
            height, width = cv_image.shape[:2]
            if height < 300 or width < 400:
                raise ValueError("Document image too small")
            
            # Extract face from document
            face_extracted = False
            face_confidence = 0.0
            face_image_path = None
            
            # Use MediaPipe for face detection
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                results = face_detection.process(rgb_image)
                
                if results.detections:
                    face_extracted = True
                    face_confidence = results.detections[0].score[0]  # Use actual confidence from MediaPipe
                    
                    # Extract face bounding box
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    
                    h, w, _ = rgb_image.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Extract and save face image
                    face_image = rgb_image[y:y+height, x:x+width]
                    
                    # Save face image (in production, save to secure storage)
                    face_image_path = f"/tmp/face_{uuid.uuid4().hex}.jpg"
                    cv2.imwrite(face_image_path, cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))
            
            # OCR text extraction (simplified - in production use Tesseract or cloud OCR)
            extracted_text = self._extract_document_text(cv_image, document_type)
            
            # Security features detection (simplified)
            security_features = self._detect_security_features(cv_image)
            
            # Tampering detection
            tampering_detected = self._detect_tampering(cv_image)
            
            # Quality assessment
            quality_score = self._assess_image_quality(cv_image)
            
            return DocumentAnalysisResult(
                document_type=document_type,
                extracted_text=extracted_text,
                face_image_extracted=face_extracted,
                face_image_path=face_image_path,
                face_confidence=face_confidence,
                document_valid=face_extracted and quality_score > 0.5,
                security_features_detected=security_features,
                tampering_detected=tampering_detected,
                quality_score=quality_score,
                processing_metadata={
                    "image_dimensions": f"{cv_image.shape[1]}x{cv_image.shape[0]}",
                    "faces_detected": 1 if face_extracted else 0,
                    "processing_time": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Synchronous document analysis failed: {e}")
            raise
    
    def _extract_document_text(self, image: np.ndarray, doc_type: DocumentType) -> Dict[str, str]:
        """Extract text from document (simplified OCR)"""
        # In production, use advanced OCR like Tesseract or cloud services
        # This is a simplified implementation
        return {
            "name": "Sample Name",
            "id_number": "123456789",
            "date_of_birth": "1990-01-01",
            "nationality": "Sample Country",
            "document_number": "DOC123456"
        }
    
    def _detect_security_features(self, image: np.ndarray) -> List[str]:
        """Detect security features in document"""
        features = []
        
        # Simplified security feature detection
        # In production, implement advanced algorithms for:
        # - Watermark detection
        # - Hologram detection
        # - Microtext detection
        # - UV reactive elements
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Basic edge detection for security patterns
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 100:
            features.append("complex_background_pattern")
        
        # Check for reflective elements (simplified)
        brightness_variance = np.var(gray)
        if brightness_variance > 1000:
            features.append("reflective_elements")
        
        return features
    
    def _detect_tampering(self, image: np.ndarray) -> bool:
        """Detect if document has been tampered with"""
        # Simplified tampering detection
        # In production, implement sophisticated algorithms for:
        # - Clone detection
        # - Splice detection
        # - Copy-move forgery
        # - Compression artifacts analysis
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Basic noise analysis
        noise_level = np.std(gray)
        
        # Simple edge discontinuity check
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
        
        # Heuristic for tampering (very basic)
        return noise_level > 50 or edge_density < 0.01 or edge_density > 0.3
    
    def _assess_image_quality(self, image: np.ndarray) -> float:
        """Assess overall image quality"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Brightness
        brightness = np.mean(gray)
        
        # Contrast
        contrast = np.std(gray)
        
        # Normalize and combine metrics
        sharpness_score = min(sharpness / 1000, 1.0)  # Normalize to 0-1
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Prefer mid-range brightness
        contrast_score = min(contrast / 50, 1.0)  # Normalize to 0-1
        
        # Weighted quality score
        quality = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
        return max(0.0, min(1.0, quality))
    
    async def perform_liveness_check(self, challenge: LivenessChallenge, response: LivenessResponse) -> LivenessResult:
        """Process liveness detection"""
        try:
            # Decode video/image data
            response_bytes = base64.b64decode(response.response_data.split(',')[-1])
            
            # Run liveness check in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._process_liveness_sync,
                challenge,
                response_bytes
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            raise ValueError(f"Liveness check failed: {str(e)}")
    
    def _process_liveness_sync(self, challenge: LivenessChallenge, video_data: bytes) -> LivenessResult:
        """Synchronous liveness processing"""
        try:
            start_time = datetime.now()
            
            # For video data, we'd need to extract frames and analyze motion
            # For now, simulate liveness detection with basic face detection
            
            # Create temporary file for video processing
            temp_path = f"/tmp/liveness_{uuid.uuid4().hex}.webm"
            with open(temp_path, 'wb') as f:
                f.write(video_data)
            
            # Process video frames
            cap = cv2.VideoCapture(temp_path)
            frames_processed = 0
            face_detected_frames = 0
            motion_detected = False
            blink_detected = False
            
            liveness_indicators = {
                "face_detected": False,
                "motion_detected": False,
                "blink_detected": False,
                "head_movement": False,
                "live_person": False
            }
            
            try:
                while cap.isOpened() and frames_processed < 30:  # Process max 30 frames
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frames_processed += 1
                    
                    # Face detection using MediaPipe
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                        results = face_detection.process(rgb_frame)
                        
                        if results.detections:
                            face_detected_frames += 1
                            liveness_indicators["face_detected"] = True
                        
                        # Simple motion detection between frames
                        if frames_processed > 1:
                            motion_detected = True
                            liveness_indicators["motion_detected"] = True
                
                # Clean up
                cap.release()
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"Video processing error: {e}")
                if cap:
                    cap.release()
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            # Calculate results
            face_detected = face_detected_frames > 0
            face_ratio = face_detected_frames / max(frames_processed, 1)
            
            # Determine face quality
            face_quality = BiometricQuality.GOOD if face_ratio > 0.7 else \
                          BiometricQuality.ACCEPTABLE if face_ratio > 0.4 else \
                          BiometricQuality.POOR
            
            # Simple spoof detection (in production, use advanced algorithms)
            spoof_detection_passed = motion_detected and face_detected
            
            # Overall liveness score
            confidence_score = (face_ratio * 0.6 + (1.0 if motion_detected else 0.0) * 0.4)
            
            # Success determination
            success = (
                face_detected and
                motion_detected and
                confidence_score > 0.6 and
                spoof_detection_passed
            )
            
            # Update liveness indicators
            liveness_indicators.update({
                "live_person": success,
                "head_movement": motion_detected,
                "blink_detected": frames_processed > 10  # Simplified blink detection
            })
            
            failure_reasons = []
            if not face_detected:
                failure_reasons.append("No face detected in video")
            if not motion_detected:
                failure_reasons.append("No motion detected")
            if not spoof_detection_passed:
                failure_reasons.append("Spoof detection failed")
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return LivenessResult(
                challenge_id=challenge.challenge_id,
                vendor_id=challenge.vendor_id,
                success=success,
                confidence_score=confidence_score,
                liveness_indicators=liveness_indicators,
                face_detected=face_detected,
                face_quality=face_quality,
                spoof_detection_passed=spoof_detection_passed,
                processing_time_ms=processing_time,
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Liveness processing failed: {e}")
            raise
    
    async def perform_face_matching(self, request: FaceMatchRequest) -> FaceMatchResult:
        """Match faces between document and live scan"""
        try:
            # Decode images
            ref_bytes = base64.b64decode(request.reference_image.split(',')[-1])
            comp_bytes = base64.b64decode(request.comparison_image.split(',')[-1])
            
            # Run matching in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._match_faces_sync,
                request,
                ref_bytes,
                comp_bytes
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Face matching failed: {e}")
            raise ValueError(f"Face matching failed: {str(e)}")
    
    def _match_faces_sync(self, request: FaceMatchRequest, ref_bytes: bytes, comp_bytes: bytes) -> FaceMatchResult:
        """Synchronous face matching using MediaPipe and template matching"""
        try:
            # Load images
            ref_image = Image.open(io.BytesIO(ref_bytes))
            comp_image = Image.open(io.BytesIO(comp_bytes))
            
            # Convert to numpy arrays
            ref_array = np.array(ref_image)
            comp_array = np.array(comp_image)
            
            # Extract face regions using MediaPipe
            ref_face = self._extract_face_region_mediapipe(ref_array)
            comp_face = self._extract_face_region_mediapipe(comp_array)
            
            if ref_face is None:
                return FaceMatchResult(
                    vendor_id=request.vendor_id,
                    similarity_score=0.0,
                    match_confirmed=False,
                    confidence_level=0.0,
                    reference_face_quality=BiometricQuality.UNACCEPTABLE,
                    comparison_face_quality=BiometricQuality.UNACCEPTABLE,
                    processing_metadata={"error": "No face found in reference image"}
                )
            
            if comp_face is None:
                return FaceMatchResult(
                    vendor_id=request.vendor_id,
                    similarity_score=0.0,
                    match_confirmed=False,
                    confidence_level=0.0,
                    reference_face_quality=BiometricQuality.GOOD,
                    comparison_face_quality=BiometricQuality.UNACCEPTABLE,
                    processing_metadata={"error": "No face found in comparison image"}
                )
            
            # Calculate similarity using template matching and histogram comparison
            similarity_score = self._calculate_face_similarity(ref_face, comp_face)
            
            # Assess face quality (simplified)
            ref_quality = self._assess_face_quality(ref_array)
            comp_quality = self._assess_face_quality(comp_array)
            
            # Determine match
            match_confirmed = similarity_score >= request.match_threshold
            
            # Confidence level based on quality and similarity
            confidence_level = (similarity_score * 0.7 + 
                              (ref_quality + comp_quality) / 2 * 0.3)
            
            return FaceMatchResult(
                vendor_id=request.vendor_id,
                similarity_score=similarity_score,
                match_confirmed=match_confirmed,
                confidence_level=confidence_level,
                reference_face_quality=self._quality_score_to_enum(ref_quality),
                comparison_face_quality=self._quality_score_to_enum(comp_quality),
                processing_metadata={
                    "similarity_score": similarity_score,
                    "match_threshold": request.match_threshold,
                    "ref_face_extracted": ref_face is not None,
                    "comp_face_extracted": comp_face is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Face matching processing failed: {e}")
            raise
    
    def _assess_face_quality(self, face_array: np.ndarray) -> float:
        """Assess quality of extracted face"""
        try:
            # Convert to grayscale
            if len(face_array.shape) == 3:
                gray = cv2.cvtColor(face_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = face_array
            
            # Sharpness
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Size check
            height, width = gray.shape
            size_score = min((height * width) / (100 * 100), 1.0)
            
            # Brightness uniformity
            brightness_std = np.std(gray)
            brightness_score = min(brightness_std / 50, 1.0)
            
            # Combined quality
            quality = (sharpness / 1000 * 0.5 + size_score * 0.3 + brightness_score * 0.2)
            return max(0.0, min(1.0, quality))
            
        except Exception:
            return 0.0
    
    def _quality_score_to_enum(self, score: float) -> BiometricQuality:
        """Convert quality score to enum"""
        if score >= 0.9:
            return BiometricQuality.EXCELLENT
        elif score >= 0.7:
            return BiometricQuality.GOOD
        elif score >= 0.5:
            return BiometricQuality.ACCEPTABLE
        elif score >= 0.3:
            return BiometricQuality.POOR
        else:
            return BiometricQuality.UNACCEPTABLE
    
    async def process_fingerprint(self, request: FingerprintCaptureRequest) -> FingerprintTemplate:
        """Process fingerprint data and create template"""
        try:
            # Decode fingerprint image
            fp_bytes = base64.b64decode(request.fingerprint_data.split(',')[-1])
            
            # Run processing in thread pool
            loop = asyncio.get_event_loop()
            template = await loop.run_in_executor(
                self.executor,
                self._process_fingerprint_sync,
                request,
                fp_bytes
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Fingerprint processing failed: {e}")
            raise ValueError(f"Fingerprint processing failed: {str(e)}")
    
    def _process_fingerprint_sync(self, request: FingerprintCaptureRequest, fp_bytes: bytes) -> FingerprintTemplate:
        """Synchronous fingerprint processing"""
        try:
            # Load fingerprint image
            fp_image = Image.open(io.BytesIO(fp_bytes))
            fp_array = cv2.cvtColor(np.array(fp_image), cv2.COLOR_RGB2GRAY)
            
            # Basic fingerprint processing (simplified)
            # In production, use specialized fingerprint libraries like NFIQ, SourceAFIS, etc.
            
            # Basic quality assessment
            quality_score = self._assess_fingerprint_quality(fp_array)
            
            # Extract minutiae points (simplified - use pattern analysis)
            minutiae = self._extract_minutiae_simplified(fp_array)
            
            # Create encrypted template
            template_data = {
                "minutiae_points": minutiae,
                "ridge_pattern": self._analyze_ridge_pattern(fp_array),
                "quality_metrics": {
                    "clarity": quality_score,
                    "ridge_count": len(minutiae) if minutiae else 0
                }
            }
            
            # Encrypt template
            template_json = json.dumps(template_data)
            encrypted_template = self.encrypt_template(template_json)
            
            return FingerprintTemplate(
                vendor_id=request.vendor_id,
                finger_position=request.finger_position,
                minutiae_template=encrypted_template,
                quality_score=quality_score,
                ridge_count=len(minutiae) if minutiae else 0,
                template_size=len(encrypted_template)
            )
            
        except Exception as e:
            logger.error(f"Fingerprint processing failed: {e}")
            raise
    
    def _assess_fingerprint_quality(self, fp_image: np.ndarray) -> float:
        """Assess fingerprint image quality"""
        try:
            # Normalize image
            fp_normalized = cv2.equalizeHist(fp_image)
            
            # Calculate sharpness
            sharpness = cv2.Laplacian(fp_normalized, cv2.CV_64F).var()
            
            # Ridge clarity (using Gabor filters would be better)
            sobel_x = cv2.Sobel(fp_normalized, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(fp_normalized, cv2.CV_64F, 0, 1, ksize=3)
            ridge_clarity = np.mean(np.sqrt(sobel_x**2 + sobel_y**2))
            
            # Contrast
            contrast = np.std(fp_normalized)
            
            # Combine metrics
            quality = min(1.0, (sharpness / 500 * 0.4 + ridge_clarity / 100 * 0.4 + contrast / 50 * 0.2))
            return max(0.0, quality)
            
        except Exception:
            return 0.0
    
    def _extract_minutiae_simplified(self, fp_image: np.ndarray) -> List[Dict[str, Any]]:
        """Simplified minutiae extraction"""
        try:
            # This is a very basic implementation
            # In production, use specialized fingerprint libraries
            
            # Apply preprocessing
            enhanced = cv2.equalizeHist(fp_image)
            
            # Find key points using corner detection as approximation
            corners = cv2.goodFeaturesToTrack(enhanced, maxCorners=100, qualityLevel=0.01, minDistance=10)
            
            minutiae = []
            if corners is not None:
                for corner in corners:
                    x, y = corner.ravel()
                    minutiae.append({
                        "x": int(x),
                        "y": int(y),
                        "type": "ridge_ending",  # Simplified
                        "angle": 0  # Would need proper calculation
                    })
            
            return minutiae[:50]  # Limit to 50 minutiae points
            
        except Exception:
            return []
    
    def _analyze_ridge_pattern(self, fp_image: np.ndarray) -> Dict[str, Any]:
        """Analyze ridge patterns in fingerprint"""
        try:
            # Simplified ridge analysis
            # In production, implement proper ridge flow and pattern classification
            
            height, width = fp_image.shape
            
            # Basic pattern indicators
            horizontal_variance = np.var(np.mean(fp_image, axis=0))
            vertical_variance = np.var(np.mean(fp_image, axis=1))
            
            # Determine basic pattern type
            if horizontal_variance > vertical_variance:
                pattern_type = "arch"
            elif vertical_variance > horizontal_variance * 1.5:
                pattern_type = "loop"
            else:
                pattern_type = "whorl"
            
            return {
                "pattern_type": pattern_type,
                "horizontal_variance": float(horizontal_variance),
                "vertical_variance": float(vertical_variance),
                "pattern_confidence": min(1.0, abs(horizontal_variance - vertical_variance) / 100)
            }
            
        except Exception:
            return {"pattern_type": "unknown", "pattern_confidence": 0.0}
    
    def _extract_face_region_mediapipe(self, image_array: np.ndarray) -> Optional[np.ndarray]:
        """Extract face region using MediaPipe"""
        try:
            with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                results = face_detection.process(image_array)
                
                if results.detections:
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    
                    h, w, _ = image_array.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Extract face region with some padding
                    padding = 20
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    width = min(w - x, width + 2 * padding)
                    height = min(h - y, height + 2 * padding)
                    
                    face_region = image_array[y:y+height, x:x+width]
                    return face_region
                    
            return None
            
        except Exception as e:
            logger.error(f"Face extraction failed: {e}")
            return None
    
    def _calculate_face_similarity(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """Calculate similarity between two face regions using multiple methods"""
        try:
            # Resize faces to same size for comparison
            target_size = (128, 128)
            face1_resized = cv2.resize(face1, target_size)
            face2_resized = cv2.resize(face2, target_size)
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(face1_resized, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(face2_resized, cv2.COLOR_RGB2GRAY)
            
            # Method 1: Template matching
            result = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)
            template_similarity = np.max(result)
            
            # Method 2: Histogram comparison
            hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
            hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Method 3: Structural similarity (SSIM approximation)
            ssim_score = self._calculate_ssim_approx(gray1, gray2)
            
            # Combine similarities with weights
            combined_similarity = (
                template_similarity * 0.4 +
                hist_similarity * 0.3 +
                ssim_score * 0.3
            )
            
            return max(0.0, min(1.0, combined_similarity))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_ssim_approx(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Approximate SSIM calculation"""
        try:
            # Calculate means
            mu1 = np.mean(img1)
            mu2 = np.mean(img2)
            
            # Calculate variances and covariance
            var1 = np.var(img1)
            var2 = np.var(img2)
            cov = np.mean((img1 - mu1) * (img2 - mu2))
            
            # SSIM constants
            c1 = (0.01 * 255) ** 2
            c2 = (0.03 * 255) ** 2
            
            # SSIM formula
            ssim = ((2 * mu1 * mu2 + c1) * (2 * cov + c2)) / ((mu1**2 + mu2**2 + c1) * (var1 + var2 + c2))
            
            return max(0.0, min(1.0, ssim))
            
        except Exception:
            return 0.0

class BiometricService:
    """Main biometric verification service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.processor = BiometricProcessor()
        self.sessions_collection = db.biometric_sessions
        self.templates_collection = db.biometric_templates
        self.audit_collection = db.biometric_audit
        self.config_collection = db.biometric_config
        
        # Default configuration
        self.config = BiometricConfig()
        
    async def start_verification_session(self, vendor_id: str, session_type: str = "initial_verification") -> BiometricVerificationSession:
        """Start a new biometric verification session"""
        try:
            # Check for existing active session
            existing_session = await self.sessions_collection.find_one({
                "vendor_id": vendor_id,
                "status": {"$in": ["pending", "in_progress"]},
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            
            if existing_session:
                existing_session.pop("_id", None)
                return BiometricVerificationSession(**existing_session)
            
            # Create new session
            session = BiometricVerificationSession(
                vendor_id=vendor_id,
                session_type=session_type,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.config.session_timeout_minutes)
            )
            
            # Calculate next verification date
            if session_type == "initial_verification":
                session.next_verification_due = datetime.now(timezone.utc) + timedelta(days=self.config.verification_validity_days)
            
            # Save session
            session_dict = session.dict()
            await self.sessions_collection.insert_one(session_dict)
            session_dict.pop("_id", None)
            
            # Log audit event
            await self._log_audit_event(vendor_id, session.session_id, "session_started", 
                                       f"Started {session_type} session")
            
            logger.info(f"Biometric verification session started: {session.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to start verification session: {e}")
            raise ValueError(f"Session creation failed: {str(e)}")
    
    async def get_verification_status(self, vendor_id: str) -> VerificationStatusResponse:
        """Get current verification status for vendor"""
        try:
            # Get latest completed session
            latest_session = await self.sessions_collection.find_one(
                {"vendor_id": vendor_id, "status": "verified"},
                sort=[("completed_at", -1)]
            )
            
            if not latest_session:
                return VerificationStatusResponse(
                    vendor_id=vendor_id,
                    current_status=VerificationStatus.PENDING,
                    verification_score=0.0,
                    next_verification_due=None,
                    compliance_status="not_verified",
                    active_templates={}
                )
            
            # Count active templates
            template_counts = {}
            for biometric_type in BiometricType:
                count = await self.templates_collection.count_documents({
                    "vendor_id": vendor_id,
                    "biometric_type": biometric_type.value,
                    "is_active": True
                })
                template_counts[biometric_type] = count
            
            # Determine compliance status
            compliance_status = "compliant"
            if latest_session.get("next_verification_due"):
                if datetime.now(timezone.utc) > latest_session["next_verification_due"]:
                    compliance_status = "verification_expired"
            
            return VerificationStatusResponse(
                vendor_id=vendor_id,
                current_status=VerificationStatus(latest_session["status"]),
                verification_score=latest_session.get("verification_score", 0.0),
                next_verification_due=latest_session.get("next_verification_due"),
                compliance_status=compliance_status,
                active_templates=template_counts
            )
            
        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            return VerificationStatusResponse(
                vendor_id=vendor_id,
                current_status=VerificationStatus.PENDING,
                verification_score=0.0,
                next_verification_due=None,
                compliance_status="error",
                active_templates={}
            )
    
    async def _log_audit_event(self, vendor_id: str, session_id: str, event_type: str, 
                              description: str, success: bool = True, **kwargs):
        """Log audit event"""
        try:
            audit_event = BiometricAuditEvent(
                vendor_id=vendor_id,
                session_id=session_id,
                event_type=event_type,
                event_description=description,
                ip_address=kwargs.get("ip_address", "unknown"),
                user_agent=kwargs.get("user_agent", "unknown"),
                success=success,
                error_message=kwargs.get("error_message"),
                metadata=kwargs.get("metadata", {})
            )
            
            await self.audit_collection.insert_one(audit_event.dict())
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    async def update_session_progress(self, session_id: str) -> float:
        """Calculate and update session completion percentage"""
        try:
            session = await self.sessions_collection.find_one({"session_id": session_id})
            if not session:
                return 0.0
            
            # Calculate completion based on required steps
            completed_steps = 0
            total_steps = 6  # document, liveness, face_match, fingerprint, duplicate_check, risk_assessment
            
            if session.get("document_uploaded", False):
                completed_steps += 1
            if session.get("liveness_completed", False):
                completed_steps += 1
            if session.get("face_match_completed", False):
                completed_steps += 1
            if session.get("fingerprint_captured", False):
                completed_steps += 1
            if session.get("duplicate_check_completed", False):
                completed_steps += 1
            if session.get("risk_assessment"):
                completed_steps += 1
            
            completion_percentage = (completed_steps / total_steps) * 100
            
            # Update session
            await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"completion_percentage": completion_percentage}}
            )
            
            return completion_percentage
            
        except Exception as e:
            logger.error(f"Failed to update session progress: {e}")
            return 0.0