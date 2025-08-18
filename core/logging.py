import logging
import sys
import os
import watchtower
import boto3
from typing import Optional

def setup_logging() -> logging.Logger:
    """Configure application logging with CloudWatch integration"""
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Setup CloudWatch logging if credentials are available
    try:
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if aws_access_key_id and aws_secret_access_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=os.getenv("AWS_REGION", "ap-southeast-1"),  
            )
            
            log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "MyFastAPIAppLogs")
            
            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=log_group,
                stream_name=os.getenv("RENDER_SERVICE_ID", "fastapi-service"),
                create_log_group=True,
            )
            
            logging.getLogger().addHandler(cloudwatch_handler)
            
        logger = logging.getLogger(__name__)
        logger.info("Logging setup completed")
        return logger
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to setup CloudWatch logging: {e}")
        return logger