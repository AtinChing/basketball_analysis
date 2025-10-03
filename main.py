import os
import argparse
from utils import read_video, save_video
from trackers import PlayerTracker, BallTracker
from team_assigner import TeamAssigner
from court_keypoint_detector import CourtKeypointDetector
from ball_aquisition import BallAquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from tactical_view_converter import TacticalViewConverter
from speed_and_distance_calculator import SpeedAndDistanceCalculator
from basketball_statistics_calculator import print_four_factors_summary
from free_throw_detector import FreeThrowDetector
from drawers import (
    PlayerTracksDrawer, 
    BallTracksDrawer,
    CourtKeypointDrawer,
    TeamBallControlDrawer,
    FrameNumberDrawer,
    PassInterceptionDrawer,
    TacticalViewDrawer,
    SpeedAndDistanceDrawer,
    FreeThrowDrawer
)
from configs import(
    STUBS_DEFAULT_PATH,
    PLAYER_DETECTOR_PATH,
    BALL_DETECTOR_PATH,
    COURT_KEYPOINT_DETECTOR_PATH,
    OUTPUT_VIDEO_PATH
)

def parse_args():
    parser = argparse.ArgumentParser(description='Basketball Video Analysis')
    parser.add_argument('input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_video', type=str, default=OUTPUT_VIDEO_PATH, 
                        help='Path to output video file')
    parser.add_argument('--stub_path', type=str, default=STUBS_DEFAULT_PATH,
                        help='Path to stub directory')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Read Video
    video_frames = read_video(args.input_video)
    
    ## Initialize Tracker
    player_tracker = PlayerTracker(PLAYER_DETECTOR_PATH)
    ball_tracker = BallTracker(BALL_DETECTOR_PATH)

    ## Initialize Keypoint Detector
    court_keypoint_detector = CourtKeypointDetector(COURT_KEYPOINT_DETECTOR_PATH)

    # Run Detectors
    player_tracks = player_tracker.get_object_tracks(video_frames,
                                       read_from_stub=False,
                                       stub_path=os.path.join(args.stub_path, 'player_track_stubs.pkl')
                                      )
    
    ball_tracks = ball_tracker.get_object_tracks(video_frames,
                                                 read_from_stub=False,
                                                 stub_path=os.path.join(args.stub_path, 'ball_track_stubs.pkl')
                                                )
    ## Run KeyPoint Extractor
    court_keypoints_per_frame = court_keypoint_detector.get_court_keypoints(video_frames,
                                                                    read_from_stub=False,
                                                                    stub_path=os.path.join(args.stub_path, 'court_key_points_stub.pkl')
                                                                    )

    # Remove Wrong Ball Detections
    ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
    # Interpolate Ball Tracks
    ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)
   

    # Assign Player Teams
    team_assigner = TeamAssigner()
    player_assignment = team_assigner.get_player_teams_across_frames(video_frames,
                                                                    player_tracks,
                                                                    read_from_stub=False,
                                                                    stub_path=os.path.join(args.stub_path, 'player_assignment_stub.pkl')
                                                                    )

    # Ball Acquisition
    ball_aquisition_detector = BallAquisitionDetector()
    ball_aquisition = ball_aquisition_detector.detect_ball_possession(player_tracks,ball_tracks)

    # Detect Passes
    pass_and_interception_detector = PassAndInterceptionDetector()
    passes = pass_and_interception_detector.detect_passes(ball_aquisition,player_assignment)
    interceptions = pass_and_interception_detector.detect_interceptions(ball_aquisition,player_assignment)

    # Tactical View
    tactical_view_converter = TacticalViewConverter(
        court_image_path="./images/basketball_court.png"
    )

    court_keypoints_per_frame = tactical_view_converter.validate_keypoints(court_keypoints_per_frame)
    tactical_player_positions = tactical_view_converter.transform_players_to_tactical_view(court_keypoints_per_frame,player_tracks)

    # Speed and Distance Calculator
    speed_and_distance_calculator = SpeedAndDistanceCalculator(
        tactical_view_converter.width,
        tactical_view_converter.height,
        tactical_view_converter.actual_width_in_meters,
        tactical_view_converter.actual_height_in_meters
    )
    player_distances_per_frame = speed_and_distance_calculator.calculate_distance(tactical_player_positions)
    player_speed_per_frame = speed_and_distance_calculator.calculate_speed(player_distances_per_frame)

    # Free Throw Detection
    free_throw_detector = FreeThrowDetector()
    free_throw_events = free_throw_detector.detect_free_throws(
        tactical_player_positions, 
        ball_aquisition, 
        player_assignment
    )
    
    # Print free throw detection summary
    if free_throw_events:
        summary = free_throw_detector.get_free_throw_summary(free_throw_events)
        print(f"Free Throw Detection Summary:")
        print(f"  Total Free Throws Detected: {summary['total_free_throws']}")
        print(f"  Team 1 Free Throws: {summary['team1_free_throws']}")
        print(f"  Team 2 Free Throws: {summary['team2_free_throws']}")
        print(f"  Average Confidence: {summary['average_confidence']:.2f}")
        print(f"  Frames with Free Throws: {summary['frames_with_free_throws']}")
    else:
        # Provide a detailed diagnostic summary of how close frames were to detection
        max_confidence = 0.0
        max_conf_frame = -1
        best_formation = None
        best_ball_at_line = False

        frames_with_one_at_line = 0
        frames_with_sufficient_lane = 0
        frames_with_ball_holder_at_line = 0
        frames_meeting_all_three = 0

        blockers_counts = {
            'line_presence': 0,              # not exactly one player at a line
            'lane_occupancy': 0,             # insufficient players in lane
            'possession_alignment': 0        # ball holder not at line
        }

        for frame_num, frame_positions in enumerate(tactical_player_positions):
            if not frame_positions:
                continue

            frame_ball_possession = ball_aquisition[frame_num] if frame_num < len(ball_aquisition) else -1
            formation = free_throw_detector.analyze_player_formation(frame_positions, 0)

            total_at_lines = len(formation['players_at_left_line']) + len(formation['players_at_right_line'])
            players_in_lane = formation['total_players_in_lane']
            all_players_at_lines = formation['players_at_left_line'] + formation['players_at_right_line']
            ball_at_line = frame_ball_possession in all_players_at_lines

            if total_at_lines == 1:
                frames_with_one_at_line += 1
            if players_in_lane >= free_throw_detector.min_players_in_lane:
                frames_with_sufficient_lane += 1
            if ball_at_line:
                frames_with_ball_holder_at_line += 1
            if (total_at_lines == 1 and
                players_in_lane >= free_throw_detector.min_players_in_lane and
                ball_at_line):
                frames_meeting_all_three += 1

            confidence = free_throw_detector.calculate_free_throw_confidence(formation, frame_ball_possession, 0)
            if confidence > max_confidence:
                max_confidence = confidence
                max_conf_frame = frame_num
                best_formation = formation
                best_ball_at_line = ball_at_line

            if total_at_lines != 1:
                blockers_counts['line_presence'] += 1
            if players_in_lane < free_throw_detector.min_players_in_lane:
                blockers_counts['lane_occupancy'] += 1
            if not ball_at_line:
                blockers_counts['possession_alignment'] += 1

        print("No free throw situations detected in the video.")
        print("Diagnostic summary:")
        print(f"  Max confidence observed: {max_confidence:.2f} (threshold {free_throw_detector.confidence_threshold:.2f}) at frame {max_conf_frame if max_conf_frame != -1 else 'N/A'}")
        if max_conf_frame != -1 and best_formation is not None:
            total_at_lines = len(best_formation['players_at_left_line']) + len(best_formation['players_at_right_line'])
            players_in_lane = best_formation['total_players_in_lane']
            line_factor = (0.4 if total_at_lines == 1 else max(0.0, 0.4 - max(0, total_at_lines - 1) * 0.2))
            lane_factor = (0.3 if players_in_lane >= free_throw_detector.min_players_in_lane else (players_in_lane / max(1, free_throw_detector.min_players_in_lane)) * 0.3)
            possession_factor = 0.3 if best_ball_at_line else 0.0
            gap = max(0.0, free_throw_detector.confidence_threshold - max_confidence)
            print(f"  Best-frame factors: line={line_factor:.2f}, lane={lane_factor:.2f}, possession={possession_factor:.2f}")
            print(f"  Players at lines (L,R): ({len(best_formation['players_at_left_line'])},{len(best_formation['players_at_right_line'])}); in lane: {players_in_lane}")
            print(f"  Ball holder at line: {best_ball_at_line}")
            print(f"  Confidence gap to threshold: {gap:.2f}")
        print("  Condition coverage across frames:")
        print(f"    Exactly one player at a line: {frames_with_one_at_line}")
        print(f"    Sufficient lane occupancy (>= {free_throw_detector.min_players_in_lane}): {frames_with_sufficient_lane}")
        print(f"    Ball holder at a line: {frames_with_ball_holder_at_line}")
        print(f"    Frames meeting all three conditions: {frames_meeting_all_three}")
        print("  Most common blockers (frame counts):")
        print(f"    Line presence issue: {blockers_counts['line_presence']}")
        print(f"    Lane occupancy issue: {blockers_counts['lane_occupancy']}")
        print(f"    Possession alignment issue: {blockers_counts['possession_alignment']}")

    # Collect statistics throughout video processing
    # Note: In a real implementation, you would detect actual basketball events
    # like shots, rebounds, turnovers, etc. For now, we'll use example data
    
    # Example statistics for demonstration
    team1_stats = {
        'fgm': 2,  # Field goals made (2-pointers)
        'fga': 3,  # Field goal attempts (2-pointers)
        'fgm_3pt': 1,  # Three-point field goals made
        'fga_3pt': 2,  # Three-point field goal attempts
        'ftm': 3,  # Free throws made
        'fta': 4,  # Free throw attempts
        'offensive_rebounds': 5,
        'defensive_rebounds': 8,
        'turnovers': 1,
        'possessions': 20
    }
    
    team2_stats = {
        'fgm': 1,  # Field goals made (2-pointers)
        'fga': 4,  # Field goal attempts (2-pointers)
        'fgm_3pt': 2,  # Three-point field goals made
        'fga_3pt': 3,  # Three-point field goal attempts
        'ftm': 2,  # Free throws made
        'fta': 3,  # Free throw attempts
        'offensive_rebounds': 3,
        'defensive_rebounds': 10,
        'turnovers': 5,
        'possessions': 18
    }

    # Draw output   
    # Initialize Drawers
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    court_keypoint_drawer = CourtKeypointDrawer()
    team_ball_control_drawer = TeamBallControlDrawer()
    frame_number_drawer = FrameNumberDrawer()
    pass_and_interceptions_drawer = PassInterceptionDrawer()
    tactical_view_drawer = TacticalViewDrawer()
    speed_and_distance_drawer = SpeedAndDistanceDrawer()
    free_throw_drawer = FreeThrowDrawer()

    ## Draw object Tracks
    output_video_frames = player_tracks_drawer.draw(video_frames, 
                                                    player_tracks,
                                                    player_assignment,
                                                    ball_aquisition)
    output_video_frames = ball_tracks_drawer.draw(output_video_frames, ball_tracks)

    ## Draw KeyPoints
    output_video_frames = court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)

    ## Draw Frame Number
    output_video_frames = frame_number_drawer.draw(output_video_frames)

    # Draw Team Ball Control
    output_video_frames = team_ball_control_drawer.draw(output_video_frames,
                                                        player_assignment,
                                                        ball_aquisition)

    # Draw Passes and Interceptions
    output_video_frames = pass_and_interceptions_drawer.draw(output_video_frames,
                                                             passes,
                                                             interceptions)
    
    # Speed and Distance Drawer
    output_video_frames = speed_and_distance_drawer.draw(output_video_frames,
                                                         player_tracks,
                                                         player_distances_per_frame,
                                                         player_speed_per_frame
                                                         )

    # Free Throw Detection Drawer
    output_video_frames = free_throw_drawer.draw(output_video_frames,
                                                free_throw_events,
                                                tactical_player_positions,
                                                player_assignment,
                                                tactical_view_converter,
                                                show_summary=True)

    ## Draw Tactical View
    output_video_frames = tactical_view_drawer.draw(output_video_frames,
                                                    tactical_view_converter.court_image_path,
                                                    tactical_view_converter.width,
                                                    tactical_view_converter.height,
                                                    tactical_view_converter.key_points,
                                                    tactical_player_positions,
                                                    player_assignment,
                                                    ball_aquisition,
                                                    )

    # Save video
    save_video(output_video_frames, args.output_video)
    
    # Display comprehensive four factors summary after processing entire clip
    print_four_factors_summary(team1_stats, team2_stats, len(video_frames), fps=30.0)

if __name__ == '__main__':
    main()
    