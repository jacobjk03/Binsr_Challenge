"""
Data mapper for TREC inspection report
Maps inspection.json data to TREC template fields
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class DataMapper:
    """Maps inspection data to TREC template fields"""
    
    STATUS_MAP = {
        'I': 'Inspected',
        'NI': 'Not Inspected',
        'NP': 'Not Present',
        'D': 'Deficient'
    }
    
    def __init__(self, json_path: str):
        """Load and parse inspection JSON"""
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        self.inspection = self.data.get('inspection', {})
        self.account = self.data.get('account', {})
    
    def get_field_value(self, field_path: List[str], default: str = "Data not found in test data") -> str:
        """Get a field value from nested JSON, return default if not found"""
        obj = self.inspection
        for key in field_path:
            if isinstance(obj, dict):
                obj = obj.get(key)
                if obj is None:
                    return default
            else:
                return default
        return str(obj) if obj is not None and obj != "" else default
    
    def format_timestamp(self, timestamp: Optional[int]) -> str:
        """Convert Unix timestamp (milliseconds) to readable date"""
        if not timestamp or timestamp == 0:
            return "Data not found in test data"
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime("%m/%d/%Y")
        except:
            return "Data not found in test data"
    
    def get_header_fields(self) -> Dict[str, str]:
        """Extract header/metadata fields"""
        client_info = self.inspection.get('clientInfo', {})
        inspector = self.inspection.get('inspector', {})
        address = self.inspection.get('address', {})
        schedule = self.inspection.get('schedule', {})
        
        fields = {
            'Name of Client': client_info.get('name', 'Data not found in test data'),
            'Date of Inspection': self.format_timestamp(schedule.get('date')),
            'Address of Inspected Property': address.get('fullAddress', 'Data not found in test data'),
            'Name of Inspector': inspector.get('name', 'Data not found in test data'),
            'TREC License': 'Data not found in test data',  # Not in JSON
            'Name of Sponsor if applicable': 'Data not found in test data',  # Not in JSON
            'TREC License_2': 'Data not found in test data',  # Not in JSON
        }
        
        return fields
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """Get all sections with line items"""
        sections = self.inspection.get('sections', [])
        # Sort by order field
        sorted_sections = sorted(sections, key=lambda x: x.get('order', 0))
        return sorted_sections
    
    def get_line_items_for_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all line items for a section, sorted by order"""
        line_items = section.get('lineItems', [])
        sorted_items = sorted(line_items, key=lambda x: x.get('order', 0))
        return sorted_items
    
    def get_comments_for_line_item(self, line_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all comments for a line item"""
        comments = line_item.get('comments', [])
        sorted_comments = sorted(comments, key=lambda x: x.get('order', 0))
        return sorted_comments
    
    def get_photos_for_comment(self, comment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get all photos for a comment"""
        return comment.get('photos', [])
    
    def get_videos_for_comment(self, comment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get all videos for a comment"""
        return comment.get('videos', [])
    
    def get_status_label(self, status_code: Optional[str]) -> str:
        """Convert status code to readable label"""
        if not status_code:
            return "Data not found in test data"
        return self.STATUS_MAP.get(status_code, status_code)
    
    def get_checkbox_states(self, status_code: Optional[str]) -> Dict[str, bool]:
        """
        Determine which checkbox should be checked based on status
        Returns dict with keys: I, NI, NP, D
        """
        states = {
            'I': False,
            'NI': False,
            'NP': False,
            'D': False
        }
        
        if status_code and status_code in states:
            states[status_code] = True
        elif status_code is None:
            # If no status, randomly select one (as per requirements)
            # For consistency, let's default to 'I' (Inspected)
            states['I'] = True
        
        return states
    
    def get_all_media(self) -> tuple[List[Dict], List[Dict]]:
        """Get all photos and videos from all comments"""
        all_photos = []
        all_videos = []
        
        sections = self.get_sections()
        for section in sections:
            line_items = self.get_line_items_for_section(section)
            for line_item in line_items:
                comments = self.get_comments_for_line_item(line_item)
                for comment in comments:
                    photos = self.get_photos_for_comment(comment)
                    videos = self.get_videos_for_comment(comment)
                    
                    for photo in photos:
                        photo_with_context = photo.copy()
                        photo_with_context['section_name'] = section.get('name', 'Unknown')
                        photo_with_context['line_item_name'] = line_item.get('name', 'Unknown')
                        photo_with_context['comment_text'] = comment.get('text', '')[:100]
                        all_photos.append(photo_with_context)
                    
                    for video in videos:
                        video_with_context = video.copy()
                        video_with_context['section_name'] = section.get('name', 'Unknown')
                        video_with_context['line_item_name'] = line_item.get('name', 'Unknown')
                        video_with_context['comment_text'] = comment.get('text', '')[:100]
                        all_videos.append(video_with_context)
        
        return all_photos, all_videos
    
    def get_property_info(self) -> Dict[str, str]:
        """Get property information"""
        address = self.inspection.get('address', {})
        property_info = address.get('propertyInfo', {})
        
        return {
            'street': address.get('street', 'Data not found in test data'),
            'city': address.get('city', 'Data not found in test data'),
            'state': address.get('state', 'Data not found in test data'),
            'zipcode': address.get('zipcode', 'Data not found in test data'),
            'square_footage': str(property_info.get('squareFootage', 'Data not found in test data'))
        }
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics"""
        sections = self.get_sections()
        stats = {
            'total_sections': len(sections),
            'total_line_items': 0,
            'inspected': 0,
            'not_inspected': 0,
            'not_present': 0,
            'deficient': 0,
            'total_photos': 0,
            'total_videos': 0
        }
        
        for section in sections:
            line_items = self.get_line_items_for_section(section)
            stats['total_line_items'] += len(line_items)
            
            for line_item in line_items:
                status = line_item.get('inspectionStatus')
                if status == 'I':
                    stats['inspected'] += 1
                elif status == 'NI':
                    stats['not_inspected'] += 1
                elif status == 'NP':
                    stats['not_present'] += 1
                elif status == 'D':
                    stats['deficient'] += 1
                
                comments = self.get_comments_for_line_item(line_item)
                for comment in comments:
                    stats['total_photos'] += len(self.get_photos_for_comment(comment))
                    stats['total_videos'] += len(self.get_videos_for_comment(comment))
        
        return stats


if __name__ == '__main__':
    # Test the mapper
    mapper = DataMapper('inspection.json')
    
    print("=== HEADER FIELDS ===")
    header_fields = mapper.get_header_fields()
    for key, value in header_fields.items():
        print(f"{key}: {value}")
    
    print("\n=== SUMMARY STATS ===")
    stats = mapper.get_summary_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== SECTIONS ===")
    sections = mapper.get_sections()
    for section in sections[:3]:
        print(f"\nSection: {section.get('name')}")
        line_items = mapper.get_line_items_for_section(section)
        print(f"  Line items: {len(line_items)}")
        for item in line_items[:2]:
            print(f"    - {item.get('name')}: {mapper.get_status_label(item.get('inspectionStatus'))}")
            checkbox_states = mapper.get_checkbox_states(item.get('inspectionStatus'))
            print(f"      Checkboxes: {checkbox_states}")

