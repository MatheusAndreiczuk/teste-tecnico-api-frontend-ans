import pandas as pd
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
    
    def read_file(self, file_path: Path) -> pd.DataFrame:
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    return pd.read_excel(file_path)
                elif file_path.suffix.lower() in ['.csv', '.txt']:
                    separators = [';', ',', '|', '\t']
                    for sep in separators:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
                            if len(df.columns) > 1:
                                return df
                        except:
                            continue
            except Exception as e:
                continue
        
        raise ValueError(f"Não foi possível ler o arquivo: {file_path}")
    
    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        column_mapping = {
            'cnpj': ['cnpj', 'cd_cnpj', 'num_cnpj', 'cnpj_operadora'],
            'razao_social': ['razao_social', 'razao', 'nome', 'nm_razao_social', 'nome_operadora'],
            'valor': ['valor', 'vl_despesa', 'despesa', 'vl_sinistro', 'sinistro', 'valor_despesas'],
            'data': ['data', 'dt_referencia', 'periodo', 'competencia', 'dt_competencia'],
        }
        
        normalized_df = pd.DataFrame()
        
        df.columns = df.columns.str.lower().str.strip()
        
        for standard_col, possible_names in column_mapping.items():
            for col in df.columns:
                if any(name in col for name in possible_names):
                    normalized_df[standard_col] = df[col]
                    break
        
        return normalized_df