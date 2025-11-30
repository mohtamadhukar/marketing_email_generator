# Deployment Guide: Vertex AI Agent Engine

This guide walks you through deploying your email generation agent to Vertex AI Agent Engine.

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Project**
   - A Google Cloud project with billing enabled
   - Project ID ready (you'll need this for deployment)

2. **Required APIs Enabled**
   - Vertex AI API
   - Cloud Storage API
   
   Enable them using:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage-component.googleapis.com
   ```

3. **Authentication**
   Authenticate your local environment:
   ```bash
   gcloud auth application-default login
   ```

4. **Python Environment**
   - Python 3.9 or higher
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

## Deployment Steps

### Step 1: Install Dependencies

Make sure all required packages are installed:

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables (Optional)

You can configure deployment settings via a `.env` file or command-line arguments. Command-line arguments take precedence over `.env` values.

**Create a `.env` file** (optional, but recommended):
```bash
# Required (or provide via --project-id)
GCP_PROJECT_ID=your-project-id

# Optional (defaults shown)
GCP_REGION=us-central1
AGENT_NAME=email-generator-agent
TEST_AFTER_DEPLOY=false
TEST_MESSAGE=Start creating the emails using pre-defined briefs and show them for approval or rejection
```

**Environment Variables:**
- `GCP_PROJECT_ID` or `PROJECT_ID`: Google Cloud Project ID (required if not in command line)
- `GCP_REGION` or `REGION`: GCP region (default: `us-central1`)
- `AGENT_NAME`: Custom name for the deployed agent
- `TEST_AFTER_DEPLOY`: Set to `"true"` to automatically test after deployment
- `TEST_MESSAGE`: Custom test message (used with `--test` flag)

**Note:** The agent also reads `DATA_ROOT_FOLDER` for data file paths (defaults to `./data` if not set). For deployment, the data files will be packaged with the agent.

### Step 3: Deploy to Vertex AI

Use the deployment script. You can use `.env` file, command-line arguments, or both:

**Option 1: Using .env file (recommended)**
```bash
# Create .env file with GCP_PROJECT_ID, then:
python deploy.py
```

**Option 2: Using command-line arguments**
```bash
python deploy.py --project-id YOUR_PROJECT_ID --region us-central1
```

**Option 3: Mix of both (command-line overrides .env)**
```bash
# Uses GCP_PROJECT_ID from .env, but overrides region
python deploy.py --region us-east1
```

**Command-line Parameters:**
- `--project-id` (required if not in .env): Your Google Cloud Project ID
- `--region` (optional): GCP region (default: from .env or `us-central1`)
- `--agent-name` (optional): Custom name for your deployed agent
- `--test` (optional): Test the agent after deployment
- `--test-message` (optional): Custom test message (used with `--test`)

**Examples:**
```bash
# Full command-line example
python deploy.py \
  --project-id my-email-agent-project \
  --region us-central1 \
  --agent-name email-generator-prod \
  --test

# Using .env file (simpler)
python deploy.py

# Override just the region from .env
python deploy.py --region us-east1
```

### Step 4: Verify Deployment

After deployment, you should see:
- ✅ Deployment successful message
- Agent Engine ID
- Next steps for testing

## Testing Your Deployed Agent

### Option 1: Using the Deployment Script

Add the `--test` flag when deploying:
```bash
python deploy.py --project-id YOUR_PROJECT_ID --test
```

### Option 2: Using Python Code

```python
from vertexai import agent_engines

# Get your deployed agent
remote_agent = agent_engines.get("projects/YOUR_PROJECT_ID/locations/us-central1/agentEngines/YOUR_AGENT_ID")

# Test with async streaming
import asyncio

async def test_agent():
    async for event in remote_agent.async_stream_query(
        user_id="test_user",
        message="Start creating the emails using pre-defined briefs and show them for approval or rejection"
    ):
        print(event)

asyncio.run(test_agent())
```

### Option 3: Using Vertex AI Console

1. Go to [Vertex AI Console](https://console.cloud.google.com/vertex-ai)
2. Navigate to **Agent Builder** > **Agent Engines**
3. Find your deployed agent
4. Use the test interface to interact with your agent

## Managing Your Deployment

### List Deployed Agents

```python
from vertexai import agent_engines

# List all agent engines in your project
agents = agent_engines.list()
for agent in agents:
    print(f"Agent: {agent.name}")
```

### Get Agent Details

```python
from vertexai import agent_engines

# Get specific agent
agent = agent_engines.get("projects/YOUR_PROJECT_ID/locations/us-central1/agentEngines/YOUR_AGENT_ID")
print(agent)
```

### Update/Re-deploy

To update your agent, simply run the deployment script again with the same parameters. This will create a new version of your agent.

## Monitoring and Observability

### Vertex AI Console

Monitor your agent in the [Vertex AI Console](https://console.cloud.google.com/vertex-ai):
- View agent performance metrics
- Check logs and errors
- Monitor token usage and latency
- Track tool call statistics

### Key Metrics to Monitor

- **Token Usage**: Track input/output tokens per request
- **Latency**: Monitor response times
- **Error Rate**: Track failed requests
- **Tool Calls**: Monitor function tool invocations
- **User Sessions**: Track active user sessions

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Error: Could not automatically determine credentials
   ```
   **Solution**: Run `gcloud auth application-default login`

2. **Permission Denied**
   ```
   Error: Permission denied on resource
   ```
   **Solution**: Ensure you have the required IAM roles (`roles/aiplatform.user`, `roles/storage.admin`)

3. **API Not Enabled**
   ```
   Error: API not enabled
   ```
   **Solution**: Enable Vertex AI API:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

4. **Data File Not Found**
   ```
   Error: FileNotFoundError: initial_state.json
   ```
   **Solution**: Ensure `data/initial_state.json` exists in your project directory. The deployment script packages all files in the project.

5. **Deployment Timeout**
   ```
   Error: Deployment taking too long
   ```
   **Solution**: 
   - Check your network connection
   - Verify billing is enabled
   - Check Cloud Storage quota

### Getting Help

- Check [Vertex AI Agent Builder Documentation](https://docs.cloud.google.com/agent-builder/agent-engine/deploy)
- Review [ADK Quickstart Guide](https://docs.cloud.google.com/agent-builder/agent-engine/quickstart-adk)
- Check deployment logs in Cloud Logging

## Production Considerations

### Security

1. **Service Account**: Use a service account instead of user credentials for production
2. **IAM**: Follow principle of least privilege
3. **Data**: Ensure sensitive data is properly handled
4. **Secrets**: Use Secret Manager for API keys and credentials

### Performance

1. **Caching**: Consider implementing response caching for common queries
2. **Rate Limiting**: Implement rate limiting for production workloads
3. **Monitoring**: Set up alerts for error rates and latency
4. **Scaling**: Vertex AI Agent Engine handles scaling automatically

### Cost Optimization

1. **Model Selection**: Use appropriate model sizes (e.g., `gemini-2.5-flash-lite` for cost efficiency)
2. **Token Usage**: Monitor and optimize token consumption
3. **Caching**: Cache responses to reduce API calls
4. **Quotas**: Set up quotas to control costs

## Next Steps

After successful deployment:

1. **Integrate with Your Application**
   - Use the agent_engines API to integrate with your frontend/backend
   - Implement proper error handling and retries
   - Add authentication and authorization

2. **Set Up Monitoring**
   - Configure Cloud Monitoring dashboards
   - Set up alerts for errors and performance issues
   - Track business metrics (email generation success rate, etc.)

3. **Optimize Performance**
   - Monitor token usage and optimize prompts
   - Implement caching where appropriate
   - Fine-tune agent instructions based on usage patterns

4. **Scale for Production**
   - Test with expected load
   - Set up proper error handling
   - Implement logging and observability

## Additional Resources

- [Vertex AI Agent Builder Documentation](https://docs.cloud.google.com/agent-builder)
- [ADK Documentation](https://cloud.google.com/vertex-ai/docs/adk)
- [Vertex AI Python SDK](https://cloud.google.com/vertex-ai/docs/python-sdk)
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/using-iam-securely)

