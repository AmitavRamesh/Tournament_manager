import math
import random
from app.db import db
from app.models import Tournament, Match, Leaderboard, Team


def generate_bracket(tournament, team_ids):
    """
    Generate a single-elimination bracket for a tournament.
    
    Args:
        tournament: Tournament object
        team_ids: List of team IDs to include in the bracket
    
    Returns:
        dict: Information about the generated bracket
    """
    if len(team_ids) < 2:
        raise ValueError("At least 2 teams are required to generate a bracket")
    
    # Calculate number of rounds needed
    num_teams = len(team_ids)
    num_slots_round1 = 2 ** math.ceil(math.log2(num_teams))
    num_matches_round1 = num_slots_round1 // 2  # Each match has 2 slots
    # Number of rounds = log2(slots)
    # For 4 teams: 4 slots -> 2 rounds (round 1: 2 matches, round 2: 1 final match)
    # For 8 teams: 8 slots -> 3 rounds (round 1: 4 matches, round 2: 2 matches, round 3: 1 final)
    num_rounds = int(math.log2(num_slots_round1))
    
    # Apply seeding
    if tournament.seeding == 'ranked':
        # Order teams by their leaderboard stats (wins desc, losses asc)
        leaderboard_entries = Leaderboard.query.filter(
            Leaderboard.tournament_id == tournament.id,
            Leaderboard.team_id.in_(team_ids)
        ).order_by(
            Leaderboard.wins.desc(),
            Leaderboard.losses.asc(),
            Leaderboard.points.desc()
        ).all()
        seeded_team_ids = [entry.team_id for entry in leaderboard_entries]
        # Add any teams not in leaderboard (shouldn't happen, but safety check)
        for team_id in team_ids:
            if team_id not in seeded_team_ids:
                seeded_team_ids.append(team_id)
    else:  # random seeding
        seeded_team_ids = team_ids.copy()
        random.shuffle(seeded_team_ids)
    
    # Create round 1 matches
    matches_created = []
    byes_advanced = []
    
    for slot in range(num_matches_round1):
        # Calculate team indices for this match
        team_a_index = slot * 2
        team_b_index = slot * 2 + 1
        
        team_a_id = seeded_team_ids[team_a_index] if team_a_index < len(seeded_team_ids) else None
        team_b_id = seeded_team_ids[team_b_index] if team_b_index < len(seeded_team_ids) else None
        
        # Create match
        match = Match(
            tournament_id=tournament.id,
            round=1,
            slot=slot,
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            played=False
        )
        db.session.add(match)
        matches_created.append(match)
        
        # Handle bye advancement
        if team_a_id and team_b_id is None:
            # Team A gets a bye, advance automatically
            byes_advanced.append(team_a_id)
            match.played = True
            match.winner_id = team_a_id
            # Update leaderboard
            leaderboard = Leaderboard.query.filter_by(
                tournament_id=tournament.id,
                team_id=team_a_id
            ).first()
            if leaderboard:
                leaderboard.wins += 1
    
    db.session.commit()
    
    # Advance all bye winners to next round
    for team_id in byes_advanced:
        _advance_team_to_next_round(tournament, team_id, 1, num_slots_round1)
    
    return {
        'num_teams': num_teams,
        'num_rounds': num_rounds,
        'round1_slots': num_slots_round1,
        'round1_matches': num_matches_round1,
        'matches_created': len(matches_created),
        'byes_advanced': len(byes_advanced)
    }


def _advance_team_to_next_round(tournament, team_id, current_round, current_round_slots):
    """
    Helper function to advance a team to the next round.
    
    Args:
        tournament: Tournament object
        team_id: ID of team to advance
        current_round: Current round number
        current_round_slots: Number of slots in current round
    """
    # Calculate next round and slot
    next_round = current_round + 1
    # Find the match this team is in
    current_match = Match.query.filter_by(
        tournament_id=tournament.id,
        round=current_round,
        winner_id=team_id
    ).first()
    
    if not current_match:
        return
    
    current_slot = current_match.slot
    # For matches: slot 0 and 1 go to slot 0, slot 2 and 3 go to slot 1, etc.
    # So next_slot = current_slot // 2
    next_slot = current_slot // 2
    # next_round_slots is the number of slots in the next round
    next_round_slots = current_round_slots // 2
    
    # Check if next round match exists
    next_match = Match.query.filter_by(
        tournament_id=tournament.id,
        round=next_round,
        slot=next_slot
    ).first()
    
    if not next_match:
        # Create next round match
        next_match = Match(
            tournament_id=tournament.id,
            round=next_round,
            slot=next_slot,
            team_a_id=None,
            team_b_id=None,
            played=False
        )
        db.session.add(next_match)
    
    # Insert team into appropriate position (even slots -> team_a, odd slots -> team_b)
    if current_slot % 2 == 0:
        next_match.team_a_id = team_id
    else:
        next_match.team_b_id = team_id
    
    db.session.commit()


def advance_winner(match_id, winner_id):
    """
    Advance a match winner to the next round and update leaderboard.
    
    Args:
        match_id: ID of the match
        winner_id: ID of the winning team
    
    Returns:
        dict: Information about the advancement
    """
    match = Match.query.get(match_id)
    if not match:
        raise ValueError(f"Match {match_id} not found")
    
    # Validate winner belongs to match
    if winner_id not in [match.team_a_id, match.team_b_id]:
        raise ValueError(f"Winner team {winner_id} does not belong to match {match_id}")
    
    if match.played:
        raise ValueError(f"Match {match_id} result has already been submitted")
    
    # Mark match as played
    match.winner_id = winner_id
    match.played = True
    
    # Update leaderboard
    leaderboard_a = Leaderboard.query.filter_by(
        tournament_id=match.tournament_id,
        team_id=match.team_a_id
    ).first()
    
    leaderboard_b = Leaderboard.query.filter_by(
        tournament_id=match.tournament_id,
        team_id=match.team_b_id
    ).first()
    
    if leaderboard_a and leaderboard_b:
        if winner_id == match.team_a_id:
            leaderboard_a.wins += 1
            leaderboard_b.losses += 1
        else:
            leaderboard_b.wins += 1
            leaderboard_a.losses += 1
    
    db.session.commit()
    
    # Check if this is the final match
    tournament = Tournament.query.get(match.tournament_id)
    total_rounds = _get_total_rounds(tournament)
    
    # Final match is in the last round
    if match.round == total_rounds:
        # This is the final match - tournament is complete
        return {
            'match_id': match.id,
            'winner_id': winner_id,
            'tournament_complete': True,
            'champion_id': winner_id
        }
    
    # Advance winner to next round
    current_round_slots = _get_round_slots(tournament, match.round)
    _advance_team_to_next_round(
        tournament,
        winner_id,
        match.round,
        current_round_slots
    )
    
    # Check if next round match is ready to play (both teams filled)
    next_round = match.round + 1
    next_slot = match.slot // 2
    
    next_match = Match.query.filter_by(
        tournament_id=match.tournament_id,
        round=next_round,
        slot=next_slot
    ).first()
    
    return {
        'match_id': match.id,
        'winner_id': winner_id,
        'tournament_complete': False,
        'next_match_id': next_match.id if next_match else None,
        'next_match_ready': next_match and next_match.team_a_id and next_match.team_b_id if next_match else False
    }


def _get_total_rounds(tournament):
    """Calculate total number of rounds in the tournament."""
    round1_matches = Match.query.filter_by(
        tournament_id=tournament.id,
        round=1
    ).count()
    
    if round1_matches == 0:
        return 0
    
    # Each match represents 2 slots, so round1_slots = round1_matches * 2
    # Total rounds = log2(round1_slots) = log2(round1_matches * 2) = log2(round1_matches) + 1
    # For 2 matches (4 slots): log2(2) + 1 = 2 rounds
    # For 4 matches (8 slots): log2(4) + 1 = 3 rounds
    return int(math.log2(round1_matches * 2))


def _get_round_slots(tournament, round_num):
    """Get the number of slots in a given round."""
    if round_num == 1:
        return Match.query.filter_by(
            tournament_id=tournament.id,
            round=1
        ).count()
    else:
        # Each round has half the slots of the previous round
        round1_slots = _get_round1_slots(tournament)
        return round1_slots // (2 ** (round_num - 1))


def _get_round1_slots(tournament):
    """Get the number of slots in round 1."""
    return Match.query.filter_by(
        tournament_id=tournament.id,
        round=1
    ).count()
