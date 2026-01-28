from typing import Optional, Dict, Any
import msal
from app.config import settings

class SSOService:
    def __init__(self):
        self.client_id = settings.CLIENT_ID
        self.client_secret = settings.CLIENT_SECRET
        self.tenant_id = settings.TENANT_ID
        self.redirect_uri = settings.REDIRECT_URI
        
        # Validar que las credenciales SSO estén configuradas
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            raise ValueError("SSO no está configurado. Faltan variables: CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI")
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["User.Read"]
        
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_auth_url(self) -> str:
        """Genera la URL de autenticación para redirigir al usuario"""
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scope,
            redirect_uri=self.redirect_uri
        )
        return auth_url
    
    def get_token_from_code(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Intercambia el código de autorización por un token de acceso"""
        try:
            result = self.app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=self.scope,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                return result
            else:
                print(f"Error getting token: {result.get('error_description', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Exception in get_token_from_code: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene información del usuario usando el token de acceso"""
        import requests
        
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting user info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception in get_user_info: {str(e)}")
            return None