"""
Video handler for TREC inspection report
Handles video URLs and creates clickable links in PDFs
"""

from typing import List, Dict, Any


class VideoHandler:
    """Handles video URLs and link generation"""
    
    def __init__(self):
        """Initialize video handler"""
        pass
    
    def format_video_url(self, url: str) -> str:
        """
        Format video URL for display
        
        Args:
            url: Video URL
            
        Returns:
            Formatted URL string
        """
        if not url:
            return "No video URL available"
        
        # Truncate very long URLs for display
        if len(url) > 80:
            return url[:77] + "..."
        return url
    
    def create_video_link_text(self, video_data: Dict[str, Any], index: int = 1) -> str:
        """
        Create descriptive text for video link
        
        Args:
            video_data: Video data dictionary
            index: Video number/index
            
        Returns:
            Link text string
        """
        url = video_data.get('url', '')
        description = video_data.get('description') or video_data.get('caption')
        
        if description:
            return f"Video {index}: {description}"
        else:
            return f"Video {index}"
    
    def extract_videos_from_comment(self, comment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all videos from a comment
        
        Args:
            comment: Comment dictionary
            
        Returns:
            List of video dictionaries
        """
        return comment.get('videos', [])
    
    def get_video_url(self, video_data: Dict[str, Any]) -> str:
        """
        Extract URL from video data
        
        Args:
            video_data: Video data dictionary
            
        Returns:
            Video URL string
        """
        return video_data.get('url', '')
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is well-formed
        
        Args:
            url: URL string
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        
        # Basic URL validation
        return url.startswith(('http://', 'https://'))
    
    def get_video_metadata(self, video_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract metadata from video data
        
        Args:
            video_data: Video data dictionary
            
        Returns:
            Dictionary with metadata
        """
        return {
            'url': video_data.get('url', ''),
            'description': video_data.get('description') or video_data.get('caption', ''),
            'timestamp': str(video_data.get('timestamp', '')),
            'fileName': video_data.get('fileName', ''),
            'fileType': video_data.get('fileType', ''),
        }
    
    def format_video_section(self, videos: List[Dict[str, Any]], 
                           section_name: str = '', 
                           item_name: str = '') -> List[str]:
        """
        Format videos for display in a section
        
        Args:
            videos: List of video dictionaries
            section_name: Name of the section
            item_name: Name of the line item
            
        Returns:
            List of formatted strings
        """
        if not videos:
            return []
        
        formatted = []
        
        if section_name and item_name:
            formatted.append(f"Videos for {section_name} - {item_name}:")
        
        for i, video in enumerate(videos, 1):
            url = self.get_video_url(video)
            if url and self.validate_url(url):
                link_text = self.create_video_link_text(video, i)
                formatted.append(f"  {link_text}")
                formatted.append(f"  URL: {url}")
            else:
                formatted.append(f"  Video {i}: Invalid or missing URL")
        
        return formatted
    
    def count_videos(self, videos: List[Dict[str, Any]]) -> int:
        """Count valid videos"""
        return sum(1 for v in videos if self.validate_url(self.get_video_url(v)))


if __name__ == '__main__':
    # Test the video handler
    handler = VideoHandler()
    
    # Test data
    test_videos = [
        {
            'url': 'https://example.com/video1.mp4',
            'description': 'Roof damage video',
            'timestamp': 1234567890
        },
        {
            'url': 'https://example.com/video2.mp4',
            'caption': 'Foundation issues',
        },
        {
            'url': 'invalid_url',
        }
    ]
    
    print("=== VIDEO HANDLER TEST ===")
    print(f"Total videos: {len(test_videos)}")
    print(f"Valid videos: {handler.count_videos(test_videos)}")
    
    for i, video in enumerate(test_videos, 1):
        print(f"\nVideo {i}:")
        print(f"  URL: {handler.get_video_url(video)}")
        print(f"  Valid: {handler.validate_url(handler.get_video_url(video))}")
        print(f"  Link text: {handler.create_video_link_text(video, i)}")
        print(f"  Metadata: {handler.get_video_metadata(video)}")
    
    print("\n=== FORMATTED SECTION ===")
    formatted = handler.format_video_section(test_videos, "Roofing", "Roof Condition")
    for line in formatted:
        print(line)

