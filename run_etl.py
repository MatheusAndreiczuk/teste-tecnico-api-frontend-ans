from src.etl.downloader import ANSDownloader
from src.etl.processor import ANSProcessor
import sys

def main():
    print("\n--- ETL Pipeline ANS ---\n")
    
    try:
        downloader = ANSDownloader()
        processor = ANSProcessor()
        
        print("Baixando e extraindo arquivos dos últimos 3 trimestres")
        
        try:
            quarters = downloader.get_available_quarters()
            
            if not quarters:
                print("Erro: Nenhum trimestre encontrado na API da ANS.")
                print("Verifique sua conexão com a internet e tente novamente.")
                sys.exit(1)
            
            all_files = []
            for year, quarter, file_url in quarters:
                print(f"  Processando {quarter}{year}...", end=" ")
                zip_file = downloader.download_quarter_files(year, quarter, file_url)
                extracted = downloader.extract_zip(zip_file)
                all_files.extend(extracted)
                print(f"({len(extracted)} arquivos)")
            
            if not all_files:
                print("Erro: Nenhum arquivo extraído dos ZIPs.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Erro ao acessar a API da ANS: {str(e)}")
            print("Verifique sua conexão e tente novamente.")
            sys.exit(1)
        
        print(f"Total extraído: {len(all_files)} arquivos\n")
        
        print("Processando arquivos e identificando dados de despesas...")
        data_files = processor.find_despesas_files(all_files)
        
        if not data_files:
            print("Erro: Nenhum arquivo de despesas identificado.")
            print("Os arquivos baixados não contêm o formato de dados esperado.")
            sys.exit(1)
        
        print(f"Encontrados: {len(data_files)} arquivos de despesas\n")
        
        print("Processando e consolidando dados...")
        data = processor.process_files(data_files)
        
        if not data:
            print("Erro: Nenhum registro extraído dos arquivos.")
            sys.exit(1)
        
        df_consolidated = processor.consolidate_data(data)
        
        if len(df_consolidated) == 0:
            print("Erro: Nenhum registro válido após a validação.")
            print("Todos os registros foram removidos devido a CNPJs inválidos ou valores zerados.")
            sys.exit(1)
        
        print(f"Consolidado: {len(df_consolidated)} registros\n")
        
        print("Baixando dados do cadastro de operadoras...")
        cadastro_path = processor.download_operadoras_cadastro()
        print("Cadastro baixado\n")
        
        print("Enriquecendo dados com informações do cadastro...")
        df_enriched = processor.enrich_data("consolidado_despesas.csv", "operadoras_cadastro.csv")
        print(f"Enriquecido: {len(df_enriched)} registros\n")
        
        print("Agregando dados por nome da empresa e estado...")
        df_aggregated = processor.aggregate_data("despesas_enriquecidas.csv")
        print(f"Gerado: {len(df_aggregated)} agregações\n")
        
        print("--- Pipeline concluído com sucesso ---\n")
        print("Arquivos de saída em data/processed/:")
        print(f"  - consolidado_despesas.csv ({len(df_consolidated)} registros)")
        print(f"  - consolidado_despesas.zip")
        print(f"  - operadoras_cadastro.csv")
        print(f"  - despesas_enriquecidas.csv ({len(df_enriched)} registros)")
        print(f"  - despesas_agregadas.csv ({len(df_aggregated)} agregações)\n")
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nErro crítico: {str(e)}")
        print("\nRastreamento de pilha:")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
