import sys
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

sys.path.append('../')
from utils.bbox_utils import measure_distance, get_center_of_bbox

@dataclass
class FreeThrowEvent:
    """Container for free throw event information"""
    frame_number: int
    shooter_player_id: int
    shooter_team: int
    free_throw_line_position: Tuple[float, float]
    confidence: float
    event_type: str  # 'free_throw_attempt' or 'free_throw_setup'

class FreeThrowDetector:
    """
    Detects free throw situations in basketball games by analyzing:
    1. Player positioning relative to free throw lines
    2. Ball possession at free throw line
    3. Player formation patterns typical of free throw situations
    """
    
    def __init__(self):
        """
        Initialize the FreeThrowDetector with detection parameters.
        
        Attributes:
            free_throw_line_tolerance (float): Distance tolerance for free throw line detection (in tactical view units)
            min_players_in_lane (int): Minimum number of players that should be in lane area for free throw
            max_players_at_line (int): Maximum number of players allowed at free throw line
            confidence_threshold (float): Minimum confidence for free throw detection
        """
        self.free_throw_line_tolerance = 16.0  # tactical view units
        self.min_players_in_lane = 2  # minimum players in lane area
        self.max_players_at_line = 1  # only shooter should be at line
        self.confidence_threshold = 0.4
        
        # Free throw line positions in tactical view (from tactical_view_converter)
        # Left free throw line: positions 8-9, Right free throw line: positions 15-16
        self.left_free_throw_line = (5.79, 7.59)  # (x, y) in tactical view
        self.right_free_throw_line = (22.21, 7.59)  # (x, y) in tactical view
        
        # Lane area boundaries for player formation analysis
        self.lane_left_boundary = 5.79
        self.lane_right_boundary = 22.21
        self.lane_top_boundary = 5.18
        self.lane_bottom_boundary = 10.0
    
    def is_player_at_free_throw_line(self, player_position: Tuple[float, float], 
                                   free_throw_line: Tuple[float, float]) -> bool:
        """
        Check if a player is positioned at the free throw line.
        
        Args:
            player_position (Tuple[float, float]): Player's (x, y) position in tactical view
            free_throw_line (Tuple[float, float]): Free throw line (x, y) position
            
        Returns:
            bool: True if player is within tolerance of free throw line
        """
        distance = measure_distance(player_position, free_throw_line)
        return distance <= self.free_throw_line_tolerance
    
    def is_player_in_lane_area(self, player_position: Tuple[float, float]) -> bool:
        """
        Check if a player is in the lane area (key area around the basket).
        
        Args:
            player_position (Tuple[float, float]): Player's (x, y) position in tactical view
            
        Returns:
            bool: True if player is in the lane area
        """
        x, y = player_position
        return (self.lane_left_boundary <= x <= self.lane_right_boundary and 
                self.lane_top_boundary <= y <= self.lane_bottom_boundary)
    
    def analyze_player_formation(self, tactical_positions: Dict[int, Tuple[float, float]], 
                               shooter_team: int) -> Dict:
        """
        Analyze the player formation to determine if it matches a free throw situation.
        
        Args:
            tactical_positions (Dict[int, Tuple[float, float]]): Player positions in tactical view
            shooter_team (int): Team ID of the potential shooter
            
        Returns:
            Dict: Formation analysis results
        """
        players_at_left_line = []
        players_at_right_line = []
        players_in_lane = []
        other_players = []
        
        for player_id, position in tactical_positions.items():
            if self.is_player_at_free_throw_line(position, self.left_free_throw_line):
                players_at_left_line.append(player_id)
            elif self.is_player_at_free_throw_line(position, self.right_free_throw_line):
                players_at_right_line.append(player_id)
            elif self.is_player_in_lane_area(position):
                players_in_lane.append(player_id)
            else:
                other_players.append(player_id)
        
        return {
            'players_at_left_line': players_at_left_line,
            'players_at_right_line': players_at_right_line,
            'players_in_lane': players_in_lane,
            'other_players': other_players,
            'total_players_in_lane': len(players_in_lane)
        }
    
    def calculate_free_throw_confidence(self, formation_analysis: Dict, 
                                      ball_possession: int, shooter_team: int) -> float:
        """
        Calculate confidence score for free throw detection based on multiple factors.
        
        Args:
            formation_analysis (Dict): Results from analyze_player_formation
            ball_possession (int): Player ID who has the ball (-1 if no possession)
            shooter_team (int): Team ID of the potential shooter
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # Factor 1: Only one player at free throw line (40% weight)
        total_at_lines = len(formation_analysis['players_at_left_line']) + len(formation_analysis['players_at_right_line'])
        if total_at_lines == 1:
            confidence += 0.4
        elif total_at_lines == 0:
            confidence += 0.0
        else:
            confidence += max(0.0, 0.4 - (total_at_lines - 1) * 0.2)
        
        # Factor 2: Sufficient players in lane area (30% weight)
        players_in_lane = formation_analysis['total_players_in_lane']
        if players_in_lane >= self.min_players_in_lane:
            confidence += 0.3
        else:
            confidence += (players_in_lane / self.min_players_in_lane) * 0.3
        
        # Factor 3: Ball possession by player at free throw line (30% weight)
        if ball_possession != -1:
            all_players_at_lines = (formation_analysis['players_at_left_line'] + 
                                  formation_analysis['players_at_right_line'])
            if ball_possession in all_players_at_lines:
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def detect_free_throws(self, tactical_positions: List[Dict[int, Tuple[float, float]]], 
                          ball_possession: List[int], 
                          player_assignment: List[Dict[int, int]]) -> List[FreeThrowEvent]:
        """
        Detect free throw situations across all frames.
        
        Args:
            tactical_positions (List[Dict[int, Tuple[float, float]]]): Player positions for each frame
            ball_possession (List[int]): Ball possession for each frame
            player_assignment (List[Dict[int, int]]): Team assignments for each frame
            
        Returns:
            List[FreeThrowEvent]: List of detected free throw events
        """
        free_throw_events = []
        
        for frame_num in range(len(tactical_positions)):
            frame_positions = tactical_positions[frame_num]
            frame_ball_possession = ball_possession[frame_num] if frame_num < len(ball_possession) else -1
            frame_assignments = player_assignment[frame_num] if frame_num < len(player_assignment) else {}
            
            # Skip frames with insufficient data
            if not frame_positions or frame_ball_possession == -1:
                continue
            
            # Analyze player formation
            formation_analysis = self.analyze_player_formation(frame_positions, 0)
            
            # Check both free throw lines
            for line_name, line_position in [("left", self.left_free_throw_line), 
                                           ("right", self.right_free_throw_line)]:
                
                players_at_line = (formation_analysis['players_at_left_line'] if line_name == "left" 
                                 else formation_analysis['players_at_right_line'])
                
                if len(players_at_line) == 1:
                    shooter_id = players_at_line[0]
                    shooter_team = frame_assignments.get(shooter_id, -1)
                    
                    if shooter_team != -1:
                        # Calculate confidence
                        confidence = self.calculate_free_throw_confidence(
                            formation_analysis, frame_ball_possession, shooter_team
                        )
                        
                        # Create event if confidence is above threshold
                        if confidence >= self.confidence_threshold:
                            event = FreeThrowEvent(
                                frame_number=frame_num,
                                shooter_player_id=shooter_id,
                                shooter_team=shooter_team,
                                free_throw_line_position=line_position,
                                confidence=confidence,
                                event_type='free_throw_attempt'
                            )
                            free_throw_events.append(event)
        
        return free_throw_events
    
    def get_free_throw_summary(self, events: List[FreeThrowEvent]) -> Dict:
        """
        Generate a summary of detected free throw events.
        
        Args:
            events (List[FreeThrowEvent]): List of free throw events
            
        Returns:
            Dict: Summary statistics
        """
        if not events:
            return {
                'total_free_throws': 0,
                'team1_free_throws': 0,
                'team2_free_throws': 0,
                'average_confidence': 0.0,
                'frames_with_free_throws': []
            }
        
        team1_count = sum(1 for event in events if event.shooter_team == 1)
        team2_count = sum(1 for event in events if event.shooter_team == 2)
        avg_confidence = sum(event.confidence for event in events) / len(events)
        frames = [event.frame_number for event in events]
        
        return {
            'total_free_throws': len(events),
            'team1_free_throws': team1_count,
            'team2_free_throws': team2_count,
            'average_confidence': avg_confidence,
            'frames_with_free_throws': frames
        }

