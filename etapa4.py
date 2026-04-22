#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HEADER_FIXO = """<?xml version="1.0" encoding="UTF-8"?>
<fet version="7.5.8">
  <Mode>Official</Mode>
  <Institution_Name>Default institution</Institution_Name>
  <Comments>Default comments</Comments>
  <Days_List>
    <Number_of_Days>6</Number_of_Days>
    <Day>
      <Name>SEG</Name>
      <Long_Name>Segunda</Long_Name>
    </Day>
    <Day>
      <Name>TER</Name>
      <Long_Name>Terca</Long_Name>
    </Day>
    <Day>
      <Name>QUA</Name>
      <Long_Name>Quarta</Long_Name>
    </Day>
    <Day>
      <Name>QUI</Name>
      <Long_Name>Quinta</Long_Name>
    </Day>
    <Day>
      <Name>SEX</Name>
      <Long_Name>Sexta</Long_Name>
    </Day>
    <Day>
      <Name>SAB</Name>
      <Long_Name>Sabado</Long_Name>
    </Day>
  </Days_List>
  <Hours_List>
    <Number_of_Hours>20</Number_of_Hours>
    <Hour>
      <Name>7:00 7:45</Name>
      <Long_Name>07:00</Long_Name>
    </Hour>
    <Hour>
      <Name>7:45
8:30</Name>
      <Long_Name>07:45</Long_Name>
    </Hour>
    <Hour>
      <Name>8:30 9:15</Name>
      <Long_Name>08:30</Long_Name>
    </Hour>
    <Hour>
      <Name>9:35
10:20</Name>
      <Long_Name>9:35</Long_Name>
    </Hour>
    <Hour>
      <Name>10:20 11:05</Name>
      <Long_Name>10:20</Long_Name>
    </Hour>
    <Hour>
      <Name>11:05 11:50</Name>
      <Long_Name>11:05</Long_Name>
    </Hour>
    <Hour>
      <Name>11:50 12:35</Name>
      <Long_Name>11:50</Long_Name>
    </Hour>
    <Hour>
      <Name>12:35 13:00</Name>
      <Long_Name>12:35</Long_Name>
    </Hour>
    <Hour>
      <Name>13:00 13:45</Name>
      <Long_Name>13:00</Long_Name>
    </Hour>
    <Hour>
      <Name>13:45
14:30</Name>
      <Long_Name>13:45</Long_Name>
    </Hour>
    <Hour>
      <Name>14:30 15:15</Name>
      <Long_Name>14:30</Long_Name>
    </Hour>
    <Hour>
      <Name>15:30
16:15</Name>
      <Long_Name>15:30</Long_Name>
    </Hour>
    <Hour>
      <Name>16:15
17:00</Name>
      <Long_Name>16:15</Long_Name>
    </Hour>
    <Hour>
      <Name>17:00
17:45</Name>
      <Long_Name>17:00</Long_Name>
    </Hour>
    <Hour>
      <Name>17:45 18:30</Name>
      <Long_Name>17:45</Long_Name>
    </Hour>
    <Hour>
      <Name>18:30 19:15</Name>
      <Long_Name>18:30</Long_Name>
    </Hour>
    <Hour>
      <Name>19:15
20:00</Name>
      <Long_Name>19:15</Long_Name>
    </Hour>
    <Hour>
      <Name>20:00 20:45</Name>
      <Long_Name>20:00</Long_Name>
    </Hour>
    <Hour>
      <Name>20:55 21:40</Name>
      <Long_Name>20:55</Long_Name>
    </Hour>
    <Hour>
      <Name>21:40
22:25</Name>
      <Long_Name>21:40</Long_Name>
    </Hour>
  </Hours_List>
"""

HEADER_ALIASES = {
    "curso": "curso",
    "turma": "turma",
    "turma/grupo": "turma",
    "unidade curricular": "disciplina",
    "disciplina": "disciplina",
    "ch semanal (h/a)": "ch",
    "ch": "ch",
    "ead": "ead",
    "ts": "ts",
    "professor(a)": "professor",
    "professor": "professor",
    "docente": "professor",
    "área sugerida": "area",
    "area sugerida": "area",
    "área": "area",
    "area": "area",
    "período no ppc": "periodo",
    "periodo no ppc": "periodo",
    "observações da coordenação": "obs_coord",
    "observacoes da coordenacao": "obs_coord",
    "observações do(a) professor(a)": "obs_prof",
    "observacoes do(a) professor(a)": "obs_prof",
}

def xml(text: str) -> str:
    return escape(text or "")

def norm(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())

def norm_key(value) -> str:
    s = norm(value).lower()
    trocas = {
        "á":"a","à":"a","ã":"a","â":"a",
        "é":"e","ê":"e",
        "í":"i",
        "ó":"o","ô":"o","õ":"o",
        "ú":"u",
        "ç":"c",
    }
    for a, b in trocas.items():
        s = s.replace(a, b)
    return s

def canonical_header(value: str) -> str:
    return HEADER_ALIASES.get(norm_key(value), norm_key(value))

def slug(value: str) -> str:
    s = norm_key(value)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def detect_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8000]
    return ";" if sample.count(";") > sample.count(",") else ","

def read_csv_rows(path: Path):
    delimiter = detect_delimiter(path)
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            raw_header = next(reader)
        except StopIteration:
            return [], []

        header = [canonical_header(h) for h in raw_header]

        for raw in reader:
            if not any(norm(c) for c in raw):
                continue
            row = {}
            for i, cell in enumerate(raw):
                key = header[i] if i < len(header) else f"extra_{i}"
                row[key] = norm(cell)
            rows.append(row)

    return header, rows

def to_int_hours(text: str) -> int:
    value = norm(text).replace(",", ".")
    if not value:
        return 0
    try:
        num = float(value)
    except Exception:
        return 0
    if 0 < num < 1:
        return 1
    return max(0, int(round(num)))

def split_duration(total: int):
    if total <= 0:
        return []
    if total <= 3:
        return [total]
    if total == 4:
        return [2, 2]
    if total == 5:
        return [3, 2]
    parts = []
    remaining = total
    while remaining > 0:
        if remaining == 4:
            parts.extend([2, 2])
            break
        if remaining == 5:
            parts.extend([3, 2])
            break
        if remaining <= 3:
            parts.append(remaining)
            break
        parts.append(3)
        remaining -= 3
    return parts

def infer_group(course: str, turma: str) -> str:
    c = norm_key(course)
    t = slug(turma) or "grupo"

    if "integrado" in c and "edific" in c:
        return f"edifint-{t}"
    if "integrado" in c and "informat" in c:
        return f"infint-{t}"
    if "proeja" in c and "edific" in c:
        return f"edifproeja-{t}"
    if "proeja" in c and "informat" in c:
        return f"infproeja-{t}"
    if "licenciatura" in c and "comput" in c:
        return f"liccomp-{t}"
    if "arquitet" in c:
        return f"arq-{t}"
    if "administr" in c and "ead" in c:
        return f"admead-{t}"
    if "sub" in c and "log" in c:
        return f"logsub-{t}"
    if "sub" in c and "edific" in c:
        return f"edifsub-{t}"

    base = slug(course)[:10] or "curso"
    return f"{base}-{t}"

def build_subject_parts(row, warnings):
    """
    Regra:
    - a disciplina base usa exatamente a CH da coluna 'ch'
    - se EAD > 0, cria também uma disciplina '<nome> - EAD' com CH = coluna 'ead'
    - se TS > 0, cria também uma disciplina '<nome> - TS' com CH = coluna 'ts'
    - não há redistribuição, metade, resto ou qualquer cálculo entre as colunas

    Exemplo:
    - ch=2, ead=0, ts=2
      -> disciplina base: 2
      -> disciplina ' - TS': 2
    """
    disc = norm(row.get("disciplina", ""))
    if not disc:
        return []

    ch_principal = to_int_hours(row.get("ch", "0"))
    ch_ead = to_int_hours(row.get("ead", "0"))
    ch_ts = to_int_hours(row.get("ts", "0"))

    parts = []

    if ch_principal > 0:
        parts.append((disc, ch_principal))

    if ch_ead > 0:
        parts.append((f"{disc} - EAD", ch_ead))

    if ch_ts > 0:
        parts.append((f"{disc} - TS", ch_ts))

    if not parts:
        warnings.append(f"CH, EAD e TS zerados em '{disc}'")

    return parts

def main():
    if len(sys.argv) != 3:
        print("uso: python etapa_4_corrigida_ead_ts_metade.py entrada.csv saida.fet")
        return

    inp = Path(sys.argv[1]).expanduser().resolve()
    out = Path(sys.argv[2]).expanduser().resolve()

    if not inp.exists():
        print(f"Arquivo não encontrado: {inp}")
        return

    header, rows = read_csv_rows(inp)
    if not rows:
        print("Nenhuma linha válida encontrada.")
        return

    warnings = []
    teachers = []
    subjects = []
    years = {}
    activities = []
    next_id = 1

    for row in rows:
        curso = norm(row.get("curso", ""))
        turma = norm(row.get("turma", ""))
        disc = norm(row.get("disciplina", ""))
        prof = norm(row.get("professor", ""))

        if not disc:
            warnings.append(f"Disciplina vazia: {row}")
            continue
        if not prof:
            warnings.append(f"Professor vazio em '{disc}'")
            continue

        if prof not in teachers:
            teachers.append(prof)

        year_name = curso if curso else "Cursos"
        group_name = infer_group(curso, turma)

        years.setdefault(year_name, [])
        if group_name not in years[year_name]:
            years[year_name].append(group_name)

        parts = build_subject_parts(row, warnings)
        if not parts:
            warnings.append(f"CH inválida em '{disc}'")
            continue

        for subj, ch_total in parts:
            if subj not in subjects:
                subjects.append(subj)
            for dur in split_duration(ch_total):
                activities.append({
                    "teacher": prof,
                    "subject": subj,
                    "students": group_name,
                    "duration": dur,
                    "id": next_id,
                })
                next_id += 1

    with out.open("w", encoding="utf-8", newline="") as f:
        f.write(HEADER_FIXO)

        f.write("  <Subjects_List>\n")
        for s in subjects:
            f.write("    <Subject>\n")
            f.write(f"      <Name>{xml(s)}</Name>\n")
            f.write("      <Long_Name></Long_Name>\n")
            f.write("      <Code></Code>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Subject>\n")
        f.write("  </Subjects_List>\n")

        f.write("  <Activity_Tags_List>\n")
        f.write("  </Activity_Tags_List>\n")

        f.write("  <Teachers_List>\n")
        for t in teachers:
            f.write("    <Teacher>\n")
            f.write(f"      <Name>{xml(t)}</Name>\n")
            f.write("      <Long_Name></Long_Name>\n")
            f.write("      <Code></Code>\n")
            f.write("      <Target_Number_of_Hours>0</Target_Number_of_Hours>\n")
            f.write("      <Qualified_Subjects>\n")
            f.write("      </Qualified_Subjects>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Teacher>\n")
        f.write("  </Teachers_List>\n")

        f.write("  <Students_List>\n")
        for year_name, groups in years.items():
            f.write("    <Year>\n")
            f.write(f"      <Name>{xml(year_name)}</Name>\n")
            f.write("      <Number_of_Students>0</Number_of_Students>\n")
            f.write("      <Comments></Comments>\n")
            for g in groups:
                f.write("      <Group>\n")
                f.write(f"        <Name>{xml(g)}</Name>\n")
                f.write("        <Number_of_Students>0</Number_of_Students>\n")
                f.write("        <Comments></Comments>\n")
                f.write("      </Group>\n")
            f.write("    </Year>\n")
        f.write("  </Students_List>\n")

        f.write("  <Activities_List>\n")
        for a in activities:
            f.write("    <Activity>\n")
            f.write(f"      <Teacher>{xml(a['teacher'])}</Teacher>\n")
            f.write(f"      <Subject>{xml(a['subject'])}</Subject>\n")
            f.write(f"      <Students>{xml(a['students'])}</Students>\n")
            f.write(f"      <Duration>{a['duration']}</Duration>\n")
            f.write(f"      <Total_Duration>{a['duration']}</Total_Duration>\n")
            f.write(f"      <Id>{a['id']}</Id>\n")
            f.write("      <Activity_Group_Id>0</Activity_Group_Id>\n")
            f.write("      <Active>true</Active>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Activity>\n")
        f.write("  </Activities_List>\n")

        f.write("  <Rooms_List>\n")
        f.write("  </Rooms_List>\n")

        f.write("  <Time_Constraints_List>\n")
        f.write("    <ConstraintBasicCompulsoryTime>\n")
        f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
        f.write("      <Active>true</Active>\n")
        f.write("      <Comments></Comments>\n")
        f.write("    </ConstraintBasicCompulsoryTime>\n")
        f.write("  </Time_Constraints_List>\n")

        f.write("  <Space_Constraints_List>\n")
        f.write("    <ConstraintBasicCompulsorySpace>\n")
        f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
        f.write("      <Active>true</Active>\n")
        f.write("      <Comments></Comments>\n")
        f.write("    </ConstraintBasicCompulsorySpace>\n")
        f.write("  </Space_Constraints_List>\n")

        f.write("</fet>\n")

    warnings_path = out.with_suffix(".warnings.txt")
    warnings_path.write_text("\n".join(warnings) if warnings else "Nenhum aviso.", encoding="utf-8")

    print(f"OK - FET gerado: {out}")
    print(f"Avisos: {warnings_path}")
    print(f"Linhas lidas: {len(rows)}")
    print(f"Teachers: {len(teachers)} | Subjects: {len(subjects)} | Activities: {len(activities)}")

if __name__ == "__main__":
    main()
