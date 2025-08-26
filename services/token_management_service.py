import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

class TokenManagementService:
    """
    Service quản lý Zalo token lifecycle và Render environment updates
    """
    
    async def refresh_zalo_access_token(self):
        """
        Gọi Zalo API để refresh access token từ refresh token
        """
        if not all([settings.zalo_oa_refresh_token, settings.zalo_app_id, settings.zalo_secret_key]):
            return {
                "success": False,
                "message": "Missing Zalo configuration: refresh_token, app_id, or secret_key"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://oauth.zaloapp.com/v4/oa/access_token",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "secret_key": settings.zalo_secret_key
                    },
                    data={
                        "refresh_token": settings.zalo_oa_refresh_token,
                        "app_id": str(settings.zalo_app_id),
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Zalo API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message": f"Zalo API error: {response.status_code}"
                    }
                
                data = response.json()
                
                if "access_token" not in data:
                    logger.error(f"Invalid Zalo response: {data}")
                    return {
                        "success": False,
                        "message": "Invalid response from Zalo API"
                    }
                
                logger.info("Successfully refreshed Zalo access token")
                return {
                    "success": True,
                    "access_token": data["access_token"],
                    "refresh_token": data.get("refresh_token", settings.zalo_oa_refresh_token),
                    "expires_in": data.get("expires_in", "90000")
                }
                
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return {
                "success": False,
                "message": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    async def update_render_env_vars(self, access_token: str, refresh_token: str):
        """
        Update Zalo tokens trong Render environment variables
        """
        if not settings.render_service_id:
            return {
                "success": False,
                "message": "Missing render_service_id configuration"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Update access token
                access_response = await client.put(
                    f"https://api.render.com/v1/services/{settings.render_service_id}/env-vars/ZALO_OA_ACCESS_TOKEN",
                    headers={
                        "accept": "application/json",
                        "content-type": "application/json",
                        "authorization": f"Bearer {settings.render_api_key}" if settings.render_api_key else ""
                    },
                    json={"value": access_token}
                )
                
                # Update refresh token
                refresh_response = await client.put(
                    f"https://api.render.com/v1/services/{settings.render_service_id}/env-vars/ZALO_OA_REFRESH_TOKEN",
                    headers={
                        "accept": "application/json", 
                        "content-type": "application/json",
                        "authorization": f"Bearer {settings.render_api_key}" if settings.render_api_key else ""
                    },
                    json={"value": refresh_token}
                )
                
                if access_response.status_code not in [200, 201]:
                    logger.error(f"Failed to update access token: {access_response.status_code} - {access_response.text}")
                    return {
                        "success": False,
                        "message": f"Failed to update access token: {access_response.status_code}"
                    }
                
                if refresh_response.status_code not in [200, 201]:
                    logger.error(f"Failed to update refresh token: {refresh_response.status_code} - {refresh_response.text}")
                    return {
                        "success": False,
                        "message": f"Failed to update refresh token: {refresh_response.status_code}"
                    }
                
                logger.info("Successfully updated Render environment variables")
                return {
                    "success": True,
                    "message": "Environment variables updated successfully",
                    "updated_at": "now"
                }
                
        except httpx.RequestError as e:
            logger.error(f"Failed to update Render env vars: {e}")
            return {
                "success": False,
                "message": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error updating env vars: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    async def refresh_tokens_with_env_update(self):
        """
        Orchestration method: refresh tokens và update environment
        Được gọi bởi cron worker và manual API endpoint
        """
        logger.info("Starting automatic Zalo token refresh...")
        
        try:
            # 1. Refresh token
            token_result = await self.refresh_zalo_access_token()
            if not token_result["success"]:
                logger.error(f"Token refresh failed: {token_result['message']}")
                return {
                    "success": False,
                    "message": token_result["message"],
                    "step": "refresh_token"
                }
            
            # 2. Update Render env vars
            env_result = await self.update_render_env_vars(
                token_result["access_token"],
                token_result["refresh_token"] 
            )
            
            if not env_result["success"]:
                logger.error(f"Env update failed: {env_result['message']}")
                return {
                    "success": False,
                    "message": env_result["message"],
                    "step": "update_environment",
                    "token_data": token_result  # Token refresh thành công nhưng update env failed
                }
                
            logger.info("Token refresh and environment update completed successfully")
            return {
                "success": True,
                "message": "Token refreshed and environment updated successfully",
                "token_expires_in": token_result.get("expires_in"),
                "updated_at": env_result.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Token management error: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "step": "unknown"
            }

# Global service instance - Dependency Injection pattern
def get_token_management_service() -> TokenManagementService:
    """Factory function để tạo service instance"""
    return TokenManagementService()
