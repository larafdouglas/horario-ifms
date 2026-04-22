#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from pathlib import Path

# Junta TODOS os CSV ignorando diferenças de cabeçalho
# Usa apenas o cabeçalho do primeiro arquivo

pasta = Path(".")
saida = Path("entrada.csv")

arquivos = sorted([p for p in pasta.rglob("*.csv") if p != saida])

cabecalho = None
total_linhas = 0

with saida.open("w", newline="", encoding="utf-8-sig") as out:
    writer = csv.writer(out)

    for i, arquivo in enumerate(arquivos):
        with arquivo.open("r", newline="", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))

        if not reader:
            continue

        if cabecalho is None:
            cabecalho = reader[0]
            writer.writerow(cabecalho)

        # pega só as linhas após o cabeçalho
        for linha in reader[1:]:
            if not any(str(c).strip() for c in linha):
                continue
            writer.writerow(linha)
            total_linhas += 1

print("Arquivo combinado_total.csv gerado!")
print("Total de linhas:", total_linhas)
