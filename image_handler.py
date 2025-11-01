"""
Image handler for TREC inspection report
Downloads and processes images from URLs
"""

import requests
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple
import os


class ImageHandler:
    """Handles image downloading, resizing, and processing"""
    
    def __init__(self, max_width: int = 400, max_height: int = 300):
        """
        Initialize image handler
        
        Args:
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
        """
        self.max_width = max_width
        self.max_height = max_height
        self.cache = {}  # Cache downloaded images
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """
        Download image from URL
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            PIL Image object or None if failed
        """
        # Check cache first
        if url in self.cache:
            return self.cache[url]
        
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Load image from response
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Cache the image
            self.cache[url] = img
            return img
            
        except Exception as e:
            print(f"Failed to download image from {url}: {str(e)}")
            return None
    
    def resize_image(self, img: Image.Image, max_width: Optional[int] = None, 
                    max_height: Optional[int] = None) -> Image.Image:
        """
        Resize image maintaining aspect ratio
        
        Args:
            img: PIL Image object
            max_width: Maximum width (uses instance default if None)
            max_height: Maximum height (uses instance default if None)
            
        Returns:
            Resized PIL Image object
        """
        if max_width is None:
            max_width = self.max_width
        if max_height is None:
            max_height = self.max_height
        
        # Calculate aspect ratio
        width, height = img.size
        aspect = width / height
        
        # Determine new size
        if width > max_width or height > max_height:
            if aspect > 1:  # Wider than tall
                new_width = min(width, max_width)
                new_height = int(new_width / aspect)
                if new_height > max_height:
                    new_height = max_height
                    new_width = int(new_height * aspect)
            else:  # Taller than wide
                new_height = min(height, max_height)
                new_width = int(new_height * aspect)
                if new_width > max_width:
                    new_width = max_width
                    new_height = int(new_width / aspect)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    def process_image(self, url: str, max_width: Optional[int] = None, 
                     max_height: Optional[int] = None) -> Optional[Tuple[Image.Image, int, int]]:
        """
        Download and process image from URL
        
        Args:
            url: Image URL
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Tuple of (PIL Image, width, height) or None if failed
        """
        img = self.download_image(url)
        if img is None:
            return None
        
        img = self.resize_image(img, max_width, max_height)
        return (img, img.width, img.height)
    
    def save_image_temp(self, img: Image.Image, filename: str = 'temp_image.jpg') -> str:
        """
        Save image to temporary file
        
        Args:
            img: PIL Image object
            filename: Temporary filename
            
        Returns:
            Path to saved file
        """
        temp_path = f"/tmp/{filename}"
        img.save(temp_path, 'JPEG', quality=85)
        return temp_path
    
    def get_image_dimensions(self, img: Image.Image) -> Tuple[int, int]:
        """Get image dimensions"""
        return img.size
    
    def create_placeholder_image(self, width: int = 300, height: int = 200, 
                                 text: str = "Image Not Available") -> Image.Image:
        """
        Create a placeholder image when actual image fails to load
        
        Args:
            width: Image width
            height: Image height
            text: Text to display
            
        Returns:
            PIL Image object
        """
        from PIL import ImageDraw, ImageFont
        
        # Create gray background
        img = Image.new('RGB', (width, height), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        
        # Add border
        draw.rectangle([0, 0, width-1, height-1], outline=(100, 100, 100), width=2)
        
        # Add text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Calculate text position (center)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 6
            text_height = 10
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=(100, 100, 100), font=font)
        
        return img


if __name__ == '__main__':
    # Test the image handler
    handler = ImageHandler(max_width=400, max_height=300)
    
    # Test with a placeholder
    print("Creating placeholder image...")
    placeholder = handler.create_placeholder_image()
    print(f"Placeholder size: {placeholder.size}")
    
    # You would test with real URLs like:
    # test_url = "https://example.com/image.jpg"
    # result = handler.process_image(test_url)
    # if result:
    #     img, width, height = result
    #     print(f"Processed image: {width}x{height}")

