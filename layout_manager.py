"""
Layout manager for TREC inspection report
Handles page layout, text wrapping, and positioning
"""

from typing import List, Tuple, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors


class LayoutManager:
    """Manages PDF layout and positioning"""
    
    def __init__(self, page_width: float = None, page_height: float = None):
        """
        Initialize layout manager
        
        Args:
            page_width: Page width in points (default: letter width)
            page_height: Page height in points (default: letter height)
        """
        if page_width is None or page_height is None:
            page_width, page_height = letter
        
        self.page_width = page_width
        self.page_height = page_height
        
        # Standard margins (in points, 1 inch = 72 points)
        self.margin_left = 0.75 * inch
        self.margin_right = 0.75 * inch
        self.margin_top = 0.75 * inch
        self.margin_bottom = 0.75 * inch
        
        # Calculate usable area
        self.content_width = self.page_width - self.margin_left - self.margin_right
        self.content_height = self.page_height - self.margin_top - self.margin_bottom
        
        # Current Y position (starts at top of content area)
        self.current_y = self.page_height - self.margin_top
        
        # Line spacing
        self.line_height = 14  # points
        self.paragraph_spacing = 8  # points between paragraphs
        
        # Image spacing
        self.image_spacing = 10  # points between images
        self.caption_spacing = 5  # points between image and caption
    
    def reset_position(self):
        """Reset Y position to top of page"""
        self.current_y = self.page_height - self.margin_top
    
    def move_down(self, points: float):
        """Move cursor down by specified points"""
        self.current_y -= points
    
    def move_up(self, points: float):
        """Move cursor up by specified points"""
        self.current_y += points
    
    def has_space(self, required_height: float) -> bool:
        """
        Check if there's enough space on current page
        
        Args:
            required_height: Required height in points
            
        Returns:
            True if space available, False otherwise
        """
        return (self.current_y - required_height) >= self.margin_bottom
    
    def get_remaining_space(self) -> float:
        """Get remaining vertical space on page"""
        return self.current_y - self.margin_bottom
    
    def wrap_text(self, text: str, max_width: float, font_name: str = 'Helvetica', 
                  font_size: int = 10) -> List[str]:
        """
        Wrap text to fit within max width
        
        Args:
            text: Text to wrap
            max_width: Maximum width in points
            font_name: Font name
            font_size: Font size in points
            
        Returns:
            List of text lines
        """
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        if not text:
            return []
        
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        # Approximate character width (more accurate would use actual font metrics)
        char_width = font_size * 0.5
        
        for word in words:
            word_width = len(word) * char_width + char_width  # +space
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_text_height(self, text: str, max_width: float, 
                             font_name: str = 'Helvetica', 
                             font_size: int = 10) -> float:
        """
        Calculate height required for text
        
        Args:
            text: Text content
            max_width: Maximum width
            font_name: Font name
            font_size: Font size
            
        Returns:
            Required height in points
        """
        lines = self.wrap_text(text, max_width, font_name, font_size)
        return len(lines) * self.line_height
    
    def calculate_image_height(self, img_width: int, img_height: int, 
                              max_width: float, include_caption: bool = True) -> float:
        """
        Calculate height required for image with optional caption
        
        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
            max_width: Maximum width in points
            include_caption: Include space for caption
            
        Returns:
            Required height in points
        """
        # Calculate scaled dimensions
        aspect = img_width / img_height if img_height > 0 else 1
        scaled_width = min(img_width, max_width)
        scaled_height = scaled_width / aspect
        
        total_height = scaled_height
        
        if include_caption:
            total_height += self.caption_spacing + self.line_height
        
        total_height += self.image_spacing
        
        return total_height
    
    def position_image(self, img_width: int, img_height: int, 
                      max_width: float) -> Tuple[float, float, float, float]:
        """
        Calculate image position and scaled dimensions
        
        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
            max_width: Maximum width in points
            
        Returns:
            Tuple of (x, y, scaled_width, scaled_height)
        """
        # Calculate scaled dimensions maintaining aspect ratio
        aspect = img_width / img_height if img_height > 0 else 1
        scaled_width = min(img_width, max_width)
        scaled_height = scaled_width / aspect
        
        # Center horizontally within content area
        x = self.margin_left + (self.content_width - scaled_width) / 2
        
        # Position at current Y (top of image)
        y = self.current_y - scaled_height
        
        return (x, y, scaled_width, scaled_height)
    
    def can_fit_images(self, num_images: int, avg_height: float) -> bool:
        """
        Check if multiple images can fit on current page
        
        Args:
            num_images: Number of images
            avg_height: Average height per image
            
        Returns:
            True if images fit, False otherwise
        """
        total_height = num_images * (avg_height + self.image_spacing)
        return self.has_space(total_height)
    
    def get_content_x(self) -> float:
        """Get X position for left-aligned content"""
        return self.margin_left
    
    def get_center_x(self) -> float:
        """Get X position for centered content"""
        return self.page_width / 2
    
    def get_right_x(self) -> float:
        """Get X position for right-aligned content"""
        return self.page_width - self.margin_right
    
    def format_multiline_text(self, canvas_obj, text: str, x: float, y: float,
                             max_width: float, font_name: str = 'Helvetica',
                             font_size: int = 10, leading: Optional[float] = None):
        """
        Draw multiline text on canvas
        
        Args:
            canvas_obj: ReportLab canvas object
            text: Text to draw
            x: X position
            y: Y position (top of text block)
            max_width: Maximum width
            font_name: Font name
            font_size: Font size
            leading: Line spacing (uses line_height if None)
        """
        if leading is None:
            leading = self.line_height
        
        lines = self.wrap_text(text, max_width, font_name, font_size)
        
        canvas_obj.setFont(font_name, font_size)
        text_obj = canvas_obj.beginText(x, y)
        text_obj.setFont(font_name, font_size)
        text_obj.setLeading(leading)
        
        for line in lines:
            text_obj.textLine(line)
        
        canvas_obj.drawText(text_obj)
        
        return len(lines) * leading


if __name__ == '__main__':
    # Test the layout manager
    layout = LayoutManager()
    
    print("=== LAYOUT MANAGER TEST ===")
    print(f"Page size: {layout.page_width} x {layout.page_height}")
    print(f"Content area: {layout.content_width} x {layout.content_height}")
    print(f"Margins: L={layout.margin_left}, R={layout.margin_right}, T={layout.margin_top}, B={layout.margin_bottom}")
    print(f"\nInitial Y position: {layout.current_y}")
    print(f"Remaining space: {layout.get_remaining_space()}")
    
    # Test text wrapping
    test_text = "This is a very long line of text that should be wrapped to fit within the specified maximum width of the content area. Let's see how it handles multiple sentences and longer paragraphs."
    lines = layout.wrap_text(test_text, layout.content_width)
    print(f"\nWrapped text ({len(lines)} lines):")
    for i, line in enumerate(lines, 1):
        print(f"  {i}. {line}")
    
    # Test space checking
    print(f"\nHas space for 100 points? {layout.has_space(100)}")
    print(f"Has space for 1000 points? {layout.has_space(1000)}")
    
    # Test image positioning
    img_x, img_y, img_w, img_h = layout.position_image(800, 600, 300)
    print(f"\nImage position (800x600 scaled to max 300): x={img_x:.1f}, y={img_y:.1f}, w={img_w:.1f}, h={img_h:.1f}")

