from pathlib import Path
from typing import List

class ANSProcessor:
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_despesas_files(self, file_paths: List[Path]) -> List[Path]:
        despesas_keywords = [
            'despesa', 'sinistro', 'evento', 'exhibit', 'demonstração',
            'DESPESA', 'SINISTRO', 'EVENTO', 'EXHIBIT', 'DEMONSTRAÇÃO'
        ]
        
        files = []
        print(f"  Analisando {len(file_paths)} arquivos...")
        
        for file_path in file_paths:
            if not file_path.exists() or file_path.is_dir():
                continue
            
            filename = file_path.name.lower()
            has_valid_ext = any(ext in filename for ext in ['.csv', '.txt', '.xlsx', '.xls'])
            has_keyword = any(keyword.lower() in filename for keyword in despesas_keywords)
            
            if has_valid_ext and has_keyword:
                files.append(file_path)
                print(f"    {file_path.name}")
        
        print(f"  Arquivos de despesas encontrados: {len(files)}")
        return files