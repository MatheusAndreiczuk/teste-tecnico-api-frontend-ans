import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
from src.etl.validator import validate_cnpj, normalize_cnpj

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
    
    def _extract_quarter(self, date_str) -> str:
        if pd.isna(date_str):
            return 'Q1'
        
        try:
            date_str = str(date_str)
            if 'T' in date_str or len(date_str) > 10:
                date = pd.to_datetime(date_str)
                return f"Q{(date.month - 1) // 3 + 1}"
        except:
            pass
        
        return 'Q1'
    
    def process_files(self, directories: List[Tuple[str, str, Path]]) -> List[Dict]:
        all_data = []
        
        for year, quarter, directory in directories:
            print(f"\nProcessando arquivos de {year}/{quarter}...")
            print(f"Diretório: {directory}")
            
            if not directory.exists():
                print(f"AVISO: Diretório não existe: {directory}")
                continue
            
            files = self.find_despesas_files(directory)
            
            print(f"Encontrados {len(files)} arquivos de despesas")
            
            for file_path in files:
                try:
                    print(f"Lendo: {file_path.name}")
                    df = self.read_file(file_path)
                    print(f"  Shape do arquivo: {df.shape}")
                    print(f"  Primeiras colunas: {list(df.columns)[:10]}")
                    
                    df_normalized = self.normalize_columns(df)
                    print(f"  Colunas normalizadas: {list(df_normalized.columns)}")
                    
                    if 'cnpj' not in df_normalized.columns:
                        print(f"Arquivo ignorado (sem coluna CNPJ após normalização): {file_path.name}")
                        continue
                    
                    for _, row in df_normalized.iterrows():
                        record = {
                            'CNPJ': row.get('cnpj', ''),
                            'RazaoSocial': row.get('razao_social', ''),
                            'Trimestre': quarter if quarter else self._extract_quarter(row.get('data', '')),
                            'Ano': year,
                            'ValorDespesas': row.get('valor', 0),
                            '_source_file': file_path.name
                        }
                        all_data.append(record)
                    
                except Exception as e:
                    print(f"Erro ao processar {file_path.name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        return all_data
    
    def consolidate_data(self, data: List[Dict], output_file: str = "consolidado_despesas.csv") -> pd.DataFrame:
        if len(data) == 0:
            print("\n AVISO: Nenhum dado foi extraído dos arquivos!")
            print("Criando DataFrame vazio para prosseguir")
            df = pd.DataFrame(columns=['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas'])
        else:
            df = pd.DataFrame(data)
        
        print(f"\nTotal de registros antes da limpeza: {len(df)}")
        
        if len(df) == 0:
            print("Nenhum registro para processar. Salvando arquivo vazio.")
            output_path = self.output_dir / output_file
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return df
        
        df['CNPJ'] = df['CNPJ'].apply(lambda x: normalize_cnpj(str(x)) if pd.notna(x) else '')
        
        df = df[df['CNPJ'].str.len() > 0]
        
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
        
        print(f"\nInconsistências encontradas:")
        print(f"- Valores zerados ou negativos: {len(df[df['ValorDespesas'] <= 0])}")
        
        cnpj_duplicates = df.groupby('CNPJ')['RazaoSocial'].nunique()
        print(f"- CNPJs com razões sociais diferentes: {len(cnpj_duplicates[cnpj_duplicates > 1])}")
        
        df_valid_cnpj = df[df['CNPJ'].apply(validate_cnpj)]
        print(f"- CNPJs inválidos removidos: {len(df) - len(df_valid_cnpj)}")
        df = df_valid_cnpj
        
        def get_most_common_razao(group):
            return group['RazaoSocial'].mode()[0] if len(group['RazaoSocial'].mode()) > 0 else group['RazaoSocial'].iloc[0]
        
        razao_mapping = df.groupby('CNPJ').apply(get_most_common_razao).to_dict()
        df['RazaoSocial'] = df['CNPJ'].map(razao_mapping)
        
        df = df[df['ValorDespesas'] > 0]
        
        df = df[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']]
        
        print(f"\nTotal de registros após limpeza: {len(df)}")
        
        output_path = self.output_dir / output_file
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nArquivo consolidado salvo: {output_path}")
        
        import zipfile
        zip_path = self.output_dir / output_file.replace('.csv', '.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(output_path, output_file)
        print(f"Arquivo compactado: {zip_path}")
        
        return df