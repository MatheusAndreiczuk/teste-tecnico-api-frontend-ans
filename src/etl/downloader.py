import requests
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Tuple
import re
from src.core.config import get_settings

settings = get_settings()

class ANSDownloader:
    def __init__(self, download_dir: str = "data/downloads"):
        self.base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis"
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_quarters(self) -> List[Tuple[str, str, str]]:
        print(f"Acessando: {self.base_url}")
        response = requests.get(self.base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        years = []
        for link in soup.find_all('a', href=True):
            href = link['href'].strip('/')
            if re.match(r'^20\d{2}$', href):
                years.append(href)
        
        years = sorted(years, reverse=True)
        print(f"Anos encontrados: {years[:5]}")
        
        quarters = []
        for year in years[:3]:
            year_url = f"{self.base_url}/{year}/"
            print(f"Verificando ano: {year}")
            
            try:
                year_response = requests.get(year_url, timeout=30)
                year_response.raise_for_status()
                year_soup = BeautifulSoup(year_response.content, 'html.parser')
                
                for link in year_soup.find_all('a', href=True):
                    href = link['href']
                    match = re.match(r'(\d)T(20\d{2})\.zip', href)
                    if match:
                        quarter_num = match.group(1)
                        quarter_year = match.group(2)
                        file_url = f"{year_url}{href}"
                        quarters.append((quarter_year, f"{quarter_num}T", file_url))
                        print(f"  Encontrado: {quarter_num}T{quarter_year}")
            except Exception as e:
                print(f"Erro ao acessar {year_url}: {e}")
        
        quarters = sorted(quarters, key=lambda x: (x[0], x[1]), reverse=True)[:3]
        print(f"\nÚltimos 3 trimestres: {[(q[1]+q[0], q[2]) for q in quarters]}")
        return quarters
    
    def download_quarter_files(self, year: str, quarter: str, file_url: str) -> Path:
        filename = f"{quarter}{year}.zip"
        file_path = self.download_dir / filename
        
        if file_path.exists():
            print(f"  Arquivo já existe: {filename}")
            return file_path
        
        print(f"  Baixando: {filename}")
        response = requests.get(file_url, timeout=300, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"    Progresso: {progress:.1f}%", end='\r')
        
        print(f"\n    Download completo: {filename}")
        return file_path
    
    def extract_zip(self, zip_path: Path) -> List[Path]:
        extract_dir = self.download_dir / f"extracted_{zip_path.stem}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  Extraindo: {zip_path.name}")
        
        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                extracted_path = extract_dir / file_info.filename
                zip_ref.extract(file_info, extract_dir)
                if not file_info.is_dir():
                    extracted_files.append(extracted_path)
        
        print(f"  Extraídos {len(extracted_files)} arquivos")
        return extracted_files
