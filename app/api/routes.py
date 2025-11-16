from flask import Blueprint, request, jsonify
from app.db import db
from app.models import Team, Tournament, Match, Leaderboard
from app.bracket import generate_bracket, advance_winner

bp = Blueprint('api', __name__)


@bp.route('/teams', methods=['POST'])
def create_team():
    """Create a new team."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Team name is required'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Team name cannot be empty'}), 400
    
    members = data.get('members', '').strip() if data.get('members') else None
    
    # Check if team with same name already exists
    existing_team = Team.query.filter_by(name=name).first()
    if existing_team:
        return jsonify({'error': f'Team with name "{name}" already exists'}), 400
    
    try:
        team = Team(name=name, members=members)
        db.session.add(team)
        db.session.commit()
        
        return jsonify({
            'id': team.id,
            'name': team.name,
            'members': team.members,
            'created_at': team.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/teams', methods=['GET'])
def get_teams():
    """Get all teams."""
    try:
        teams = Team.query.all()
        return jsonify([{
            'id': team.id,
            'name': team.name,
            'members': team.members,
            'created_at': team.created_at.isoformat()
        } for team in teams]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments', methods=['POST'])
def create_tournament():
    """Create a new tournament."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Tournament name is required'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Tournament name cannot be empty'}), 400
    
    tournament_type = data.get('type', 'single_elim')
    seeding = data.get('seeding', 'random')
    
    try:
        tournament = Tournament(name=name, type=tournament_type, seeding=seeding)
        db.session.add(tournament)
        db.session.commit()
        
        return jsonify({
            'id': tournament.id,
            'name': tournament.name,
            'type': tournament.type,
            'seeding': tournament.seeding,
            'created_at': tournament.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments/<int:tournament_id>/add-teams', methods=['POST'])
def add_teams_to_tournament(tournament_id):
    """Add teams to a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    data = request.get_json()
    if not data or 'team_ids' not in data:
        return jsonify({'error': 'team_ids array is required'}), 400
    
    team_ids = data.get('team_ids', [])
    if not isinstance(team_ids, list) or len(team_ids) == 0:
        return jsonify({'error': 'team_ids must be a non-empty array'}), 400
    
    # Validate all team IDs exist
    teams = Team.query.filter(Team.id.in_(team_ids)).all()
    found_ids = {team.id for team in teams}
    missing_ids = set(team_ids) - found_ids
    
    if missing_ids:
        return jsonify({'error': f'Teams with IDs {list(missing_ids)} not found'}), 404
    
    try:
        added_teams = []
        for team_id in team_ids:
            # Check if leaderboard entry already exists
            existing = Leaderboard.query.filter_by(
                tournament_id=tournament_id,
                team_id=team_id
            ).first()
            
            if not existing:
                leaderboard_entry = Leaderboard(
                    tournament_id=tournament_id,
                    team_id=team_id,
                    wins=0,
                    losses=0,
                    points=0
                )
                db.session.add(leaderboard_entry)
                added_teams.append(team_id)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Added {len(added_teams)} teams to tournament',
            'added_team_ids': added_teams,
            'total_teams': len(team_ids)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments/<int:tournament_id>/generate-bracket', methods=['POST'])
def generate_tournament_bracket(tournament_id):
    """Generate bracket for a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    # Get teams from leaderboard
    leaderboard_entries = Leaderboard.query.filter_by(tournament_id=tournament_id).all()
    team_ids = [entry.team_id for entry in leaderboard_entries]
    
    if len(team_ids) < 2:
        return jsonify({'error': 'Tournament must have at least 2 teams to generate bracket'}), 400
    
    # Check if bracket already exists
    existing_matches = Match.query.filter_by(tournament_id=tournament_id).first()
    if existing_matches:
        return jsonify({'error': 'Bracket already generated for this tournament'}), 400
    
    try:
        # Generate bracket using bracket module
        result = generate_bracket(tournament, team_ids)
        
        return jsonify({
            'message': 'Bracket generated successfully',
            'tournament_id': tournament_id,
            'num_teams': result['num_teams'],
            'num_rounds': result['num_rounds'],
            'round1_slots': result['round1_slots'],
            'matches_created': result['matches_created'],
            'byes_advanced': result['byes_advanced']
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments/<int:tournament_id>/matches', methods=['GET'])
def get_tournament_matches(tournament_id):
    """Get all matches for a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    try:
        matches = Match.query.filter_by(tournament_id=tournament_id).order_by(
            Match.round, Match.slot
        ).all()
        
        return jsonify([{
            'id': match.id,
            'tournament_id': match.tournament_id,
            'round': match.round,
            'slot': match.slot,
            'team_a_id': match.team_a_id,
            'team_b_id': match.team_b_id,
            'winner_id': match.winner_id,
            'played': match.played
        } for match in matches]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments/<int:tournament_id>/bracket', methods=['GET'])
def get_tournament_bracket(tournament_id):
    """Get bracket view for a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    try:
        matches = Match.query.filter_by(tournament_id=tournament_id).order_by(
            Match.round, Match.slot
        ).all()
        
        # Organize matches by round
        bracket = {}
        for match in matches:
            round_num = match.round
            if round_num not in bracket:
                bracket[round_num] = []
            
            bracket[round_num].append({
                'id': match.id,
                'slot': match.slot,
                'team_a_id': match.team_a_id,
                'team_b_id': match.team_b_id,
                'winner_id': match.winner_id,
                'played': match.played
            })
        
        return jsonify({
            'tournament_id': tournament_id,
            'tournament_name': tournament.name,
            'bracket': bracket
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/matches/<int:match_id>/result', methods=['POST'])
def submit_match_result(match_id):
    """Submit match result."""
    match = Match.query.get_or_404(match_id)
    
    data = request.get_json()
    if not data or 'winner_id' not in data:
        return jsonify({'error': 'winner_id is required'}), 400
    
    winner_id = data.get('winner_id')
    
    # Validate winner belongs to match
    if winner_id not in [match.team_a_id, match.team_b_id]:
        return jsonify({
            'error': f'Winner team ID {winner_id} does not belong to this match'
        }), 400
    
    if match.played:
        return jsonify({'error': 'Match result has already been submitted'}), 400
    
    try:
        # Use advance_winner function which handles leaderboard update and auto-advancement
        result = advance_winner(match_id, winner_id)
        
        response_data = {
            'message': 'Match result submitted successfully',
            'match_id': match.id,
            'winner_id': match.winner_id,
            'played': match.played,
            'tournament_complete': result.get('tournament_complete', False)
        }
        
        if result.get('tournament_complete'):
            response_data['champion_id'] = result.get('champion_id')
        else:
            response_data['next_match_id'] = result.get('next_match_id')
            response_data['next_match_ready'] = result.get('next_match_ready', False)
        
        return jsonify(response_data), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tournaments/<int:tournament_id>/leaderboard', methods=['GET'])
def get_tournament_leaderboard(tournament_id):
    """Get leaderboard for a tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    try:
        leaderboard_entries = Leaderboard.query.filter_by(
            tournament_id=tournament_id
        ).order_by(
            Leaderboard.wins.desc(),
            Leaderboard.points.desc(),
            Leaderboard.losses.asc()
        ).all()
        
        result = []
        for entry in leaderboard_entries:
            team = Team.query.get(entry.team_id)
            result.append({
                'team_id': entry.team_id,
                'team_name': team.name if team else 'Unknown',
                'wins': entry.wins,
                'losses': entry.losses,
                'points': entry.points
            })
        
        return jsonify({
            'tournament_id': tournament_id,
            'tournament_name': tournament.name,
            'leaderboard': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
