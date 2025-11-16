# Tournament Manager

A full-stack esports tournament management system.

## Repository Structure

This is a monorepo containing multiple components:

```
Tournament_manager/
├── tourney-backend/     # Flask backend API
├── tourney-frontend/    # Frontend application (to be added)
└── LICENSE             # Apache 2.0 License
```

## Backend (tourney-backend)

The Flask backend for managing tournaments, teams, matches, and brackets.

### Features

- RESTful API for tournament management
- Single-elimination bracket generation
- Automatic winner advancement
- Bye handling for non-power-of-two team counts
- Leaderboard tracking
- Database migrations with Alembic

### Quick Start

See [tourney-backend/README.md](tourney-backend/README.md) for detailed setup instructions.

```bash
cd tourney-backend
pip install -r requirements.txt
alembic upgrade head
python run.py
```

### API Endpoints

- `POST /api/teams` - Create a team
- `GET /api/teams` - List all teams
- `POST /api/tournaments` - Create a tournament
- `POST /api/tournaments/<id>/add-teams` - Add teams to tournament
- `POST /api/tournaments/<id>/generate-bracket` - Generate bracket
- `GET /api/tournaments/<id>/matches` - Get tournament matches
- `GET /api/tournaments/<id>/bracket` - Get bracket view
- `POST /api/matches/<id>/result` - Submit match result
- `GET /api/tournaments/<id>/leaderboard` - Get leaderboard

## Frontend (tourney-frontend)

Frontend application - coming soon!

## License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

