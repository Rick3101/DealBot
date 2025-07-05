import csv
from io import StringIO

def exportar_para_csv(colunas: list[str], dados: list[list], separador=",") -> bytes:
    output = StringIO()
    writer = csv.writer(output, delimiter=separador)
    writer.writerow(colunas)
    for linha in dados:
        writer.writerow(linha)
    return output.getvalue().encode()
