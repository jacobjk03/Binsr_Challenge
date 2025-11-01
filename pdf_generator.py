"""
PDF Generator for TREC inspection report
Fills form fields and adds content using PyMuPDF
"""

import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional
from data_mapper import DataMapper
from image_handler import ImageHandler
from video_handler import VideoHandler
from io import BytesIO
from PIL import Image


class PDFGenerator:
    """Generates TREC PDF reports"""
    
    def __init__(self, template_path: str, data_mapper: DataMapper):
        """
        Initialize PDF generator
        
        Args:
            template_path: Path to TREC template PDF
            data_mapper: DataMapper instance
        """
        self.template_path = template_path
        self.data_mapper = data_mapper
        self.image_handler = ImageHandler(max_width=400, max_height=300)
        self.video_handler = VideoHandler()
        self.doc = None
    
    def open_template(self):
        """Open the template PDF"""
        self.doc = fitz.open(self.template_path)
    
    def close_document(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
    
    def fill_header_fields(self):
        """Fill header fields in the template"""
        if not self.doc:
            raise ValueError("Document not opened")
        
        header_fields = self.data_mapper.get_header_fields()
        
        # Fill fields on first page
        page = self.doc[0]
        for widget in page.widgets():
            field_name = widget.field_name
            if field_name in header_fields:
                value = header_fields[field_name]
                widget.field_value = value
                widget.update()
                print(f"Filled field '{field_name}': {value[:50]}")
    
    def fill_form_fields(self, field_mapping: Dict[str, str]):
        """
        Fill specific form fields
        
        Args:
            field_mapping: Dictionary of field_name -> value
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            for widget in page.widgets():
                field_name = widget.field_name
                if field_name in field_mapping:
                    value = field_mapping[field_name]
                    if widget.field_type == 2:  # Checkbox
                        widget.field_value = value  # True/False
                    else:
                        widget.field_value = str(value)
                    widget.update()
    
    def add_text_to_page(self, page_num: int, text: str, x: float, y: float,
                        font_size: int = 10, color: tuple = (0, 0, 0)):
        """
        Add text to a specific page
        
        Args:
            page_num: Page number (0-based)
            text: Text to add
            x: X position
            y: Y position
            font_size: Font size
            color: RGB color tuple (0-1 range)
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        page = self.doc[page_num]
        point = fitz.Point(x, y)
        page.insert_text(point, text, fontsize=font_size, color=color)
    
    def add_image_to_page(self, page_num: int, image_data: bytes, 
                         x: float, y: float, width: float, height: float):
        """
        Add image to a specific page
        
        Args:
            page_num: Page number (0-based)
            image_data: Image bytes
            x: X position
            y: Y position
            width: Image width
            height: Image height
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + width, y + height)
        page.insert_image(rect, stream=image_data)
    
    def add_link_to_page(self, page_num: int, x: float, y: float, 
                        width: float, height: float, url: str):
        """
        Add clickable link to page
        
        Args:
            page_num: Page number (0-based)
            x: X position
            y: Y position
            width: Link area width
            height: Link area height
            url: URL to link to
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + width, y + height)
        link = {
            'kind': fitz.LINK_URI,
            'from': rect,
            'uri': url
        }
        page.insert_link(link)
    
    def add_new_page(self) -> int:
        """
        Add a new blank page to the document
        
        Returns:
            Page number of new page
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        new_page = self.doc.new_page()
        return len(self.doc) - 1
    
    def add_content_section(self, section: Dict[str, Any], start_page: int = 1) -> int:
        """
        Add a section with line items to the PDF
        
        Args:
            section: Section dictionary
            start_page: Page to start adding content
            
        Returns:
            Current page number after adding content
        """
        current_page = start_page
        y_position = 100  # Start position on page
        
        # Add section name
        section_name = section.get('name', 'Unknown Section')
        self.add_text_to_page(current_page, section_name, 50, y_position, 
                             font_size=12, color=(0, 0, 0))
        y_position += 20
        
        # Add line items
        line_items = self.data_mapper.get_line_items_for_section(section)
        for line_item in line_items:
            # Check if we need a new page
            if y_position > 700:  # Near bottom of page
                current_page = self.add_new_page()
                y_position = 50
            
            # Add line item name
            item_name = line_item.get('name', 'Unknown Item')
            status = self.data_mapper.get_status_label(line_item.get('inspectionStatus'))
            self.add_text_to_page(current_page, f"{item_name}: {status}", 
                                 70, y_position, font_size=10)
            y_position += 15
            
            # Add comments
            comments = self.data_mapper.get_comments_for_line_item(line_item)
            for comment in comments:
                comment_text = comment.get('text', '')
                if comment_text:
                    # Wrap text if too long
                    max_chars = 80
                    if len(comment_text) > max_chars:
                        # Simple wrapping
                        words = comment_text.split()
                        lines = []
                        current_line = []
                        current_length = 0
                        for word in words:
                            if current_length + len(word) + 1 <= max_chars:
                                current_line.append(word)
                                current_length += len(word) + 1
                            else:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                                current_length = len(word)
                        if current_line:
                            lines.append(' '.join(current_line))
                        
                        for line in lines[:3]:  # Limit to 3 lines per comment
                            if y_position > 700:
                                current_page = self.add_new_page()
                                y_position = 50
                            self.add_text_to_page(current_page, line, 90, y_position, font_size=9)
                            y_position += 12
                    else:
                        self.add_text_to_page(current_page, comment_text[:80], 
                                            90, y_position, font_size=9)
                        y_position += 12
        
        return current_page
    
    def add_media_pages(self):
        """Add pages with images and video links"""
        if not self.doc:
            raise ValueError("Document not opened")
        
        photos, videos = self.data_mapper.get_all_media()
        
        if not photos and not videos:
            print("No media found to add")
            return
        
        # Add a new page for media
        media_page = self.add_new_page()
        y_pos = 50
        
        # Add photos
        if photos:
            self.add_text_to_page(media_page, "INSPECTION PHOTOS", 50, y_pos, 
                                font_size=14, color=(0, 0, 0))
            y_pos += 30
            
            photo_count = 0
            for photo in photos[:10]:  # Limit to first 10 photos
                if y_pos > 650:  # Need new page
                    media_page = self.add_new_page()
                    y_pos = 50
                
                # Download and add image
                url = photo.get('url', '')
                if url:
                    try:
                        result = self.image_handler.process_image(url, max_width=400, max_height=250)
                        if result:
                            img, img_width, img_height = result
                            
                            # Convert PIL image to bytes
                            img_bytes = BytesIO()
                            img.save(img_bytes, format='JPEG')
                            img_bytes = img_bytes.getvalue()
                            
                            # Add image
                            self.add_image_to_page(media_page, img_bytes, 100, y_pos, 
                                                  img_width * 0.5, img_height * 0.5)
                            
                            # Add caption
                            caption = f"{photo.get('section_name', '')}: {photo.get('line_item_name', '')}"
                            self.add_text_to_page(media_page, caption, 100, 
                                                y_pos + img_height * 0.5 + 10, font_size=8)
                            
                            y_pos += img_height * 0.5 + 30
                            photo_count += 1
                    except Exception as e:
                        print(f"Failed to add photo: {e}")
        
        # Add video links
        if videos:
            if y_pos > 600:
                media_page = self.add_new_page()
                y_pos = 50
            
            self.add_text_to_page(media_page, "INSPECTION VIDEOS", 50, y_pos, 
                                font_size=14, color=(0, 0, 0))
            y_pos += 30
            
            for i, video in enumerate(videos[:10], 1):  # Limit to first 10 videos
                if y_pos > 700:
                    media_page = self.add_new_page()
                    y_pos = 50
                
                url = video.get('url', '')
                if url and self.video_handler.validate_url(url):
                    link_text = f"Video {i}: {video.get('section_name', '')} - {video.get('line_item_name', '')}"
                    self.add_text_to_page(media_page, link_text, 70, y_pos, font_size=10, color=(0, 0, 1))
                    
                    # Add clickable link
                    self.add_link_to_page(media_page, 70, y_pos - 10, 200, 15, url)
                    
                    y_pos += 20
    
    def save(self, output_path: str):
        """
        Save the PDF to file
        
        Args:
            output_path: Output file path
        """
        if not self.doc:
            raise ValueError("Document not opened")
        
        self.doc.save(output_path)
        print(f"PDF saved to: {output_path}")
    
    def generate(self, output_path: str):
        """
        Main generation method
        
        Args:
            output_path: Output file path
        """
        try:
            print("Opening template...")
            self.open_template()
            
            print("Filling header fields...")
            self.fill_header_fields()
            
            print("Adding media pages...")
            self.add_media_pages()
            
            print("Saving PDF...")
            self.save(output_path)
            
        finally:
            print("Closing document...")
            self.close_document()


if __name__ == '__main__':
    # Test the PDF generator
    print("=== PDF GENERATOR TEST ===")
    
    mapper = DataMapper('inspection.json')
    generator = PDFGenerator('TREC_Template_Blank.pdf', mapper)
    
    print("Generating test PDF...")
    generator.generate('test_output.pdf')
    print("Done!")

