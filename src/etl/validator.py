import re

def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r'[^0-9]', '', cnpj)
