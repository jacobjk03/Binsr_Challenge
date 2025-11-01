"""
Bonus PDF Generator - Creative visualization of inspection data
Generates bonus_pdf.pdf with enhanced layout and design
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from data_mapper import DataMapper
from image_handler import ImageHandler
from video_handler import VideoHandler
from datetime import datetime
from io import BytesIO


class BonusPDFGenerator:
    """Generates creative bonus PDF report"""
    
    def __init__(self, json_path: str):
        """
        Initialize bonus generator
        
        Args:
            json_path: Path to inspection.json
        """
        self.json_path = json_path
        self.data_mapper = DataMapper(json_path)
        self.image_handler = ImageHandler(max_width=300, max_height=200)
        self.video_handler = VideoHandler()
        
        # Page setup
        self.page_width, self.page_height = letter
        self.margin = 0.75 * inch
        self.content_width = self.page_width - (2 * self.margin)
    
    def generate_report(self, output_path: str):
        """
        Generate the bonus PDF report
        
        Args:
            output_path: Output PDF path
        """
        try:
            print("\n" + "="*60)
            print("BONUS PDF REPORT GENERATOR")
            print("="*60)
            
            c = canvas.Canvas(output_path, pagesize=letter)
            
            # Page 1: Cover and Summary
            print("\n[1/5] Creating cover page...")
            self._create_cover_page(c)
            c.showPage()
            
            # Page 2: Statistics Dashboard
            print("\n[2/5] Creating statistics dashboard...")
            self._create_stats_page(c)
            c.showPage()
            
            # Page 3: Deficiencies Summary
            print("\n[3/5] Creating deficiencies summary...")
            self._create_deficiencies_page(c)
            c.showPage()
            
            # Page 4+: Photo Gallery
            print("\n[4/5] Creating photo gallery...")
            pages_created = self._create_photo_gallery(c)
            
            # Video Links
            print("\n[5/5] Adding video links...")
            self._create_video_page(c)
            c.showPage()
            
            # Save
            c.save()
            print(f"\n      ✓ Saved to: {output_path}")
            
            print("\n" + "="*60)
            print("BONUS REPORT GENERATION COMPLETE!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n✗ Error generating bonus report: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_cover_page(self, c: canvas.Canvas):
        """Create attractive cover page"""
        # Draw header background
        c.setFillColorRGB(0.1, 0.3, 0.6)
        c.rect(0, self.page_height - 3*inch, self.page_width, 3*inch, fill=1)
        
        # Title
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(self.page_width/2, self.page_height - 1.5*inch, 
                           "HOME INSPECTION")
        
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(self.page_width/2, self.page_height - 2*inch, 
                           "EXECUTIVE SUMMARY")
        
        # Property info
        c.setFillColorRGB(0, 0, 0)
        y_pos = self.page_height - 4*inch
        
        header_fields = self.data_mapper.get_header_fields()
        prop_info = self.data_mapper.get_property_info()
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.margin, y_pos, "Property Information")
        y_pos -= 30
        
        c.setFont("Helvetica", 11)
        info_items = [
            ("Address:", header_fields.get('Address of Inspected Property', 'N/A')),
            ("Client:", header_fields.get('Name of Client', 'N/A')),
            ("Inspector:", header_fields.get('Name of Inspector', 'N/A')),
            ("Date:", header_fields.get('Date of Inspection', 'N/A')),
        ]
        
        for label, value in info_items:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(self.margin, y_pos, label)
            c.setFont("Helvetica", 10)
            # Truncate long values
            display_value = value[:60] + "..." if len(value) > 60 else value
            c.drawString(self.margin + 1.5*inch, y_pos, display_value)
            y_pos -= 20
        
        # Quick stats box
        y_pos -= 30
        stats = self.data_mapper.get_summary_stats()
        
        # Draw stats box
        box_y = y_pos - 150
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(self.margin, box_y, self.content_width, 140, fill=1)
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.page_width/2, y_pos - 30, "INSPECTION OVERVIEW")
        
        # Stats in columns
        col1_x = self.margin + 1*inch
        col2_x = self.margin + 4*inch
        stat_y = y_pos - 60
        
        c.setFont("Helvetica", 10)
        stats_to_show = [
            ("Total Sections:", str(stats['total_sections'])),
            ("Total Items:", str(stats['total_line_items'])),
            ("Deficient Items:", str(stats['deficient'])),
            ("Photos:", str(stats['total_photos'])),
            ("Videos:", str(stats['total_videos'])),
        ]
        
        for i, (label, value) in enumerate(stats_to_show):
            x_pos = col1_x if i < 3 else col2_x
            y = stat_y - (i % 3) * 25
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_pos, y, label)
            c.setFont("Helvetica", 10)
            c.drawString(x_pos + 1.2*inch, y, value)
        
        # Footer
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(self.page_width/2, 1*inch, 
                           "This is a supplementary report - refer to full TREC report for complete details")
    
    def _create_stats_page(self, c: canvas.Canvas):
        """Create statistics dashboard page"""
        c.setFont("Helvetica-Bold", 20)
        c.drawString(self.margin, self.page_height - self.margin - 20, 
                    "Inspection Statistics Dashboard")
        
        y_pos = self.page_height - self.margin - 80
        
        # Get statistics
        stats = self.data_mapper.get_summary_stats()
        
        # Create visual bar representation
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin, y_pos, "Items by Status:")
        y_pos -= 30
        
        # Status categories
        status_data = [
            ("Inspected", stats['inspected'], (0.2, 0.6, 0.2)),
            ("Not Inspected", stats['not_inspected'], (0.8, 0.8, 0)),
            ("Not Present", stats['not_present'], (0.5, 0.5, 0.5)),
            ("Deficient", stats['deficient'], (0.8, 0.2, 0.2)),
        ]
        
        max_val = max(item[1] for item in status_data) or 1
        bar_width = 4*inch
        bar_height = 25
        
        for label, count, color in status_data:
            # Draw bar
            bar_length = (count / max_val) * bar_width if max_val > 0 else 0
            c.setFillColorRGB(*color)
            c.rect(self.margin + 1.5*inch, y_pos, bar_length, bar_height, fill=1)
            
            # Draw label and count
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 10)
            c.drawString(self.margin, y_pos + 8, label)
            c.drawRightString(self.margin + 1.4*inch, y_pos + 8, str(count))
            
            y_pos -= 35
        
        # Section breakdown
        y_pos -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin, y_pos, "Top Sections with Issues:")
        y_pos -= 30
        
        # Find sections with deficient items
        sections = self.data_mapper.get_sections()
        section_issues = []
        
        for section in sections:
            issues = 0
            line_items = self.data_mapper.get_line_items_for_section(section)
            for item in line_items:
                if item.get('inspectionStatus') == 'D' or item.get('isDeficient'):
                    issues += 1
            if issues > 0:
                section_issues.append((section.get('name', 'Unknown'), issues))
        
        # Sort by issue count
        section_issues.sort(key=lambda x: x[1], reverse=True)
        
        c.setFont("Helvetica", 10)
        for i, (section_name, issue_count) in enumerate(section_issues[:8]):
            # Truncate long names
            display_name = section_name[:40] + "..." if len(section_name) > 40 else section_name
            c.drawString(self.margin + 0.2*inch, y_pos, f"• {display_name}")
            c.drawRightString(self.page_width - self.margin, y_pos, 
                            f"{issue_count} issue{'s' if issue_count != 1 else ''}")
            y_pos -= 20
            
            if y_pos < 2*inch:
                break
    
    def _create_deficiencies_page(self, c: canvas.Canvas):
        """Create deficiencies summary page"""
        c.setFont("Helvetica-Bold", 20)
        c.setFillColorRGB(0.8, 0, 0)
        c.drawString(self.margin, self.page_height - self.margin - 20, 
                    "⚠ Deficiencies & Issues")
        
        c.setFillColorRGB(0, 0, 0)
        y_pos = self.page_height - self.margin - 80
        
        # Find all deficient items
        deficient_items = []
        sections = self.data_mapper.get_sections()
        
        for section in sections:
            line_items = self.data_mapper.get_line_items_for_section(section)
            for item in line_items:
                if item.get('inspectionStatus') == 'D' or item.get('isDeficient'):
                    comments = self.data_mapper.get_comments_for_line_item(item)
                    comment_text = comments[0].get('text', '') if comments else 'No details provided'
                    
                    deficient_items.append({
                        'section': section.get('name', 'Unknown'),
                        'item': item.get('name', 'Unknown'),
                        'comment': comment_text
                    })
        
        if not deficient_items:
            c.setFont("Helvetica", 12)
            c.drawString(self.margin, y_pos, "No deficiencies found - Great!")
            return
        
        c.setFont("Helvetica", 10)
        c.drawString(self.margin, y_pos, 
                    f"Found {len(deficient_items)} deficient item(s):")
        y_pos -= 30
        
        for i, item in enumerate(deficient_items[:15], 1):  # Limit to first 15
            if y_pos < 1.5*inch:
                break
            
            # Section and item name
            c.setFont("Helvetica-Bold", 10)
            header = f"{i}. {item['section']}: {item['item']}"
            if len(header) > 70:
                header = header[:67] + "..."
            c.drawString(self.margin, y_pos, header)
            y_pos -= 15
            
            # Comment
            c.setFont("Helvetica", 9)
            comment = item['comment'][:120] + "..." if len(item['comment']) > 120 else item['comment']
            c.drawString(self.margin + 0.3*inch, y_pos, comment)
            y_pos -= 25
    
    def _create_photo_gallery(self, c: canvas.Canvas) -> int:
        """Create photo gallery pages"""
        photos, _ = self.data_mapper.get_all_media()
        
        if not photos:
            c.setFont("Helvetica-Bold", 20)
            c.drawString(self.margin, self.page_height - self.margin - 20, 
                        "Photo Gallery")
            c.setFont("Helvetica", 12)
            c.drawString(self.margin, self.page_height - self.margin - 60, 
                        "No photos available")
            c.showPage()
            return 1
        
        photos_per_page = 4
        page_count = 0
        
        for page_start in range(0, min(len(photos), 16), photos_per_page):  # Max 16 photos
            # Title
            c.setFont("Helvetica-Bold", 20)
            c.drawString(self.margin, self.page_height - self.margin - 20, 
                        "Photo Gallery")
            
            y_pos = self.page_height - self.margin - 80
            photos_on_page = 0
            
            for i in range(page_start, min(page_start + photos_per_page, len(photos))):
                photo = photos[i]
                url = photo.get('url', '')
                
                if not url:
                    continue
                
                try:
                    result = self.image_handler.process_image(url, max_width=300, max_height=150)
                    if result:
                        img, img_width, img_height = result
                        
                        # Check space
                        if y_pos - img_height - 60 < self.margin:
                            break
                        
                        # Save to temporary file for ReportLab
                        import tempfile
                        import os
                        temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                        os.close(temp_fd)
                        img.save(temp_path, format='JPEG', quality=85)
                        
                        # Draw image
                        x_pos = (self.page_width - img_width) / 2
                        c.drawImage(temp_path, x_pos, y_pos - img_height, 
                                  width=img_width, height=img_height, preserveAspectRatio=True)
                        
                        # Clean up temp file
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                        
                        # Caption
                        c.setFont("Helvetica", 8)
                        caption = f"{photo.get('section_name', '')}: {photo.get('line_item_name', '')}"
                        c.drawCentredString(self.page_width/2, y_pos - img_height - 15, caption)
                        
                        y_pos -= img_height + 40
                        photos_on_page += 1
                
                except Exception as e:
                    print(f"      ✗ Failed to add photo: {e}")
                    continue
            
            c.showPage()
            page_count += 1
        
        print(f"      Created {page_count} photo gallery page(s)")
        return page_count
    
    def _create_video_page(self, c: canvas.Canvas):
        """Create video links page"""
        _, videos = self.data_mapper.get_all_media()
        
        c.setFont("Helvetica-Bold", 20)
        c.drawString(self.margin, self.page_height - self.margin - 20, 
                    "Video Links")
        
        y_pos = self.page_height - self.margin - 80
        
        if not videos:
            c.setFont("Helvetica", 12)
            c.drawString(self.margin, y_pos, "No videos available")
            return
        
        c.setFont("Helvetica", 10)
        c.drawString(self.margin, y_pos, 
                    f"Click the links below to view {len(videos)} inspection video(s):")
        y_pos -= 30
        
        for i, video in enumerate(videos[:20], 1):  # Limit to 20 videos
            if y_pos < 1.5*inch:
                break
            
            url = video.get('url', '')
            if not url or not self.video_handler.validate_url(url):
                continue
            
            # Video title
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(0, 0, 0.8)
            title = f"{i}. {video.get('section_name', 'Video')}: {video.get('line_item_name', '')}"
            if len(title) > 60:
                title = title[:57] + "..."
            c.drawString(self.margin, y_pos, title)
            
            # Add clickable link
            c.linkURL(url, (self.margin, y_pos - 5, self.margin + 4*inch, y_pos + 12))
            
            y_pos -= 15
            
            # URL
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            display_url = url[:80] + "..." if len(url) > 80 else url
            c.drawString(self.margin + 0.2*inch, y_pos, display_url)
            
            c.setFillColorRGB(0, 0, 0)
            y_pos -= 25


def main():
    """Main entry point for bonus PDF generation"""
    import os
    
    json_path = 'inspection.json'
    output_path = 'bonus_pdf.pdf'
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return
    
    generator = BonusPDFGenerator(json_path)
    generator.generate_report(output_path)


if __name__ == '__main__':
    main()

