import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
from src.etl.validator import validate_cnpj, normalize_cnpj
from bs4 import BeautifulSoup
import requests
import re
import zipfile

class ANSProcessor:
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_despesas_files(self, file_paths: List[Path]) -> List[Tuple[str, str, Path]]:
        files = []
        print(f"  Analisando {len(file_paths)} arquivos...")
        
        for file_path in file_paths:
            if not file_path.exists() or file_path.is_dir():
                continue
            
            filename = file_path.name
            if not filename.lower().endswith(('.csv', '.txt', '.xlsx', '.xls')):
                continue
            
            match = re.match(r'(\d)T(\d{4})', filename)
            if match:
                quarter = f"{match.group(1)}T"
                year = match.group(2)
                files.append((year, quarter, file_path))
                print(f"    {filename} -> {quarter}{year}")
            else:
                files.append(('', '', file_path))
                print(f"    {filename}")
        
        print(f"  Arquivos para processar: {len(files)}")
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
    
    def _filter_eventos_sinistros(self, df: pd.DataFrame) -> pd.DataFrame:
        keywords = ['EVENTO', 'SINISTRO']
        
        if 'DESCRICAO' not in df.columns:
            return df
        
        mask = df['DESCRICAO'].astype(str).str.upper().apply(
            lambda x: any(kw in x for kw in keywords)
        )
        return df[mask]
    
    def process_files(self, data_files: List[Tuple[str, str, Path]]) -> List[Dict]:
        all_data = []
        
        for year, quarter, file_path in data_files:
            try:
                print(f"  Lendo: {file_path.name}")
                df = self.read_file(file_path)
                print(f"    Shape original: {df.shape}")
                
                df.columns = df.columns.str.upper().str.strip()
                
                df_eventos = self._filter_eventos_sinistros(df)
                print(f"    Registros de eventos/sinistros: {len(df_eventos)}")
                
                if len(df_eventos) == 0:
                    continue
                
                reg_col = None
                for col in df_eventos.columns:
                    if 'REG' in col and 'ANS' in col:
                        reg_col = col
                        break
                    if col == 'REG_ANS':
                        reg_col = col
                        break
                
                if not reg_col:
                    print(f"    Coluna REG_ANS não encontrada, pulando...")
                    continue
                
                valor_col = None
                for col in df_eventos.columns:
                    if 'SALDO_FINAL' in col or 'VL_SALDO_FINAL' in col:
                        valor_col = col
                        break
                    if 'VALOR' in col:
                        valor_col = col
                        break
                
                if not valor_col:
                    print(f"    Coluna de valor não encontrada, pulando...")
                    continue
                
                for _, row in df_eventos.iterrows():
                    record = {
                        'REG_ANS': str(row[reg_col]).strip(),
                        'Trimestre': quarter,
                        'Ano': year,
                        'ValorDespesas': row[valor_col],
                        'Descricao': row.get('DESCRICAO', '')
                    }
                    all_data.append(record)
                    
            except Exception as e:
                print(f"    Erro ao processar {file_path.name}: {str(e)}")
                continue
        
        print(f"\n  Total de registros extraídos: {len(all_data)}")
        return all_data
    
    def consolidate_data(self, data: List[Dict], output_file: str = "consolidado_despesas.csv") -> pd.DataFrame:
        if len(data) == 0:
            print("\n AVISO: Nenhum dado foi extraído dos arquivos!")
            df = pd.DataFrame(columns=['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas'])
            output_path = self.output_dir / output_file
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return df
        
        df = pd.DataFrame(data)
        
        print(f"\nTotal de registros antes da limpeza: {len(df)}")
        
        df['REG_ANS'] = df['REG_ANS'].astype(str).str.strip()
        df = df[df['REG_ANS'].str.len() > 0]
        df = df[df['REG_ANS'] != 'nan']
        
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
        
        print(f"\nInconsistências encontradas:")
        zeros_negativos = len(df[df['ValorDespesas'] <= 0])
        print(f"- Valores zerados ou negativos: {zeros_negativos}")
        
        df = df[df['ValorDespesas'] > 0]
        
        df_agg = df.groupby(['REG_ANS', 'Trimestre', 'Ano']).agg({
            'ValorDespesas': 'sum'
        }).reset_index()
        
        print(f"\nBaixando cadastro para enriquecer dados...")
        cadastro_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
        response = requests.get(cadastro_url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        csv_link = None
        for link in soup.find_all('a', href=True):
            if '.csv' in link['href'].lower():
                csv_link = cadastro_url + link['href']
                break
        
        if csv_link:
            df_cadastro = pd.read_csv(csv_link, encoding='latin1', sep=';', low_memory=False)
            df_cadastro.columns = df_cadastro.columns.str.strip()
            
            df_cadastro['REG_ANS'] = df_cadastro['Registro_ANS'].astype(str).str.strip() if 'Registro_ANS' in df_cadastro.columns else df_cadastro['REGISTRO_OPERADORA'].astype(str).str.strip()
            df_cadastro['CNPJ'] = df_cadastro['CNPJ'].apply(lambda x: normalize_cnpj(str(x)) if pd.notna(x) else '')
            df_cadastro['RazaoSocial'] = df_cadastro['Razao_Social'] if 'Razao_Social' in df_cadastro.columns else ''
            
            df_cadastro_clean = df_cadastro[['REG_ANS', 'CNPJ', 'RazaoSocial']].drop_duplicates(subset=['REG_ANS'], keep='first')
            
            df_merged = df_agg.merge(df_cadastro_clean, on='REG_ANS', how='left')
            
            sem_match = df_merged['CNPJ'].isna().sum()
            print(f"- Registros sem match no cadastro: {sem_match}")
            
            df_merged = df_merged[df_merged['CNPJ'].notna()]
            df_merged = df_merged[df_merged['CNPJ'].str.len() > 0]
            
            df_valid = df_merged[df_merged['CNPJ'].apply(validate_cnpj)]
            invalidos = len(df_merged) - len(df_valid)
            print(f"- CNPJs inválidos removidos: {invalidos}")
            df_merged = df_valid
            
            cnpj_razoes = df_merged.groupby('CNPJ')['RazaoSocial'].nunique()
            duplicados = len(cnpj_razoes[cnpj_razoes > 1])
            print(f"- CNPJs com razões sociais diferentes: {duplicados}")
        else:
            df_merged = df_agg.copy()
            df_merged['CNPJ'] = ''
            df_merged['RazaoSocial'] = ''
        
        df_final = df_merged[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']]
        
        print(f"\nTotal de registros após limpeza: {len(df_final)}")
        
        output_path = self.output_dir / output_file
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nArquivo consolidado salvo: {output_path}")
        
        zip_path = self.output_dir / output_file.replace('.csv', '.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(output_path, output_file)
        print(f"Arquivo compactado: {zip_path}")
        
        return df_final
    
    def download_operadoras_cadastro(self, output_file: str = "operadoras_cadastro.csv") -> Path:
        cadastro_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
        
        response = requests.get(cadastro_url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        csv_link = None
        for link in soup.find_all('a', href=True):
            if '.csv' in link['href'].lower():
                csv_link = cadastro_url + link['href']
                break
        
        if not csv_link:
            raise ValueError("Arquivo CSV de cadastro não encontrado")
        
        print(f"Baixando cadastro de operadoras: {csv_link}")
        
        df = pd.read_csv(csv_link, encoding='latin1', sep=';', low_memory=False)
        df.columns = df.columns.str.strip()
        
        df_normalized = pd.DataFrame()
        df_normalized['cnpj'] = df['CNPJ'].apply(lambda x: normalize_cnpj(str(x)) if pd.notna(x) else '')
        df_normalized['registro_ans'] = df['REGISTRO_OPERADORA'].astype(str).str.strip() if 'REGISTRO_OPERADORA' in df.columns else ''
        df_normalized['razao_social'] = df['Razao_Social'] if 'Razao_Social' in df.columns else ''
        df_normalized['modalidade'] = df['Modalidade'] if 'Modalidade' in df.columns else ''
        df_normalized['uf'] = df['UF'] if 'UF' in df.columns else ''
        
        df_normalized = df_normalized[df_normalized['cnpj'].str.len() == 14]
        df_normalized = df_normalized.drop_duplicates(subset=['cnpj'], keep='first')
        
        output_path = self.output_dir / output_file
        df_normalized.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"Cadastro salvo: {output_path} ({len(df_normalized)} operadoras)")
        return output_path
    
    def enrich_data(self, consolidated_csv: str, cadastro_csv: str, output_file: str = "despesas_enriquecidas.csv") -> pd.DataFrame:
        df_despesas = pd.read_csv(self.output_dir / consolidated_csv, encoding='utf-8-sig', dtype={'CNPJ': str})
        df_cadastro = pd.read_csv(self.output_dir / cadastro_csv, encoding='utf-8-sig', dtype={'cnpj': str})
        
        df_cadastro = df_cadastro.rename(columns={
            'cnpj': 'CNPJ',
            'registro_ans': 'RegistroANS',
            'razao_social': 'RazaoSocialCadastro',
            'modalidade': 'Modalidade',
            'uf': 'UF'
        })
        
        df_despesas['CNPJ'] = df_despesas['CNPJ'].astype(str).str.strip()
        df_cadastro['CNPJ'] = df_cadastro['CNPJ'].astype(str).str.strip()
        
        df_cadastro_clean = df_cadastro[['CNPJ', 'RegistroANS', 'Modalidade', 'UF']].drop_duplicates(subset=['CNPJ'], keep='first')
        
        print(f"\nRegistros de despesas: {len(df_despesas)}")
        print(f"Registros de cadastro: {len(df_cadastro_clean)}")
        
        df_enriched = df_despesas.merge(df_cadastro_clean, on='CNPJ', how='left')
        
        unmatched = df_enriched['RegistroANS'].isna().sum() if 'RegistroANS' in df_enriched.columns else 0
        print(f"Registros sem match no cadastro: {unmatched}")
        
        output_path = self.output_dir / output_file
        df_enriched.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nDados enriquecidos salvos: {output_path}")
        
        return df_enriched
    
    def aggregate_data(self, enriched_csv: str, output_file: str = "despesas_agregadas.csv") -> pd.DataFrame:
        df = pd.read_csv(self.output_dir / enriched_csv, encoding='utf-8-sig')
        
        if 'UF' not in df.columns:
            df['UF'] = 'N/A'
        
        df_agg = df.groupby(['RazaoSocial', 'UF']).agg({
            'ValorDespesas': ['sum', 'mean', 'std', 'count']
        }).reset_index()
        
        df_agg.columns = ['RazaoSocial', 'UF', 'TotalDespesas', 'MediaDespesas', 'DesvioPadrao', 'NumRegistros']
        
        df_agg['DesvioPadrao'] = df_agg['DesvioPadrao'].fillna(0)
        
        df_agg = df_agg.sort_values('TotalDespesas', ascending=False)
        
        output_path = self.output_dir / output_file
        df_agg.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nDados agregados salvos: {output_path}")
        
        return df_agg