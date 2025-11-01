"""
Main TREC Report Generator
Orchestrates all modules to generate output_pdf.pdf
"""

import fitz  # PyMuPDF
from data_mapper import DataMapper
from image_handler import ImageHandler
from video_handler import VideoHandler
from layout_manager import LayoutManager
from trec_field_mapper import TRECFieldMapper
from io import BytesIO
from datetime import datetime


class TRECReportGenerator:
    """Main generator for TREC inspection reports"""
    
    def __init__(self, json_path: str, template_path: str):
        """
        Initialize generator
        
        Args:
            json_path: Path to inspection.json
            template_path: Path to TREC template PDF
        """
        self.json_path = json_path
        self.template_path = template_path
        self.data_mapper = DataMapper(json_path)
        self.image_handler = ImageHandler(max_width=350, max_height=250)
        self.video_handler = VideoHandler()
        self.layout = LayoutManager()
        self.field_mapper = TRECFieldMapper(template_path)
        self.doc = None
    
    def generate_report(self, output_path: str):
        """
        Generate the complete TREC report
        
        Args:
            output_path: Output PDF path
        """
        try:
            print("\n" + "="*60)
            print("TREC INSPECTION REPORT GENERATOR")
            print("="*60)
            
            # Step 1: Open template
            print("\n[1/6] Opening template PDF...")
            self.doc = fitz.open(self.template_path)
            print(f"      Template has {len(self.doc)} pages")
            
            # Step 2: Fill header fields
            print("\n[2/6] Filling header fields...")
            self._fill_header_fields()
            
            # Step 3: Fill inspection checkboxes in form fields
            print("\n[3/6] Filling inspection checkboxes...")
            self._fill_inspection_checkboxes()
            
            # Step 3.5: Add detailed inspection pages
            print("\n[3.5/6] Processing inspection sections...")
            self._process_sections()
            
            # Step 4: Add images
            print("\n[4/6] Adding inspection photos...")
            self._add_photos()
            
            # Step 5: Add video links
            print("\n[5/6] Adding video links...")
            self._add_videos()
            
            # Step 6: Save
            print("\n[6/6] Saving final PDF...")
            self.doc.save(output_path, garbage=4, deflate=True)
            print(f"      ✓ Saved to: {output_path}")
            
            print("\n" + "="*60)
            print("REPORT GENERATION COMPLETE!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n✗ Error generating report: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            if self.doc:
                self.doc.close()
    
    def _fill_header_fields(self):
        """Fill header information in template"""
        header_fields = self.data_mapper.get_header_fields()
        
        # Fill first page fields
        page = self.doc[0]
        filled_count = 0
        
        for widget in page.widgets():
            field_name = widget.field_name
            if field_name in header_fields:
                value = header_fields[field_name]
                try:
                    widget.field_value = value
                    widget.update()
                    filled_count += 1
                    print(f"      ✓ {field_name}: {value[:50]}...")
                except Exception as e:
                    print(f"      ✗ Failed to fill {field_name}: {e}")
        
        print(f"      Filled {filled_count} header fields")
    
    def _fill_inspection_checkboxes(self):
        """Fill inspection status checkboxes on TREC form pages 3-6"""
        sections = self.data_mapper.get_sections()
        
        # Collect all line items from all sections
        all_line_items = []
        for section in sections:
            line_items = self.data_mapper.get_line_items_for_section(section)
            for item in line_items:
                all_line_items.append({
                    'section': section.get('name', 'Unknown'),
                    'name': item.get('name', 'Unknown'),
                    'inspectionStatus': item.get('inspectionStatus'),
                    'comments': item.get('comments', [])
                })
        
        print(f"      Total line items to map: {len(all_line_items)}")
        
        # Fill checkboxes on pages 3-6 (page numbers 2-5 in 0-indexed)
        total_checkboxes_filled = 0
        total_items_processed = 0
        
        # Map line items to form pages
        # Page 3 (idx 2): ~12 items
        # Page 4 (idx 3): ~10 items  
        # Page 5 (idx 4): ~12 items
        # Page 6 (idx 5): ~7 items
        
        page_mappings = [
            (2, 0, 12),   # Page 3: items 0-11
            (3, 12, 22),  # Page 4: items 12-21
            (4, 22, 34),  # Page 5: items 22-33
            (5, 34, 41),  # Page 6: items 34-40
        ]
        
        for page_idx, start_idx, end_idx in page_mappings:
            items_for_page = all_line_items[start_idx:end_idx]
            if items_for_page:
                filled, processed = self.field_mapper.fill_line_items_on_page(
                    self.doc, page_idx, items_for_page
                )
                total_checkboxes_filled += filled
                total_items_processed += processed
                print(f"      Page {page_idx + 1}: Filled {filled} checkboxes for {processed} items")
        
        print(f"      Total: {total_checkboxes_filled} checkboxes filled for {total_items_processed} line items")
    
    def _process_sections(self):
        """Process all inspection sections and add to PDF"""
        sections = self.data_mapper.get_sections()
        print(f"      Processing {len(sections)} sections...")
        
        # We'll add content as additional pages after the template
        # For now, let's add a summary page
        
        total_items = 0
        deficient_items = 0
        
        for section in sections:
            line_items = self.data_mapper.get_line_items_for_section(section)
            total_items += len(line_items)
            
            for item in line_items:
                if item.get('inspectionStatus') == 'D' or item.get('isDeficient'):
                    deficient_items += 1
        
        print(f"      Total line items: {total_items}")
        print(f"      Deficient items: {deficient_items}")
        
        # Add a new page for inspection details
        new_page = self.doc.new_page()
        page_num = len(self.doc) - 1
        
        # Add title
        y_pos = 50
        self._add_text(page_num, "INSPECTION DETAILS", 50, y_pos, 
                      font_size=16, bold=True)
        y_pos += 40
        
        # Add sections
        section_count = 0
        for section in sections:
            if y_pos > 720:  # Near bottom
                new_page = self.doc.new_page()
                page_num = len(self.doc) - 1
                y_pos = 50
            
            section_name = section.get('name', 'Unknown Section')
            self._add_text(page_num, section_name, 50, y_pos, 
                          font_size=12, bold=True)
            y_pos += 20
            
            line_items = self.data_mapper.get_line_items_for_section(section)
            for item in line_items[:5]:  # Limit items to prevent overflow
                if y_pos > 730:
                    new_page = self.doc.new_page()
                    page_num = len(self.doc) - 1
                    y_pos = 50
                
                item_name = item.get('name', 'Unknown')
                status = self.data_mapper.get_status_label(item.get('inspectionStatus'))
                
                # Format based on status
                if item.get('inspectionStatus') == 'D':
                    color = (0.8, 0, 0)  # Red for deficient
                    status_str = f"  • {item_name}: {status} ⚠"
                else:
                    color = (0, 0, 0)  # Black
                    status_str = f"  • {item_name}: {status}"
                
                self._add_text(page_num, status_str, 60, y_pos, 
                              font_size=9, color=color)
                y_pos += 15
                
                # Add comments
                comments = self.data_mapper.get_comments_for_line_item(item)
                for comment in comments[:1]:  # First comment only
                    comment_text = comment.get('text', '')
                    if comment_text and len(comment_text) > 10:
                        # Truncate long comments
                        display_text = comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
                        self._add_text(page_num, f"    {display_text}", 
                                      70, y_pos, font_size=8, color=(0.3, 0.3, 0.3))
                        y_pos += 12
            
            y_pos += 10  # Space between sections
            section_count += 1
            
            if section_count >= 10:  # Limit sections to prevent too many pages
                break
        
        print(f"      Added {section_count} sections to report")
    
    def _add_photos(self):
        """Add photo pages to report"""
        photos, _ = self.data_mapper.get_all_media()
        
        if not photos:
            print("      No photos found")
            return
        
        print(f"      Found {len(photos)} photos")
        
        # Add new page for photos
        photo_page = self.doc.new_page()
        page_num = len(self.doc) - 1
        
        y_pos = 50
        self._add_text(page_num, "INSPECTION PHOTOS", 50, y_pos, 
                      font_size=16, bold=True)
        y_pos += 40
        
        photos_added = 0
        photos_per_page = 3  # Limit to 3 photos per page
        
        for i, photo in enumerate(photos):
            # Check if we need a new page
            if photos_added > 0 and photos_added % photos_per_page == 0:
                photo_page = self.doc.new_page()
                page_num = len(self.doc) - 1
                y_pos = 50
            
            url = photo.get('url', '')
            if not url:
                continue
            
            try:
                # Download and process image
                result = self.image_handler.process_image(url, max_width=400, max_height=200)
                if result:
                    img, img_width, img_height = result
                    
                    # Check space on page
                    if y_pos + img_height + 50 > 750:
                        photo_page = self.doc.new_page()
                        page_num = len(self.doc) - 1
                        y_pos = 50
                    
                    # Convert PIL image to bytes
                    img_bytes = BytesIO()
                    img.save(img_bytes, format='JPEG', quality=85)
                    img_bytes = img_bytes.getvalue()
                    
                    # Center image horizontally
                    x_pos = (612 - img_width) / 2  # Letter width = 612
                    
                    # Add image
                    page = self.doc[page_num]
                    rect = fitz.Rect(x_pos, y_pos, x_pos + img_width, y_pos + img_height)
                    page.insert_image(rect, stream=img_bytes)
                    
                    # Add caption
                    caption = f"{photo.get('section_name', '')}: {photo.get('line_item_name', '')}"
                    self._add_text(page_num, caption, 50, y_pos + img_height + 10, 
                                  font_size=8, color=(0.3, 0.3, 0.3))
                    
                    y_pos += img_height + 35
                    photos_added += 1
                    
                    # Limit total photos
                    if photos_added >= 12:
                        break
            
            except Exception as e:
                print(f"      ✗ Failed to add photo: {e}")
                continue
        
        print(f"      Added {photos_added} photos to report")
    
    def _add_videos(self):
        """Add video links to report"""
        _, videos = self.data_mapper.get_all_media()
        
        if not videos:
            print("      No videos found")
            return
        
        print(f"      Found {len(videos)} videos")
        
        # Add new page for videos
        video_page = self.doc.new_page()
        page_num = len(self.doc) - 1
        
        y_pos = 50
        self._add_text(page_num, "INSPECTION VIDEOS", 50, y_pos, 
                      font_size=16, bold=True)
        y_pos += 40
        
        videos_added = 0
        for i, video in enumerate(videos, 1):
            url = video.get('url', '')
            
            if not url or not self.video_handler.validate_url(url):
                continue
            
            if y_pos > 720:
                video_page = self.doc.new_page()
                page_num = len(self.doc) - 1
                y_pos = 50
            
            # Add video description
            video_text = f"Video {i}: {video.get('section_name', '')} - {video.get('line_item_name', '')}"
            self._add_text(page_num, video_text, 50, y_pos, 
                          font_size=10, color=(0, 0, 0.8))
            
            # Add clickable link
            page = self.doc[page_num]
            link_rect = fitz.Rect(50, y_pos - 10, 400, y_pos + 5)
            page.insert_link({'kind': fitz.LINK_URI, 'from': link_rect, 'uri': url})
            
            y_pos += 25
            videos_added += 1
            
            # Limit total videos
            if videos_added >= 15:
                break
        
        print(f"      Added {videos_added} video links to report")
    
    def _add_text(self, page_num: int, text: str, x: float, y: float,
                  font_size: int = 10, color: tuple = (0, 0, 0), bold: bool = False):
        """
        Add text to a page
        
        Args:
            page_num: Page number
            text: Text content
            x: X position
            y: Y position
            font_size: Font size
            color: RGB color tuple (0-1 range)
            bold: Use bold font
        """
        page = self.doc[page_num]
        # Use PyMuPDF built-in fonts (Base14 fonts)
        font = "Helvetica-Bold" if bold else "Helvetica"
        page.insert_text((x, y), text, fontsize=font_size, color=color, fontname=font)


def main():
    """Main entry point for TREC report generation"""
    import os
    
    # Paths
    json_path = 'inspection.json'
    template_path = 'TREC_Template_Blank.pdf'
    output_path = 'output_pdf.pdf'
    
    # Check files exist
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return
    
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found")
        return
    
    # Generate report
    generator = TRECReportGenerator(json_path, template_path)
    generator.generate_report(output_path)


if __name__ == '__main__':
    main()

