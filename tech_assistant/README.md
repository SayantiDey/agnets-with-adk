# Praxis-Multi-Agent AI Assistant for Brainstorming & Support.
## Overview 
The Tech Assistant is a sample agent designed to assist with the full lifecycle of technical work—from ideation to resolution. 
This sample agent uses ADK (Agent Development Kit), a PostgreSQL support case database, google search, MCP Toolbox, and deployed on Cloud Run.

It is designed to assist with:
1. Brainstorming & Strategy: Assisting with the ideation of new technology use cases and providing detailed implementation guidance.
2. Technical Troubleshooting: Helping triage and debug complex technical issues.
3. Support Ticket Management: Handling the creation and status tracking of support cases to ensure efficient resolution.


## Agent Flow

<img src="architecture.png" width="50%" alt="Architecture">

## Setup and Installation Guide

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/SayantiDey/agnets-with-adk.git
cd tech_assistant
```

2. Edit the .env.example file to set up the environment variables and rename the file to .env

3. Authenticate the Google Cloud CLI, and enable Google Cloud APIs. 

```
gcloud auth login
gcloud auth application-default login 

export PROJECT_ID="<YOUR_PROJECT_ID>"
gcloud config set project $PROJECT_ID

gcloud services enable sqladmin.googleapis.com \
   compute.googleapis.com \
   cloudresourcemanager.googleapis.com \
   servicenetworking.googleapis.com \
   aiplatform.googleapis.com
```

4. Create a Cloud SQL for PostgreSQL instance. 

```bash
gcloud sql instances create supportcase-db \
--database-version=POSTGRES_15 \
--cpu=2 \
--memory=8GiB \
--region=us-central1 \
--edition=ENTERPRISE \
--root-password=<PUT_YOUR_PASSWORD>
```

Once created, you can view your instance in the Cloud Console.

5. Set up the `cases` table. 

- From the Cloud Console (Cloud SQL), open **Cloud SQL Studio**. 

- Log into the `supportcase-db` Database using the `postgres` user and the password you specified while creating the SQL instance.

- Open a new **Editor** tab. Then, paste in the following SQL code to set up the table and create vector embeddings.

```SQL
CREATE TABLE cases (
    ticket_id SERIAL PRIMARY KEY,             
    title VARCHAR(200) NOT NULL,              
    description TEXT,                         
    steps_taken VARCHAR(100),                    
    priority VARCHAR(20) DEFAULT 'p3-low',  
    error_msg VARCHAR(100), 
    status VARCHAR(50) DEFAULT 'Open',  
    contact VARCHAR(100) NOT NULL ,
    creation_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
);
```

- Add sample data to the table. 

From Cloud SQL Studio, paste in the following SQL code to load in sample data.

```SQL
INSERT INTO cases (title, description, error_msg, steps_taken, priority, status, contact)
VALUES
('GCE VM instance fails to start', 'The ''web-server-prod-01'' GCE instance in us-central1-a is not starting.', 'ZONE_RESOURCE_POOL_EXHAUSTED', 'Tried starting multiple times. Checked GCP status dashboard.', 'p1-high', 'Open', 'arjun.sh@example.net'),
('App Engine cannot connect to Cloud SQL', 'Our App Engine service ''user-api'' is failing to connect to the ''user-db'' Cloud SQL instance.', 'Connection timed out', 'Checked firewall rules and Cloud SQL proxy settings.', 'p1-high', 'In Progress', 'priya.k@abc.com'),
('IAM permission denied for Pub/Sub', 'Service account ''data-pipeline-sa'' is denied permission to publish to a Pub/Sub topic.', '7 PERMISSION_DENIED', 'Verified the service account has the ''Pub/Sub Publisher'' role.', 'p2-edium', 'Open', 'sneha.gupta@example.com'),
('Project has exceeded CPU quota', 'Cannot launch new GCE instances in project ''dev-sandbox-123'' in asia-south1.', 'QUOTA_EXCEEDED', 'Submitted a quota increase request via the console.', 'p3-Low', 'In Progress', 'vikram.s@example.ai'),
('GKE Autopilot not scaling up', 'GKE Autopilot cluster is not scaling pods for the ''payment-gateway'' deployment during peak load.', NULL, 'Checked HorizontalPodAutoscaler logs and resource limits.', 'p2-medium', 'Open', 'a.smith@sample.org');
```

- Verify that the database is ready.

From Cloud SQL studio, run:

```SQL
SELECT * FROM tickets;
```


6. Run the MCP Toolbox for Databases Server Locally to verify

- First, update `mcp-toolbox/tools.yaml` for your Cloud SQL instance: 

```yaml
sources:
 my-cloud-sql-source:
   kind: cloud-sql-postgres
   project: ${GCP_PROJECT_ID}
   region: us-central1
   instance: supportcase-db
   database: postgres
   user: ${DB_USER}
   password: ${DB_PASSWORD}
```
- Run the following command (from the mcp-toolbox folder) to start the server:
```bash
./toolbox --tools-file "tools.yaml"
```
Ideally you should see an output that the Server has been able to connect to our data sources and has loaded the toolset and tools. A sample output:
```bash
./toolbox --tools-file "tools.yaml"
2025-04-23T14:32:29.564903079Z INFO "Initialized 1 sources." 
2025-04-23T14:32:29.565009291Z INFO "Initialized 0 authServices." 
2025-04-23T14:32:29.565070176Z INFO "Initialized 2 tools." 
2025-04-23T14:32:29.565120847Z INFO "Initialized 2 toolsets." 
2025-04-23T14:32:29.565510068Z INFO "Server ready to serve!" 
```
7. Run the Agent Locally to verify
- Once the MCP server has started successfully, in another terminal, launch the Agent (from the tech_assistant folder) with command shown below.
```bash
uv run adk web
```
8. Host MCP Toolbox server on Cloud Run
- Launch a new Cloud Shell Terminal or use an existing Cloud Shell Terminal. Go to the mcp-toolbox folder, in which the toolbox binary and tools.yaml are present.
- Set the PROJECT_ID variable to point to your Google Cloud Project Id.

```bash
export PROJECT_ID="YOUR_GOOGLE_CLOUD_PROJECT_ID" 
```
- verify that the following Google Cloud services are enabled in the project.
```bash 
gcloud services enable run.googleapis.com \
                       cloudbuild.googleapis.com \
                       artifactregistry.googleapis.com \
                       iam.googleapis.com \
                       secretmanager.googleapis.com
```
- create a separate service account that will be acting as the identity for the Toolbox service that we will be deploying on Google Cloud Run.
```bash
gcloud iam service-accounts create toolbox-identity

gcloud projects add-iam-policy-binding $PROJECT_ID \
   --member serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com \
   --role roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding $PROJECT_ID \
   --member serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com \
   --role roles/cloudsql.client
```
- Upload the tools.yaml file as a secret and since we have to install the Toolbox in Cloud Run, we are going to use the latest Container image for the toolbox and set that in the IMAGE variable.
```bash
gcloud secrets create tools --data-file=tools.yaml
export IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest 
```
- Deploy to cloud Run
```bash
gcloud run deploy toolbox \
--image $IMAGE \
--service-account toolbox-identity \
--region us-central1 \
--set-secrets "/app/tools.yaml=tools:latest" \
--args="--tools_file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
--allow-unauthenticated
```
You can now visit the Service URL listed in the output in the browser. It should display the "Hello World" message.

9. Deploy the Agent on Cloud Run
- Go to tech_assistant/tech-assistant/agent.py and point to the Toolbox service URL that is running on Cloud Run
```bash
toolbox = ToolboxTool("CLOUD_RUN_SERVICE_URL")
```
- Navigate to the tech_assistant folder and let's set the following environment variables first:

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_GOOGLE_CLOUD_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
export AGENT_PATH="tech-assistant/"
export SERVICE_NAME="praxis"
export APP_NAME="my-tech-assistant"
export GOOGLE_GENAI_USE_VERTEXAI=True
```
- Deploy the Agent Application to Cloud Run via the adk deploy cloud_run command as given below. If you are asked to allow unauthenticated invocations to the service, please provide "y" as the value for now.

```bash
adk deploy cloud_run \
--project=$GOOGLE_CLOUD_PROJECT \
--region=$GOOGLE_CLOUD_LOCATION \
--service_name=$SERVICE_NAME  \
--app_name=$APP_NAME \
--with_ui \
$AGENT_PATH
```

10. Test the Cloud Run Agent

Open the Cloud Run Service URL outputted by the previous step. 
You should see the ADK Web UI for the Praxis- Tech Assistant. 

Test the agent by asking questions like: 
- `I want to build a build a voice chat bot using GCP. How can I do that?` 
- `I want to check status of my support ticket. Ticket id -3` 
- `I am getting 429 error when trying to using gemini models from vertex ai` 
- `I want to create a new support ticket`. 

