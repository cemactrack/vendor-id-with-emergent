from fastapi import UploadFile, HTTPException
from PIL import Image
import base64
from io import BytesIO
import os

class UploadService:
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def validate_image(file: UploadFile) -> None:
        """Validate uploaded image file"""
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        extension = file.filename.split('.')[-1].lower()
        if extension not in UploadService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(UploadService.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        if hasattr(file, 'size') and file.size > UploadService.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    @staticmethod
    async def process_image(file: UploadFile) -> str:
        """Process and convert image to base64"""
        UploadService.validate_image(file)
        
        # Read file content
        content = await file.read()
        
        # Check actual file size
        if len(content) > UploadService.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
        
        try:
            # Open and process image
            image = Image.open(BytesIO(content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize if too large (max 800x800)
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            base64_string = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{base64_string}"
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    @staticmethod
    def validate_base64_image(base64_string: str) -> bool:
        """Validate base64 image string"""
        try:
            if base64_string.startswith('data:image/'):
                # Extract base64 part
                base64_data = base64_string.split(',')[1]
            else:
                base64_data = base64_string
            
            # Decode and validate
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            image.verify()
            return True
        except Exception:
            return False