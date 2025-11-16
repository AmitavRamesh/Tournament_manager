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

### Running Backend Locally

1. **Install Dependencies:**
   ```bash
   cd tourney-backend
   pip install -r requirements.txt
   ```

2. **Set Up Database:**
   ```bash
   alembic upgrade head
   ```

3. **Run the Server:**
   ```bash
   python run.py
   ```
   
   The backend will start on `http://localhost:5000` by default.

4. **CORS Configuration:**
   - CORS is already enabled for all origins in development
   - For production, update `app/__init__.py` to restrict origins to your frontend URL

See [tourney-backend/README.md](tourney-backend/README.md) for detailed setup instructions.

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

Single-page application for tournament management with a modern UI.

### Running Frontend Locally

1. **Simple HTTP Server**: Since the frontend is a single HTML file, you can serve it using any HTTP server:

   **Using Python:**
   ```bash
   cd tourney-frontend
   python -m http.server 8000
   ```
   Then open `http://localhost:8000` in your browser.

   **Using Node.js (http-server):**
   ```bash
   cd tourney-frontend
   npx http-server -p 8000
   ```

   **Using VS Code Live Server**: Right-click on `index.html` and select "Open with Live Server"

2. **Configure API URL**: 
   - The frontend uses `config.js` to set the backend API URL
   - For local development, ensure `API_BASE` in `config.js` is set to `http://localhost:5000` (or your backend port)
   - Make sure the backend is running before opening the frontend

### Changing API_BASE for Production (Azure)

1. Open `tourney-frontend/config.js`
2. Update `API_BASE` to your backend's public Azure URL:
   ```javascript
   const API_BASE = 'https://your-backend-app.azurewebsites.net';
   ```

### Deploying Frontend on Azure

**Option 1: Azure Static Web Apps (Recommended)**
1. Create a new Static Web App in Azure Portal
2. Connect your repository
3. Set build configuration:
   - Build location: `tourney-frontend`
   - App location: `tourney-frontend`
   - Output location: `tourney-frontend`
4. Deploy and update `config.js` with your backend URL

**Option 2: Azure Storage Static Website**
1. Create a Storage Account in Azure Portal
2. Enable "Static website" in the Storage Account settings
3. Upload all files from `tourney-frontend` to the `$web` container
4. Access via the provided static website URL
5. Update `config.js` with your backend URL

### Updating CORS After Deployment

After deploying the frontend, update the backend CORS configuration:

1. Open `tourney-backend/app/__init__.py`
2. Update the CORS origins to include your frontend URL:
   ```python
   CORS(app, resources={r"/api/*": {
       "origins": ["https://your-frontend-app.azurestaticapps.net", "http://localhost:8000"]
   }})
   ```
3. Redeploy the backend

Alternatively, for development, CORS is already configured to allow all origins (`"origins": "*"`).

## License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

