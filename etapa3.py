import csv

arquivo_entrada = "entrada.csv"
arquivo_saida = "saida.csv"

with open(arquivo_entrada, "r", encoding="utf-8-sig", newline="") as f:
    linhas = list(csv.reader(f))

if not linhas:
    raise ValueError("O arquivo está vazio.")

nova_linhas = []

for i, linha in enumerate(linhas):
    # ignora linhas completamente vazias
    if not any(c.strip() for c in linha):
        nova_linhas.append(linha)
        continue

    if i == 0:
        # cabeçalho
        try:
            idx_ch = linha.index("CH Semanal (h/a)")
        except ValueError:
            raise ValueError("Coluna 'CH Semanal (h/a)' não encontrada no cabeçalho.")

        novo_cabecalho = linha[:idx_ch + 1] + ["EAD", "TS"] + linha[idx_ch + 1:]
        nova_linhas.append(novo_cabecalho)
    else:
        # linhas de dados
        nova_linha = linha[:idx_ch + 1] + ["0", "0"] + linha[idx_ch + 1:]
        nova_linhas.append(nova_linha)

with open(arquivo_saida, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(nova_linhas)

print(f"Arquivo gerado com sucesso: {arquivo_saida}")
