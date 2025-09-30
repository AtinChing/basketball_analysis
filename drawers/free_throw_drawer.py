import cv2
import numpy as np
from typing import List, Dict, Tuple
from copy import deepcopy

class FreeThrowDrawer:
    """
    Draws free throw detection visualizations on video frames.
    """
    
    def __init__(self):
        """
        Initialize the FreeThrowDrawer with drawing parameters.
        """
        # Colors for different elements (BGR format)
        self.free_throw_line_color = (0, 255, 255)  # Yellow
        self.shooter_highlight_color = (0, 255, 0)  # Green
        self.confidence_text_color = (255, 255, 255)  # White
        self.background_color = (0, 0, 0)  # Black
        
        # Drawing parameters
        self.line_thickness = 3
        self.circle_radius = 8
        self.text_thickness = 2
        self.font_scale = 0.7
        self.font = cv2.FONT_HERSHEY_SIMPLEX
    
    def draw_free_throw_line_markers(self, frame: np.ndarray, 
                                   tactical_positions: Dict[int, Tuple[float, float]],
                                   tactical_view_converter) -> np.ndarray:
        """
        Draw markers at free throw line positions on the frame.
        
        Args:
            frame (np.ndarray): Video frame to draw on
            tactical_positions (Dict[int, Tuple[float, float]]): Player positions in tactical view
            tactical_view_converter: TacticalViewConverter instance for coordinate transformation
            
        Returns:
            np.ndarray: Frame with free throw line markers drawn
        """
        frame_copy = deepcopy(frame)
        
        # Get free throw line positions in tactical view
        left_ft_line = (5.79, 7.59)
        right_ft_line = (22.21, 7.59)
        
        # Convert tactical view positions back to frame coordinates
        # This is a simplified approach - in practice you'd need inverse homography
        for ft_line_pos in [left_ft_line, right_ft_line]:
            # For visualization, we'll draw a circle at an approximate position
            # In a full implementation, you'd transform back from tactical view to frame coordinates
            x_offset = 100 if ft_line_pos[0] < 15 else 500  # Approximate positioning
            y_offset = 300  # Approximate positioning
            
            cv2.circle(frame_copy, (x_offset, y_offset), self.circle_radius, 
                      self.free_throw_line_color, -1)
            cv2.putText(frame_copy, "FT Line", (x_offset + 15, y_offset), 
                       self.font, self.font_scale, self.free_throw_line_color, self.text_thickness)
        
        return frame_copy
    
    def draw_free_throw_detection(self, frame: np.ndarray, 
                                free_throw_events: List, 
                                frame_number: int,
                                tactical_positions: Dict[int, Tuple[float, float]],
                                player_assignment: Dict[int, int]) -> np.ndarray:
        """
        Draw free throw detection information on the frame.
        
        Args:
            frame (np.ndarray): Video frame to draw on
            free_throw_events (List): List of FreeThrowEvent objects
            frame_number (int): Current frame number
            tactical_positions (Dict[int, Tuple[float, float]]): Player positions in tactical view
            player_assignment (Dict[int, int]): Team assignments for players
            
        Returns:
            np.ndarray: Frame with free throw detection drawn
        """
        frame_copy = deepcopy(frame)
        
        # Check if current frame has a free throw event
        current_frame_events = [event for event in free_throw_events if event.frame_number == frame_number]
        
        if current_frame_events:
            for event in current_frame_events:
                # Draw shooter highlight
                if event.shooter_player_id in tactical_positions:
                    # For visualization, we'll use a simplified approach
                    # In practice, you'd transform tactical position back to frame coordinates
                    shooter_pos = tactical_positions[event.shooter_player_id]
                    
                    # Approximate frame position (this would be improved with proper coordinate transformation)
                    frame_x = int(shooter_pos[0] * 20)  # Scale factor
                    frame_y = int(shooter_pos[1] * 20)  # Scale factor
                    
                    # Draw circle around shooter
                    cv2.circle(frame_copy, (frame_x, frame_y), self.circle_radius * 2, 
                              self.shooter_highlight_color, self.line_thickness)
                    
                    # Draw confidence text
                    confidence_text = f"FT: {event.confidence:.2f}"
                    cv2.putText(frame_copy, confidence_text, (frame_x + 20, frame_y - 10), 
                               self.font, self.font_scale, self.confidence_text_color, self.text_thickness)
                    
                    # Draw team information
                    team_text = f"Team {event.shooter_team}"
                    cv2.putText(frame_copy, team_text, (frame_x + 20, frame_y + 10), 
                               self.font, self.font_scale, self.confidence_text_color, self.text_thickness)
        
        return frame_copy
    
    def draw_free_throw_summary(self, frame: np.ndarray, 
                              free_throw_summary: Dict) -> np.ndarray:
        """
        Draw free throw summary statistics on the frame.
        
        Args:
            frame (np.ndarray): Video frame to draw on
            free_throw_summary (Dict): Summary statistics from FreeThrowDetector
            
        Returns:
            np.ndarray: Frame with summary drawn
        """
        frame_copy = deepcopy(frame)
        
        # Position for summary text (top-left corner)
        start_x, start_y = 20, 30
        line_height = 25
        
        # Draw background rectangle
        text_lines = [
            f"Free Throws Detected: {free_throw_summary['total_free_throws']}",
            f"Team 1: {free_throw_summary['team1_free_throws']}",
            f"Team 2: {free_throw_summary['team2_free_throws']}",
            f"Avg Confidence: {free_throw_summary['average_confidence']:.2f}"
        ]
        
        # Calculate background rectangle size
        max_text_width = max(cv2.getTextSize(line, self.font, self.font_scale, self.text_thickness)[0][0] 
                           for line in text_lines)
        bg_height = len(text_lines) * line_height + 10
        bg_width = max_text_width + 20
        
        # Draw background
        cv2.rectangle(frame_copy, (start_x - 5, start_y - 20), 
                     (start_x + bg_width, start_y + bg_height), 
                     self.background_color, -1)
        cv2.rectangle(frame_copy, (start_x - 5, start_y - 20), 
                     (start_x + bg_width, start_y + bg_height), 
                     self.free_throw_line_color, 2)
        
        # Draw text lines
        for i, line in enumerate(text_lines):
            y_pos = start_y + (i * line_height)
            cv2.putText(frame_copy, line, (start_x, y_pos), 
                       self.font, self.font_scale, self.confidence_text_color, self.text_thickness)
        
        return frame_copy
    
    def draw(self, video_frames: List[np.ndarray], 
             free_throw_events: List,
             tactical_positions: List[Dict[int, Tuple[float, float]]],
             player_assignment: List[Dict[int, int]],
             tactical_view_converter=None,
             show_summary: bool = True) -> List[np.ndarray]:
        """
        Draw free throw detections on all video frames.
        
        Args:
            video_frames (List[np.ndarray]): List of video frames
            free_throw_events (List): List of FreeThrowEvent objects
            tactical_positions (List[Dict[int, Tuple[float, float]]]): Player positions for each frame
            player_assignment (List[Dict[int, int]]): Team assignments for each frame
            tactical_view_converter: TacticalViewConverter instance (optional)
            show_summary (bool): Whether to show summary statistics
            
        Returns:
            List[np.ndarray]: List of frames with free throw detections drawn
        """
        output_frames = []
        
        for frame_num, frame in enumerate(video_frames):
            frame_copy = deepcopy(frame)
            
            # Draw free throw line markers if converter is available
            if tactical_view_converter and frame_num < len(tactical_positions):
                frame_copy = self.draw_free_throw_line_markers(
                    frame_copy, tactical_positions[frame_num], tactical_view_converter
                )
            
            # Draw free throw detection for current frame
            if frame_num < len(tactical_positions) and frame_num < len(player_assignment):
                frame_copy = self.draw_free_throw_detection(
                    frame_copy, free_throw_events, frame_num, 
                    tactical_positions[frame_num], player_assignment[frame_num]
                )
            
            # Draw summary on first frame
            if show_summary and frame_num == 0 and free_throw_events:
                from free_throw_detector.free_throw_detector import FreeThrowDetector
                detector = FreeThrowDetector()
                summary = detector.get_free_throw_summary(free_throw_events)
                frame_copy = self.draw_free_throw_summary(frame_copy, summary)
            
            output_frames.append(frame_copy)
        
        return output_frames

