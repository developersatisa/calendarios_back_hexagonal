import os
from app.domain.services.document_storage_port import DocumentStoragePort
from app.config import settings

class LocalFileStorage(DocumentStoragePort):
    def __init__(self):
        self.root = settings.FILE_STORAGE_ROOT

    def save(self, cif: str, filename: str, content: bytes) -> str:
        cif = cif.strip()
        dir_path = os.path.join(self.root, cif)
        
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return filename

    def delete(self, cif: str, stored_name: str) -> None:
        cif = cif.strip()
        file_path = os.path.join(self.root, cif, stored_name)
        if os.path.exists(file_path):
            os.remove(file_path)
