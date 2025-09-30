from typing import Dict, Tuple

def calculate_four_factors(fgm: int, fga: int, fgm_3pt: int, fga_3pt: int, ftm: int, fta: int, 
                         offensive_rebounds: int, defensive_rebounds: int, 
                         turnovers: int, possessions: int) -> Dict[str, float]:
    """
    Calculate the four factors of basketball analytics.
    
    Args:
        fgm (int): Field goals made (2-pointers)
        fga (int): Field goal attempts (2-pointers)
        fgm_3pt (int): Three-point field goals made
        fga_3pt (int): Three-point field goal attempts
        ftm (int): Free throws made
        fta (int): Free throw attempts
        offensive_rebounds (int): Offensive rebounds
        defensive_rebounds (int): Defensive rebounds
        turnovers (int): Turnovers
        possessions (int): Total possessions
        
    Returns:
        dict: Dictionary containing all four factors and raw statistics
    """
    # Calculate Effective Field Goal Percentage
    # eFG% = (0.5 * 3FGM + FGM) / FGA
    effective_fg_percentage = 0.0
    total_fga = fga + fga_3pt  # Total field goal attempts
    if total_fga > 0:
        total_fgm = fgm + fgm_3pt  # Total field goals including three-pointers
        effective_fg_percentage = (0.5 * fgm_3pt + total_fgm) / total_fga
        effective_fg_percentage = min(effective_fg_percentage, 1.0)  # Cap at 100%
    
    # Calculate Turnover Percentage
    # TO% = TO / Possessions
    turnover_percentage = 0.0
    if possessions > 0:
        turnover_percentage = turnovers / possessions
    
    # Calculate Offensive Rebounding Percentage
    # OR% = OR / (OR + DR)
    offensive_rebound_percentage = 0.0
    total_rebounds = offensive_rebounds + defensive_rebounds
    if total_rebounds > 0:
        offensive_rebound_percentage = offensive_rebounds / total_rebounds
    
    # Calculate Free Throw Rate
    # FTRate = FTA / FGA
    free_throw_rate = 0.0
    if total_fga > 0:
        free_throw_rate = fta / total_fga
    
    return {
        'effective_fg_percentage': effective_fg_percentage,
        'turnover_percentage': turnover_percentage,
        'offensive_rebound_percentage': offensive_rebound_percentage,
        'free_throw_rate': free_throw_rate,
        'raw_stats': {
            'fgm': fgm,
            'fga': fga,
            'fgm_3pt': fgm_3pt,
            'fga_3pt': fga_3pt,
            'ftm': ftm,
            'fta': fta,
            'offensive_rebounds': offensive_rebounds,
            'defensive_rebounds': defensive_rebounds,
            'turnovers': turnovers,
            'possessions': possessions
        }
    }

def print_four_factors_summary(team1_stats: Dict, team2_stats: Dict, 
                              total_frames: int = 0, fps: float = 30.0, 
                              print_to_console: bool = True) -> Dict:
    """
    Calculate and optionally print four factors summary for both teams.
    
    Args:
        team1_stats (dict): Team 1 statistics with keys: fgm, fga, fgm_3pt, ftm, fta, 
                           offensive_rebounds, defensive_rebounds, turnovers, possessions
        team2_stats (dict): Team 2 statistics with same keys as team1_stats
        total_frames (int): Total frames processed (optional)
        fps (float): Frames per second (optional)
        print_to_console (bool): Whether to print to console (default: True)
        
    Returns:
        dict: Complete analysis results for both teams
    """
    # Calculate four factors for both teams
    team1_factors = calculate_four_factors(**team1_stats)
    team2_factors = calculate_four_factors(**team2_stats)
    
    # Prepare results
    results = {
        'team1': team1_factors,
        'team2': team2_factors,
        'video_metadata': {
            'total_frames': total_frames,
            'duration_seconds': total_frames / fps if fps > 0 else 0.0
        }
    }
    
    if not print_to_console:
        return results
    
    # Print comprehensive summary
    print("\n" + "="*80)
    print("BASKETBALL GAME ANALYSIS - FOUR FACTORS SUMMARY")
    print("="*80)
    
    # Video metadata
    if total_frames > 0:
        duration_minutes = results['video_metadata']['duration_seconds'] / 60
        print(f"\nVideo Analysis Summary:")
        print(f"  Total Frames Processed: {total_frames:,}")
        print(f"  Game Duration: {results['video_metadata']['duration_seconds']:.1f} seconds ({duration_minutes:.1f} minutes)")
    
    # Team 1 stats
    print(f"\n" + "-"*80)
    print("TEAM 1 STATISTICS")
    print("-"*80)
    _print_team_summary(1, team1_stats, team1_factors)
    
    # Team 2 stats
    print(f"\n" + "-"*80)
    print("TEAM 2 STATISTICS")
    print("-"*80)
    _print_team_summary(2, team2_stats, team2_factors)
    
    # Comparison
    print(f"\n" + "-"*80)
    print("FOUR FACTORS COMPARISON")
    print("-"*80)
    _print_four_factors_comparison(team1_factors, team2_factors)
    
    # Analysis
    print(f"\n" + "-"*80)
    print("PERFORMANCE ANALYSIS")
    print("-"*80)
    _print_performance_analysis(team1_factors, team2_factors, team1_stats, team2_stats)
    
    print("\n" + "="*80)
    
    return results

def _print_team_summary(team_id: int, stats: Dict, factors: Dict):
    """Print detailed summary for a specific team."""
    raw = factors['raw_stats']
    print(f"\nRaw Statistics:")
    total_fgm = raw['fgm'] + raw['fgm_3pt']
    total_fga = raw['fga'] + raw['fga_3pt']
    print(f"  Field Goals: {total_fgm}/{total_fga} ({total_fgm/total_fga*100:.1f}%)" if total_fga > 0 else "  Field Goals: 0/0 (0.0%)")
    print(f"  3-Pointers: {raw['fgm_3pt']}/{raw['fga_3pt']} ({raw['fgm_3pt']/raw['fga_3pt']*100:.1f}%)" if raw['fga_3pt'] > 0 else "  3-Pointers: 0/0 (0.0%)")
    print(f"  2-Pointers: {raw['fgm']}/{raw['fga']} ({raw['fgm']/raw['fga']*100:.1f}%)" if raw['fga'] > 0 else "  2-Pointers: 0/0 (0.0%)")
    print(f"  Free Throws: {raw['ftm']}/{raw['fta']} ({raw['ftm']/raw['fta']*100:.1f}%)" if raw['fta'] > 0 else "  Free Throws: 0/0 (0.0%)")
    print(f"  Offensive Rebounds: {raw['offensive_rebounds']}")
    print(f"  Defensive Rebounds: {raw['defensive_rebounds']}")
    print(f"  Total Rebounds: {raw['offensive_rebounds'] + raw['defensive_rebounds']}")
    print(f"  Turnovers: {raw['turnovers']}")
    print(f"  Possessions: {raw['possessions']}")
    
    print(f"\nFour Factors:")
    print(f"  1. Effective FG%: {factors['effective_fg_percentage']:.3f} ({factors['effective_fg_percentage']*100:.1f}%)")
    print(f"  2. Turnover %: {factors['turnover_percentage']:.3f} ({factors['turnover_percentage']*100:.1f}%)")
    print(f"  3. Offensive Rebound %: {factors['offensive_rebound_percentage']:.3f} ({factors['offensive_rebound_percentage']*100:.1f}%)")
    print(f"  4. Free Throw Rate: {factors['free_throw_rate']:.3f}")

def _print_four_factors_comparison(team1_factors: Dict, team2_factors: Dict):
    """Print side-by-side comparison of four factors."""
    factors = [
        ("Effective FG%", team1_factors['effective_fg_percentage'], team2_factors['effective_fg_percentage'], "Higher is better"),
        ("Turnover %", team1_factors['turnover_percentage'], team2_factors['turnover_percentage'], "Lower is better"),
        ("Offensive Rebound %", team1_factors['offensive_rebound_percentage'], team2_factors['offensive_rebound_percentage'], "Higher is better"),
        ("Free Throw Rate", team1_factors['free_throw_rate'], team2_factors['free_throw_rate'], "Higher is better")
    ]
    
    print(f"{'Factor':<20} {'Team 1':<12} {'Team 2':<12} {'Winner':<10} {'Note'}")
    print("-" * 70)
    
    for factor_name, team1_val, team2_val, note in factors:
        if factor_name == "Turnover %":
            team1_advantage = team1_val < team2_val
        else:
            team1_advantage = team1_val > team2_val
            
        winner = "Team 1" if team1_advantage else "Team 2"
        print(f"{factor_name:<20} {team1_val:<12.3f} {team2_val:<12.3f} {winner:<10} {note}")

def _print_performance_analysis(team1_factors: Dict, team2_factors: Dict, team1_stats: Dict, team2_stats: Dict):
    """Print performance analysis and insights."""
    print("Key Insights:")
    
    # Effective FG% analysis
    if team1_factors['effective_fg_percentage'] > team2_factors['effective_fg_percentage']:
        diff = team1_factors['effective_fg_percentage'] - team2_factors['effective_fg_percentage']
        print(f"  • Team 1 is more efficient shooting (+{diff:.3f} eFG%)")
    elif team2_factors['effective_fg_percentage'] > team1_factors['effective_fg_percentage']:
        diff = team2_factors['effective_fg_percentage'] - team1_factors['effective_fg_percentage']
        print(f"  • Team 2 is more efficient shooting (+{diff:.3f} eFG%)")
    else:
        print(f"  • Both teams have similar shooting efficiency")
        
    # Turnover analysis
    if team1_factors['turnover_percentage'] < team2_factors['turnover_percentage']:
        diff = team2_factors['turnover_percentage'] - team1_factors['turnover_percentage']
        print(f"  • Team 1 has better ball security ({diff:.3f} fewer turnovers per possession)")
    elif team2_factors['turnover_percentage'] < team1_factors['turnover_percentage']:
        diff = team1_factors['turnover_percentage'] - team2_factors['turnover_percentage']
        print(f"  • Team 2 has better ball security ({diff:.3f} fewer turnovers per possession)")
    else:
        print(f"  • Both teams have similar ball security")
        
    # Rebounding analysis
    if team1_factors['offensive_rebound_percentage'] > team2_factors['offensive_rebound_percentage']:
        diff = team1_factors['offensive_rebound_percentage'] - team2_factors['offensive_rebound_percentage']
        print(f"  • Team 1 is better at offensive rebounding (+{diff:.3f})")
    elif team2_factors['offensive_rebound_percentage'] > team1_factors['offensive_rebound_percentage']:
        diff = team2_factors['offensive_rebound_percentage'] - team1_factors['offensive_rebound_percentage']
        print(f"  • Team 2 is better at offensive rebounding (+{diff:.3f})")
    else:
        print(f"  • Both teams have similar offensive rebounding")
        
    # Free throw rate analysis
    if team1_factors['free_throw_rate'] > team2_factors['free_throw_rate']:
        diff = team1_factors['free_throw_rate'] - team2_factors['free_throw_rate']
        print(f"  • Team 1 gets to the line more often (+{diff:.3f} FTRate)")
    elif team2_factors['free_throw_rate'] > team1_factors['free_throw_rate']:
        diff = team2_factors['free_throw_rate'] - team1_factors['free_throw_rate']
        print(f"  • Team 2 gets to the line more often (+{diff:.3f} FTRate)")
    else:
        print(f"  • Both teams get to the line at similar rates")

