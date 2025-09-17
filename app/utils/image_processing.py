from PIL import Image
import io
import base64
from fastapi import HTTPException

def resize_image_base64(base64_string: str, max_width: int = 1024, max_height: int = 1024) -> str:
    """
    Resize an image from base64 string and return as base64
    """
    try:
        if base64_string.startswith('data:image/'):
            base64_string = base64_string.split(',', 1)[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        image_format = image.format or 'PNG'
        image.save(buffered, format=image_format)
        resized_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return f"data:image/{image_format.lower()};base64,{resized_base64}"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

def validate_image_dimensions(base64_string: str, max_size_mb: int = 10) -> bool:
    """
    Validate image dimensions and size
    """
    try:
        if base64_string.startswith('data:image/'):
            base64_string = base64_string.split(',', 1)[1]
        
        size_bytes = len(base64_string) * 3 / 4  
        if size_bytes > max_size_mb * 1024 * 1024:
            return False
            
        return True
        
    except Exception:
        return False