"""
Deployment Script for Vertex AI Agent Engine

This script deploys the email generation agent to Vertex AI Agent Engine.
It packages the agent, uploads it to Cloud Storage, and creates a deployable agent engine.

Usage:
    # Using command-line arguments:
    python deploy.py --project-id YOUR_PROJECT_ID --region us-central1
    
    # Using .env file (create .env with GCP_PROJECT_ID, GCP_REGION, etc.):
    python deploy.py
    
    # Mix of both (command-line overrides .env):
    python deploy.py --region us-east1  # Uses GCP_PROJECT_ID from .env, but overrides region

Environment Variables (optional, used as defaults):
    GCP_PROJECT_ID or PROJECT_ID    Google Cloud Project ID (required if not in command line)
    GCP_REGION or REGION             GCP region (default: us-central1)
    AGENT_NAME                       Custom name for the deployed agent
    TEST_AFTER_DEPLOY                Set to "true" to test after deployment
    TEST_MESSAGE                     Custom test message (used with --test flag)

Requirements:
    - Google Cloud Project with Vertex AI API enabled
    - Authenticated gcloud CLI (gcloud auth application-default login)
    - Required IAM roles: Vertex AI User, Storage Admin
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Import the root agent from the basic module
from basic.agent import root_agent

import vertexai

# Load environment variables from .env file
load_dotenv()


def deploy_agent(project_id: str, region: str, agent_name: str = None):
    """
    Deploy the email generation agent to Vertex AI Agent Engine.
    
    Args:
        project_id: Google Cloud Project ID
        region: GCP region for deployment (e.g., 'us-central1')
        agent_name: Optional custom name for the deployed agent
    """
    # Set default agent name if not provided
    if not agent_name:
        agent_name = "email-generator-agent"
    
    print(f"🚀 Starting deployment to Vertex AI Agent Engine...")
    print(f"   Project ID: {project_id}")
    print(f"   Region: {region}")
    print(f"   Agent Name: {agent_name}")
    print()
    
    # Initialize Vertex AI
    # Set environment variables for Vertex AI
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_REGION"] = region
    
    # Get staging bucket from environment if available
    staging_bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    try:
        init_kwargs = {
            "project": project_id,
            "location": region,
        }
        if staging_bucket:
            init_kwargs["staging_bucket"] = f"gs://{staging_bucket}"
        
        vertexai.init(**init_kwargs)
        print(f"✅ Initialized Vertex AI in project {project_id}, region {region}")
        if staging_bucket:
            print(f"   Staging bucket: gs://{staging_bucket}")
    except Exception as e:
        print(f"⚠️  Vertex AI initialization warning: {e}")
        print(f"   Continuing - agent_engines may handle initialization automatically")
    
    # Create ADK App wrapper
    try:
        print("📦 Creating ADK App wrapper...")
        app = AdkApp(
            agent=root_agent,
            enable_tracing=True,
        )
        print("✅ ADK App wrapper created")
    except Exception as e:
        print(f"❌ Failed to create ADK App: {e}")
        sys.exit(1)
    
    # Deploy the agent
    try:
        print("🚀 Deploying agent to Vertex AI Agent Engine...")
        print("   This may take a few minutes...")
        
        # Read requirements from requirements.txt
        requirements_path = Path(__file__).parent / "requirements.txt"
        requirements = []
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        # Deploy
        remote_agent = agent_engines.create(
            app,
            display_name=agent_name,
            description="Personalized Email Generator Agent",
            requirements=requirements,
            extra_packages=[
                "./basic",  # The main package
            ],
        )
        
        print()
        print("✅ Deployment successful!")
        print(f"   Agent Engine ID: {remote_agent.name}")
        print()
        print("📝 Next steps:")
        print("   1. Test your agent using the Vertex AI console")
        print("   2. Use the agent_engines API to interact with your agent")
        print("   3. Monitor performance in the Vertex AI dashboard")
        print()
        
        return remote_agent
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        print()
        print("💡 Troubleshooting tips:")
        print("   - Ensure Vertex AI API is enabled in your project")
        print("   - Check that you have the required IAM roles")
        print("   - Verify your gcloud authentication: gcloud auth application-default login")
        print("   - Check that billing is enabled for your project")
        sys.exit(1)


def test_agent(remote_agent, test_message: str = None):
    """
    Test the deployed agent with a sample message.
    
    Args:
        remote_agent: The deployed agent engine instance
        test_message: Optional test message (defaults to a sample prompt)
    """
    if not test_message:
        test_message = "Start creating the emails using pre-defined briefs and show them for approval or rejection"
    
    print(f"🧪 Testing deployed agent...")
    print(f"   Test message: {test_message}")
    print()
    
    try:
        import asyncio
        
        async def run_test():
            async for event in remote_agent.async_stream_query(
                user_id="test_user",
                message=test_message,
            ):
                print(event)
        
        asyncio.run(run_test())
        print()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("   Note: You can still test the agent via the Vertex AI console")


def main():
    """Main entry point for the deployment script."""
    # Get defaults from environment variables
    default_project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    default_region = os.getenv("GCP_REGION") or os.getenv("REGION") or "us-central1"
    default_agent_name = os.getenv("AGENT_NAME")
    default_test_message = os.getenv("TEST_MESSAGE")
    
    parser = argparse.ArgumentParser(
        description="Deploy email generation agent to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables (used as defaults if not provided via command line):
  GCP_PROJECT_ID or PROJECT_ID    Google Cloud Project ID
  GCP_REGION or REGION             GCP region (default: us-central1)
  AGENT_NAME                       Custom name for the deployed agent
  TEST_MESSAGE                     Custom test message (used with --test flag)

Example .env file:
  GCP_PROJECT_ID=my-project-id
  GCP_REGION=us-central1
  AGENT_NAME=email-generator-prod
        """
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=default_project_id,
        required=not bool(default_project_id),
        help=f"Google Cloud Project ID (default: from .env GCP_PROJECT_ID or PROJECT_ID)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=default_region,
        help=f"GCP region for deployment (default: {default_region} from .env or us-central1)",
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default=default_agent_name,
        help="Custom name for the deployed agent (default: from .env AGENT_NAME or 'email-generator-agent')",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        default=os.getenv("TEST_AFTER_DEPLOY", "").lower() in ("true", "1", "yes"),
        help="Test the deployed agent after deployment (default: from .env TEST_AFTER_DEPLOY)",
    )
    parser.add_argument(
        "--test-message",
        type=str,
        default=default_test_message,
        help="Custom test message (only used with --test flag, default: from .env TEST_MESSAGE)",
    )
    
    args = parser.parse_args()
    
    # Deploy the agent
    remote_agent = deploy_agent(
        project_id=args.project_id,
        region=args.region,
        agent_name=args.agent_name,
    )
    
    # Test if requested
    if args.test:
        print()
        test_agent(remote_agent, args.test_message)


if __name__ == "__main__":
    main()

