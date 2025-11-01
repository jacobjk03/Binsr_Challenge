"""
TREC Field Mapper - Maps inspection data to TREC form fields
Handles checkbox filling for inspection status (I, NI, NP, D)
"""

import fitz
from typing import Dict, List, Tuple


class TRECFieldMapper:
    """Maps inspection data to TREC PDF form fields"""
    
    # Status to checkbox position mapping
    # In TREC forms, checkboxes typically appear in groups of 4: I, NI, NP, D
    STATUS_TO_CHECKBOX_INDEX = {
        'I': 0,   # Inspected
        'NI': 1,  # Not Inspected
        'NP': 2,  # Not Present
        'D': 3    # Deficient
    }
    
    def __init__(self, template_path: str):
        """Initialize with TREC template"""
        self.template_path = template_path
        self.field_info = self._analyze_fields()
    
    def _analyze_fields(self) -> Dict:
        """Analyze all form fields in the template"""
        doc = fitz.open(self.template_path)
        
        fields = {
            'checkboxes': [],
            'text_fields': [],
            'by_page': {}
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_checkboxes = []
            page_text = []
            
            for widget in page.widgets():
                field_info = {
                    'name': widget.field_name,
                    'type': widget.field_type,
                    'page': page_num
                }
                
                if widget.field_type == 2:  # Checkbox
                    fields['checkboxes'].append(field_info)
                    page_checkboxes.append(field_info)
                elif widget.field_type == 7:  # Text
                    fields['text_fields'].append(field_info)
                    page_text.append(field_info)
            
            fields['by_page'][page_num] = {
                'checkboxes': page_checkboxes,
                'text_fields': page_text
            }
        
        doc.close()
        return fields
    
    def get_checkbox_groups(self, page_num: int) -> List[List[str]]:
        """
        Get checkbox field names grouped by line item
        Each group has 4 checkboxes: [I, NI, NP, D]
        """
        if page_num not in self.field_info['by_page']:
            return []
        
        checkboxes = self.field_info['by_page'][page_num]['checkboxes']
        checkbox_names = [cb['name'] for cb in checkboxes]
        
        # Group checkboxes in sets of 4
        groups = []
        for i in range(0, len(checkbox_names), 4):
            group = checkbox_names[i:i+4]
            if len(group) == 4:
                groups.append(group)
        
        return groups
    
    def fill_checkbox_for_status(self, doc: fitz.Document, checkbox_group: List[str], 
                                 status: str) -> int:
        """
        Fill checkbox in a group based on status
        
        Args:
            doc: PyMuPDF document
            checkbox_group: List of 4 checkbox field names [I, NI, NP, D]
            status: Status code ('I', 'NI', 'NP', 'D')
        
        Returns:
            Number of checkboxes filled (0 or 1)
        """
        if not status or status not in self.STATUS_TO_CHECKBOX_INDEX:
            # Default to 'I' (Inspected) if no status
            status = 'I'
        
        # Get the index of the checkbox to fill
        checkbox_idx = self.STATUS_TO_CHECKBOX_INDEX[status]
        
        if checkbox_idx >= len(checkbox_group):
            return 0
        
        checkbox_name = checkbox_group[checkbox_idx]
        
        # Find and fill the checkbox
        for page in doc:
            for widget in page.widgets():
                if widget.field_name == checkbox_name:
                    try:
                        widget.field_value = True
                        widget.update()
                        return 1
                    except Exception as e:
                        print(f"      ⚠ Failed to check {checkbox_name}: {e}")
                        return 0
        
        return 0
    
    def fill_text_field(self, doc: fitz.Document, field_name: str, value: str) -> bool:
        """Fill a text field in the document"""
        for page in doc:
            for widget in page.widgets():
                if widget.field_name == field_name and widget.field_type == 7:
                    try:
                        widget.field_value = str(value)
                        widget.update()
                        return True
                    except Exception as e:
                        print(f"      ⚠ Failed to fill {field_name}: {e}")
                        return False
        return False
    
    def get_text_fields_for_page(self, page_num: int) -> List[str]:
        """Get all text field names for a page"""
        if page_num not in self.field_info['by_page']:
            return []
        return [tf['name'] for tf in self.field_info['by_page'][page_num]['text_fields']]
    
    def get_checkbox_count_for_page(self, page_num: int) -> int:
        """Get number of checkboxes on a page"""
        if page_num not in self.field_info['by_page']:
            return 0
        return len(self.field_info['by_page'][page_num]['checkboxes'])
    
    def fill_line_items_on_page(self, doc: fitz.Document, page_num: int, 
                               line_items: List[Dict], start_idx: int = 0) -> Tuple[int, int]:
        """
        Fill line items on a specific page
        
        Args:
            doc: PyMuPDF document
            page_num: Page number (0-indexed)
            line_items: List of line item dictionaries with 'inspectionStatus' and 'name'
            start_idx: Starting index in line_items list
        
        Returns:
            Tuple of (checkboxes_filled, items_processed)
        """
        checkbox_groups = self.get_checkbox_groups(page_num)
        text_fields = self.get_text_fields_for_page(page_num)
        
        checkboxes_filled = 0
        items_processed = 0
        
        # Fill checkboxes for each line item
        for i, checkbox_group in enumerate(checkbox_groups):
            item_idx = start_idx + i
            if item_idx >= len(line_items):
                break
            
            line_item = line_items[item_idx]
            status = line_item.get('inspectionStatus', 'I')
            
            filled = self.fill_checkbox_for_status(doc, checkbox_group, status)
            checkboxes_filled += filled
            items_processed += 1
            
            # Try to fill associated text field if available
            if i < len(text_fields):
                text_field_name = text_fields[i]
                # Fill with line item name or first comment
                comments = line_item.get('comments', [])
                if comments and comments[0].get('text'):
                    comment_text = comments[0]['text'][:200]  # Limit length
                    self.fill_text_field(doc, text_field_name, comment_text)
        
        return checkboxes_filled, items_processed


if __name__ == '__main__':
    # Test the field mapper
    mapper = TRECFieldMapper('TREC_Template_Blank.pdf')
    
    print("=== TREC FIELD MAPPER TEST ===\n")
    print(f"Total checkboxes: {len(mapper.field_info['checkboxes'])}")
    print(f"Total text fields: {len(mapper.field_info['text_fields'])}")
    
    print("\nCheckbox groups by page:")
    for page_num in range(2, 6):  # Pages 3-6
        groups = mapper.get_checkbox_groups(page_num)
        print(f"  Page {page_num + 1}: {len(groups)} line items ({len(groups) * 4} checkboxes)")
    
    print("\n✅ Field mapper initialized successfully!")

