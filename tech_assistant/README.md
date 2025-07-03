# Tech Assistant for Brainstorming & Support- using MCP Toolbox for Databases and Agent Development Kit (ADK)  

## Overview 
Praxis-The Tech Assistant is a sample agent designed to assist with the full lifecycle of technical work—from ideation to resolution. 
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
    ticket_id SERIAL PRIMARY KEY,             AUTO_INCREMENT)
    title VARCHAR(255) NOT NULL,              -- A concise summary or title of the bug/issue.
    description TEXT,                         -- A detailed description of the bug.
    assignee VARCHAR(100),                    -- The name or email of the person/team assigned to the ticket.
    priority VARCHAR(50),                     -- The priority level (e.g., 'P0 - Critical', 'P1 - High').
    status VARCHAR(50) DEFAULT 'Open',        -- The current status of the ticket (e.g., 'Open', 'In Progress', 'Resolved'). Default is 'Open'.
    creation_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the ticket was first created. 'WITH TIME ZONE' is recommended for clarity and compatibility.
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- Timestamp when the ticket was last updated. Will be managed by a trigger.
);
```

### 5 - Load in sample data. 

From Cloud SQL Studio, paste in the following SQL code to load in sample data.

```SQL
INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Login Page Freezes After Multiple Failed Attempts', 'Users are reporting that after 3 failed login attempts, the login page becomes unresponsive and requires a refresh. No specific error message is displayed.', 'samuel.green@example.com', 'P0 - Critical', 'Open');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Dashboard Sales Widget Intermittent Data Loading Failure', 'The "Sales Overview" widget on the main dashboard intermittently shows a loading spinner but no data. Primarily affects Chrome browser users.', 'maria.rodriguez@example.com', 'P1 - High', 'In Progress');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Broken Link in Footer - Privacy Policy', 'The "Privacy Policy" hyperlink located in the website footer leads to a 404 "Page Not Found" error.', 'maria.rodriguez@example.com', 'P3 - Low', 'Resolved');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('UI Misalignment on Mobile Landscape View (iOS)', 'On specific iOS devices (e.g., iPhone 14 models), the top navigation bar shifts downwards when the device is viewed in landscape orientation, obscuring content.', 'maria.rodriguez@example.com', 'P2 - Medium', 'In Progress');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Critical XZ Utils Backdoor Detected in Core Dependency (CVE-2024-3094)', 'Urgent: A sophisticated supply chain compromise (CVE-2024-3094) has been identified in XZ Utils versions 5.6.0 and 5.6.1. This malicious code potentially allows unauthorized remote SSH access by modifying liblzma. Immediate investigation and action required for affected Linux/Unix systems and services relying on XZ Utils.', 'frank.white@example.com', 'P0 - Critical', 'Open');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Database Connection Timeouts During Peak Usage', 'The application is experiencing frequent database connection timeouts, particularly during peak hours (10 AM - 12 PM EDT), affecting all users and causing service interruptions.', 'frank.white@example.com', 'P1 - High', 'Open');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Export to PDF Truncates Long Text Fields in Reports', 'When generating PDF exports of reports containing extensive text fields, the text is abruptly cut off at the end of the page instead of wrapping or continuing to the next page.', 'samuel.green@example.com', 'P1 - High', 'Open');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Search Filter "Date Range" Not Applying Correctly', 'The "Date Range" filter on the search results page does not filter records accurately; results outside the specified date range are still displayed.', 'samuel.green@example.com', 'P2 - Medium', 'Resolved');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Typo in Error Message: "Unathorized Access"', 'The error message displayed when a user attempts an unauthorized action reads "Unathorized Access" instead of "Unauthorized Access."', 'maria.rodriguez@example.com', 'P3 - Low', 'Resolved');

INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Intermittent File Upload Failures for Large Files', 'Users are intermittently reporting that file uploads fail without a clear error message or explanation, especially for files exceeding 10MB in size.', 'frank.white@example.com', 'P1 - High', 'Open');
```

### 6 - Create a trigger to update the `updated_time` field when a record is updated.

```SQL
CREATE OR REPLACE FUNCTION update_updated_time_tickets()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = NOW();  -- Set the updated_time to the current timestamp
    RETURN NEW;                -- Return the new row
END;
$$ language 'plpgsql';        

CREATE TRIGGER update_tickets_updated_time
BEFORE UPDATE ON tickets
FOR EACH ROW                  -- This means the trigger fires for each row affected by the UPDATE statement
EXECUTE PROCEDURE update_updated_time_tickets();
```


### 7 - Create vector embeddings from the `description` field.

```SQL
ALTER TABLE tickets ADD COLUMN embedding vector(768) GENERATED ALWAYS AS (embedding('text-embedding-005',description)) STORED;
```

### 8 - Verify that the database is ready.

From Cloud SQL studio, run:

```SQL
SELECT * FROM tickets;
```

You should see: 

<img src="deployment/images/verify-db.png" width="80%" alt="Verify database table">


### 9 - Deploy the MCP Toolbox for Databases server to Cloud Run 

Now that we have a Cloud SQL database, we can deploy the MCP Toolbox for Databases server to Cloud Run and point it at our Cloud SQL instance.

First, update `deployment/mcp-toolbox/tools.yaml` for your Cloud SQL instance: 

```yaml
  postgresql:
    kind: cloud-sql-postgres
    project: ${PROJECT_ID}
    region: us-central1
    instance: software-assistant
    database: tickets-db
    user: ${DB_USER}
    password: ${DB_PASS}
```

Then, configure Toolbox's Cloud Run service account to access both Secret Manager and Cloud SQL. Secret Manager is where we'll store our `tools.yaml` file because it contains sensitive Cloud SQL credentials. 

Note - run this from the top-level `software-bug-assistant/` directory. 

```bash 
gcloud services enable run.googleapis.com \
   cloudbuild.googleapis.com \
   artifactregistry.googleapis.com \
   iam.googleapis.com \
   secretmanager.googleapis.com
                       
gcloud iam service-accounts create toolbox-identity

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com \
    --role roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member serviceAccount:toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com \
    --role roles/cloudsql.client

gcloud secrets create tools --data-file=deployment/mcp-toolbox/tools.yaml
```

Now we can deploy Toolbox to Cloud Run. We'll use the latest [release version](https://github.com/googleapis/genai-toolbox/releases) of the MCP Toolbox image (we don't need to build or deploy the `toolbox` from source.)

```bash
gcloud run deploy toolbox \
    --image us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
    --service-account toolbox-identity \
    --region us-central1 \
    --set-secrets "/app/tools.yaml=tools:latest" \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,DB_USER=postgres,DB_PASS=admin" \
    --args="--tools-file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
    --allow-unauthenticated
```

Verify that the Toolbox is running by getting the Cloud Run logs: 

```bash 
gcloud run services logs read toolbox --region us-central1
```

You should see: 

```bash
2025-05-15 18:03:55 2025-05-15T18:03:55.465847801Z INFO "Initialized 1 sources."
2025-05-15 18:03:55 2025-05-15T18:03:55.466152914Z INFO "Initialized 0 authServices."
2025-05-15 18:03:55 2025-05-15T18:03:55.466374245Z INFO "Initialized 9 tools."
2025-05-15 18:03:55 2025-05-15T18:03:55.466477938Z INFO "Initialized 2 toolsets."
2025-05-15 18:03:55 2025-05-15T18:03:55.467492303Z INFO "Server ready to serve!"
```

Save the Cloud Run URL for the Toolbox service as an environment variable.

```bash
export MCP_TOOLBOX_URL=$(gcloud run services describe toolbox --region us-central1 --format "value(status.url)")
```

Now we are ready to deploy the ADK Python agent to Cloud Run! :rocket:

### 10 - Create an Artifact Registry repository.

This is where we'll store the agent container image.

```bash
gcloud artifacts repositories create adk-samples \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repository for ADK Python sample agents" \
  --project=$PROJECT_ID
```

### 11 - Containerize the ADK Python agent. 

Build the container image and push it to Artifact Registry with Cloud Build.

```bash
gcloud builds submit --region=us-central1 --tag us-central1-docker.pkg.dev/$PROJECT_ID/adk-samples/software-bug-assistant:latest
```

### 12 - Deploy the agent to Cloud Run 


> [!NOTE]    
> 
> If you are using Vertex AI instead of AI Studio for Gemini calls, you will need to replace `GOOGLE_API_KEY` with `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and `GOOGLE_GENAI_USE_VERTEXAI=TRUE` in the last line of the below `gcloud run deploy` command.
> 
> ```bash
> --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_TOOLBOX_URL=$MCP_TOOLBOX_URL,GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN
> ```

```bash
gcloud run deploy software-bug-assistant \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/adk-samples/software-bug-assistant:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars=GOOGLE_API_KEY=$GOOGLE_API_KEY,MCP_TOOLBOX_URL=$MCP_TOOLBOX_URL,GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN 
```

When this runs successfully, you should see: 

```bash
Service [software-bug-assistant] revision [software-bug-assistant-00001-d4s] has been deployed and is serving 100 percent of traffic.
```


### 13 - Test the Cloud Run Agent

Open the Cloud Run Service URL outputted by the previous step. 

You should see the ADK Web UI for the Software Bug Assistant. 

Test the agent by asking questions like: 
- `Any issues around database timeouts?` 
- `How many bugs are assigned to samuel.green@example.com? Show a table.` 
- `What are some possible root-causes for the unresponsive login page issue?` (Invoke Google Search tool)
- `Get the bug ID for the unresponsive login page issues` --> `Boost that bug's priority to P0.`. 
- `Create a new bug.` (let the agent guide you through bug creation)

*Example workflow*: 

![](deployment/images/cloud-run-example.png)


### Clean up 

You can clean up this agent sample by: 
- Deleting the [Artifact Registry](https://console.cloud.google.com/artifacts). 
- Deleting the two [Cloud Run Services](https://console.cloud.google.com/run). 
- Deleting the [Cloud SQL instance](https://console.cloud.google.com/sql/instances). 
- Deleting the [Secret Manager secret](https://console.cloud.google.com/security/secret-manager). 
