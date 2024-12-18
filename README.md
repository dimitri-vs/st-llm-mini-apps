## Running & Developing the Project Locally

### .env file
Duplicate and rename the `.env.example` file to `.env` adding your own values.

### Initial Setup
Requires Python 3.8 or higher
- Create a virtual environment using `python -m venv venv`
- Always run `venv\Scripts\activate` to activate the virtual environment
- Run `pip install -r requirements.txt` to install all dependencies
- Run `streamlit run app.py` to start the server

### Ongoing Development
- Run `venv\Scripts\activate` to activate the virtual environment
- ⚠️ Always activate the virtual environment before running any commands
- Run `streamlit run app.py` to start the server
- To check for package updates, run `pip list --outdated`
- To add new packages, first add it to `requirements.txt` then run `pip install -r requirements.txt`

## Deploying to Railway.app
- Dashboard > New Project > Deploy from GitHub repo
- If you get a "Invalid service name" error create a blank service and then link the repo under Settings > Source Repo
- Select Add variables, under **Variables**:
    - Add `PORT` with value `8501`
    - Add other environment variables from `.env` file
- Click `x` to close open service, click Settings and update project name from auto-generated one, use repo name
- Click on the service (if you see Failed deployment, dont worry about it yet) under **Settings**:
    - At the top click 📝 to change service name to "streamlit-app" or similar
    - Networking > Public Networking, click `Generate Domain`, port 8502, this will be the public URL, change if needed
    - Deploy > Custom Start Command, enter `streamlit run app.py`
- You should see a large banned that says "Apply 2 changes", click Deploy, takes about 5 minutes
- You should now be able to view the app at the public URL
- For debugging deployment issues, in the service, under **Deployments**:
    - Click on the latest deployment > `View Logs`
    - Check `Build Logs` and `Deploy Logs` for errors
