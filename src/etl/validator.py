import re

def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r'[^0-9]', '', cnpj)

def validate_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    if cnpj == cnpj[0] * 14:
        return False
    
    def calculate_digit(cnpj_partial, weights):
        total = sum(int(cnpj_partial[i]) * weights[i] for i in range(len(weights)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_digit = calculate_digit(cnpj[:12], weights_first)
    
    if int(cnpj[12]) != first_digit:
        return False
    
    weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_digit = calculate_digit(cnpj[:13], weights_second)
    
    return int(cnpj[13]) == second_digit
