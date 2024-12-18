## Running & Developing the Project Locally

### .env file
Duplicate and rename the `.env.example` file to `.env` adding your own values.

### Initial Setup
Requires Python 3.8 or higher (check with `python --version`)
- Create a virtual environment using `python -m venv venv`
- Always run `venv\Scripts\activate` to activate the virtual environment
- Run `python -m pip install --upgrade pip` to ensure pip is up to date
- Run `pip install -r requirements.txt` to install all dependencies
- Run `streamlit run app.py` to start the server

### Ongoing Development
- Run `venv\Scripts\activate` to activate the virtual environment
- ⚠️ Always activate the virtual environment before running any commands
- Run `streamlit run app.py` to start the server
- To check for package updates, run `pip list --outdated`
- To add new packages, first add it to `requirements.txt` then run `pip install -r requirements.txt`

## Deploying to Railway.app
- [Dashboard](https://railway.app/dashboard) > New Project > Deploy from GitHub repo > Add variables
- If you get a "Invalid service name" error create a blank service and then link the repo under Settings > Source Repo
- Select Add variables, under **Variables**:
    - Add `PORT` with value `8501`
- If you need a database, add a Postgres service:
    - Create > Postgres
    - View the DATABASE_PUBLIC_URL in Variables > Postgres, use this in your local `.env` file
    - Connect other services to the Postgres service with PG_DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}
- Click `x` to close open service, click Settings and:
    - Update project name from auto-generated one, use repo name
    - Under **Shared Variables**, add your other variables from `.env` file
- Click on the service under **Settings**:
    - Note: If you see "Failed deployment", dont worry about it yet.
    - At the top click 📝 to change service name to "streamlit-app" or similar
    - Settings > Networking > Public Networking, click `Generate Domain`, port 8501 (or 8502?)
    - While you're editing public networking, you should change the public URL to something more user-friendly
    - If you have an issue with ports try the "magic suggestion"
    - Deploy > Custom Start Command, enter `streamlit run app.py`
- You should see a large banner that says "Apply n changes", click Deploy; Takes about 5 minutes
- You should now be able to view the app at the public URL
- For debugging deployment issues, in the service, under **Deployments**:
    - Click on the latest deployment > `View Logs`
    - Check `Build Logs` and `Deploy Logs` for errors


### Adding a Database
- TODO: This section may be incomplete.
- Create a Postgres service
- View the DATABASE_PUBLIC_URL in Variables > Postgres, use this in your local `.env` file
- Connect other services to the Postgres service with PG_DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}


### Connecting to Railway Database with DBeaver

1. In DBeaver: New Database Connection > PostgreSQL > Connect by URL

2. Get the connection details from copying the Railway `DATABASE_PUBLIC_URL`:
   ```
   postgresql://${PGUSER}:${POSTGRES_PASSWORD}@${RAILWAY_TCP_PROXY_DOMAIN}:${RAILWAY_TCP_PROXY_PORT}/${PGDATABASE}
   ```
   Example:
   ```
   postgresql://postgres:abc123...@autorack.proxy.rlwy.net:59123/railway
   ```

3. Configure the connection:
   - **JDBC URL**: Convert the Railway URL to JDBC format:
     ```
     jdbc:postgresql://[RAILWAY_TCP_PROXY_DOMAIN]:[RAILWAY_TCP_PROXY_PORT]/[PGDATABASE]
     ```
     Example:
     ```
     jdbc:postgresql://autorack.proxy.rlwy.net:59123/railway
     ```
   - **Username**: Use the `PGUSER` value from Railway
   - **Password**: Use the `POSTGRES_PASSWORD` value from Railway
   - **General** > **Connection name**: Use your project name for clarity

4. Your database tables will be located under:
   ```
   {Connection Name} > Databases > railway > Schemas > Public > Tables
   ```