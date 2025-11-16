from datetime import datetime
from app.db import db


class Team(db.Model):
    """Team model for esports teams."""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    members = db.Column(db.String(500), nullable=True)  # String to store member names
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    matches_as_team_a = db.relationship('Match', foreign_keys='Match.team_a_id', backref='team_a', lazy='dynamic')
    matches_as_team_b = db.relationship('Match', foreign_keys='Match.team_b_id', backref='team_b', lazy='dynamic')
    leaderboard_entries = db.relationship('Leaderboard', backref='team', lazy='dynamic')
    
    def __repr__(self):
        return f'<Team {self.name}>'


class Tournament(db.Model):
    """Tournament model for esports tournaments."""
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), default='single_elim', nullable=False)
    seeding = db.Column(db.String(50), default='random', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    matches = db.relationship('Match', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')
    leaderboard_entries = db.relationship('Leaderboard', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tournament {self.name}>'


class Match(db.Model):
    """Match model for tournament matches."""
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False, index=True)
    round = db.Column(db.Integer, nullable=False, index=True)
    slot = db.Column(db.Integer, nullable=False, index=True)
    team_a_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    team_b_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    played = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    winner = db.relationship('Team', foreign_keys=[winner_id], post_update=True)
    
    # Unique constraint: one match per tournament/round/slot combination
    __table_args__ = (db.UniqueConstraint('tournament_id', 'round', 'slot', name='uq_match_tournament_round_slot'),)
    
    def __repr__(self):
        return f'<Match {self.id} Tournament {self.tournament_id} Round {self.round} Slot {self.slot}>'


class Leaderboard(db.Model):
    """Leaderboard model for tournament standings."""
    __tablename__ = 'leaderboards'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    wins = db.Column(db.Integer, default=0, nullable=False)
    losses = db.Column(db.Integer, default=0, nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    
    # Unique constraint: one leaderboard entry per tournament/team combination
    __table_args__ = (db.UniqueConstraint('tournament_id', 'team_id', name='uq_leaderboard_tournament_team'),)
    
    def __repr__(self):
        return f'<Leaderboard Tournament {self.tournament_id} Team {self.team_id} W:{self.wins} L:{self.losses}>'
