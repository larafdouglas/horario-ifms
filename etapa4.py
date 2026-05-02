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

def clean_turma(value: str) -> str:
    """Converte turmas vindas da planilha, ex.: 1025.0 -> 1025."""
    s = norm(value).replace(",", ".")
    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".")[0]
    return s

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
    """
    Regra atual da etapa 4:
    - se forem apenas 2 aulas, cadastra uma aula dupla;
    - se não houver indicação específica de divisão, cadastra o restante como aulas simples.
    """
    if total <= 0:
        return []
    if total == 2:
        return [2]
    return [1] * total

def infer_group(course: str, turma: str) -> str:
    c = norm_key(course)
    t = slug(clean_turma(turma)) or "grupo"

    if "integrado" in c and "edific" in c:
        return f"edifint-{t}"
    if "integrado" in c and "informat" in c:
        return f"inf{t}"
    if "proeja" in c and "edific" in c:
        return f"edifproeja-{t}"
    if "proeja" in c and "informat" in c:
        return f"infproeja-{t}"
    if "licenciatura" in c and "comput" in c:
        return f"liccomp-{t}"
    if "arquitet" in c:
        return f"arq{t}"
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
    Ordem esperada das cargas após a disciplina:
    disciplina, CH presencial, EAD, TS, professor...

    Retorna tuplas: (nome_da_disciplina, carga, tipo)
    tipo = "presencial", "ead" ou "ts".
    """
    disc = norm(row.get("disciplina", ""))
    if not disc:
        return []

    ch_presencial = to_int_hours(row.get("ch", "0"))
    ch_ead = to_int_hours(row.get("ead", "0"))
    ch_ts = to_int_hours(row.get("ts", "0"))

    parts = []

    if ch_presencial > 0:
        parts.append((disc, ch_presencial, "presencial"))

    if ch_ead > 0:
        parts.append((f"{disc} - EAD", ch_ead, "ead"))

    if ch_ts > 0:
        parts.append((f"{disc} - TS", ch_ts, "ts"))

    if not parts:
        warnings.append(f"CH presencial, EAD e TS zerados em '{disc}'")

    return parts

def group_for_part(base_group: str, tipo: str) -> str:
    """Cria turma/grupo específico quando a parte for EAD ou TS."""
    if tipo == "ead":
        return f"{base_group}-ead"
    if tipo == "ts":
        return f"{base_group}-ts"
    return base_group

def split_teachers(text: str):
    """Permite dois ou mais professores na mesma atividade usando múltiplas tags <Teacher>."""
    raw = norm(text)
    if not raw:
        return []
    parts = re.split(r"\s*(?:;|/|\+|\be\b|\band\b|,)\s*", raw, flags=re.IGNORECASE)
    teachers = []
    for part in parts:
        name = norm(part)
        if name and name not in teachers:
            teachers.append(name)
    return teachers

ROOMS = [
    "Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11",
    "Sala C1", "Sala C2", "Sala C3", "Sala C12",
    "Lab A2", "Lab B3", "Lab B12", "Lab C9", "Lab C11", "Lab C13",
    "EAD 1", "EAD 2",
]

DAYS = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB"]
HOURS = [
    "7:00 7:45",
    "7:45\n8:30",
    "8:30 9:15",
    "9:35\n10:20",
    "10:20 11:05",
    "11:05 11:50",
    "11:50 12:35",
    "12:35 13:00",
    "13:00 13:45",
    "13:45\n14:30",
    "14:30 15:15",
    "15:30\n16:15",
    "16:15\n17:00",
    "17:00\n17:45",
    "17:45 18:30",
    "18:30 19:15",
    "19:15\n20:00",
    "20:00 20:45",
    "20:55 21:40",
    "21:40\n22:25",
]

# Períodos usados nas restrições de horário.
# Manhã: tempos 1 a 6.
# Tarde: tempos 9 a 14.
# Noite: tempos 16 a 20.
PERIOD_HOURS = {
    "manha": HOURS[0:6],
    "tarde": HOURS[8:14],
    "noite": HOURS[15:20],
}

SALAS_COM_MESAS = ["Sala A9", "Sala B9", "Sala B11", "Sala C1", "Sala C2", "Sala C3"]
SALAS_GERAIS = ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11", "Sala C1", "Sala C2", "Sala C3"]

INTEGRADO_SALA_POR_TURMA = {
    "1026": ["Sala B9"],
    "1025": ["Sala A9"],
    "1024": ["Sala C2"],
    "2026": ["Sala B11"],
    "2025": ["Sala C1"],
    "2024": ["Sala C3"],
}

ARQ_SALAS = {
    "1221": ["Lab C11"],
    "1222": ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11", "Sala C1", "Sala C2", "Sala C3"],
    "1223": ["Sala A3"],
    "1224": ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11", "Sala C1", "Sala C2", "Sala C3"],
    "1225": ["Sala A3"],
    "1226": ["Sala B10"],
    "dp": ["Sala A3", "Sala A9", "Sala B9", "Sala B11", "Sala C1", "Sala C2", "Sala C3"],
}

ARQ_LABS = {
    "1221": ["Lab C11"],
    "1222": ["Lab C9", "Lab C11"],
    "1223": ["Lab B3"],
    "1224": ["Lab C9", "Lab C11"],
    "1225": ["Lab B12", "Lab B3"],
    "1226": ["Lab B12", "Lab C9", "Lab C11"],
    "dp": ["Lab C9", "Lab C11", "Lab B3", "Lab B12"],
}

def unique_list(values):
    out = []
    for v in values:
        if v and v not in out:
            out.append(v)
    return out

def is_dp(turma: str) -> bool:
    return norm_key(clean_turma(turma)) == "dp"

def room_kind(subject: str, area: str = "", obs: str = "") -> str:
    text = norm_key(" ".join([subject, area, obs]))
    if "ead" in text:
        return "ead"
    if "hardware" in text or "manutencao" in text and "comput" in text:
        return "hardware"
    if "alto desempenho" in text or "placa de video" in text or "gpu" in text or "render" in text:
        return "alto_desempenho"
    if "materiais de construcao" in text or "material de construcao" in text:
        return "materiais"
    if "prancheta" in text or "projeto" in text or "atelie" in text or "ateliê" in text:
        return "atelie"
    lab_words = [
        "laboratorio", "lab", "informatica", "computacao", "programacao", "software",
        "banco de dados", "redes", "sistemas", "web", "algoritmo", "modelagem",
        "desenho assistido", "cad", "bim", "grasshopper", "rhino",
    ]
    if any(w in text for w in lab_words):
        return "lab"
    return "sala"

def rooms_for_activity(course: str, turma: str, subject: str, tipo: str, row: dict):
    c = norm_key(course)
    t = norm_key(clean_turma(turma))
    obs = " ".join([row.get("obs_coord", ""), row.get("obs_prof", "")])
    kind = room_kind(subject, row.get("area", ""), obs)

    if tipo == "ead" or kind == "ead":
        if "edific" in c:
            return ["EAD 2"]
        if "informat" in c or "comput" in c:
            return ["EAD 1"]
        return ["EAD 1", "EAD 2"]

    if kind == "hardware":
        return ["Lab C13"]
    if kind == "alto_desempenho":
        return ["Lab B3"]
    if kind == "materiais":
        # Dois ambientes possíveis: sala de aula da turma e Laboratório de Materiais A2.
        if "integrado" in c and not is_dp(turma):
            base = INTEGRADO_SALA_POR_TURMA.get(t, SALAS_COM_MESAS)
        elif "arquitet" in c:
            base = ARQ_SALAS.get("dp" if is_dp(turma) else t, SALAS_GERAIS)
        elif "proeja" in c:
            base = ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11"]
        else:
            base = SALAS_GERAIS
        return unique_list(base + ["Lab A2"])
    if kind == "atelie":
        return ["Sala C12"]

    if "integrado" in c:
        if is_dp(turma):
            return ["Lab C9", "Lab C11"] if kind == "lab" else ["Sala B9", "Sala B10", "Sala B11"]
        if kind == "lab":
            return ["Lab C9", "Lab C11"]
        return INTEGRADO_SALA_POR_TURMA.get(t, SALAS_COM_MESAS)

    if "arquitet" in c:
        key = "dp" if is_dp(turma) else t
        if kind == "lab":
            return ARQ_LABS.get(key, ["Lab C9", "Lab C11", "Lab B3", "Lab B12"])
        return ARQ_SALAS.get(key, SALAS_GERAIS)

    if "proeja" in c:
        if kind == "lab":
            return ["Lab B3", "Lab B12"]
        return ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11"]

    if "licenciatura" in c and "comput" in c:
        if kind == "lab":
            return ["Lab B3", "Lab B12", "Lab C9", "Lab C11"]
        return ["Sala A3", "Sala A9", "Sala B9", "Sala B10", "Sala B11", "Sala C1", "Sala C2", "Sala C3"]

    if kind == "lab":
        return ["Lab B3", "Lab B12", "Lab C9", "Lab C11"]
    return SALAS_GERAIS


# =========================================================
# TAGS DE TURNO DAS ATIVIDADES
# =========================================================

def tags_for_activity(course: str, tipo: str):
    """Define a Activity_Tag de acordo com o tipo e o curso."""
    c = norm_key(course)

    if tipo == "ead":
        return ["EAD-manha"]

    if tipo == "ts":
        return ["TS-manha-e-tarde"]

    if "integrado" in c:
        return ["manha"]

    if "arquitet" in c:
        return ["manha"]

    if "licenciatura" in c:
        return ["noite"]

    if "proeja" in c:
        return ["noite"]

    return []

def time_hours_for_activity(course: str, tipo: str):
    """Define as janelas permitidas/preferidas de horário por tipo e curso."""
    c = norm_key(course)

    # EAD sempre à tarde e à noite, independentemente do curso.
    if tipo == "ead":
        return unique_list(PERIOD_HOURS["tarde"] + PERIOD_HOURS["noite"])

    # TS sempre de manhã e à tarde, independentemente do curso.
    if tipo == "ts":
        return unique_list(PERIOD_HOURS["manha"] + PERIOD_HOURS["tarde"])

    # Presencial regular por curso.
    if "integrado" in c:
        return PERIOD_HOURS["manha"]
    if "arquitet" in c:
        return PERIOD_HOURS["manha"]
    if "licenciatura" in c:
        return PERIOD_HOURS["noite"]
    if "proeja" in c:
        return PERIOD_HOURS["noite"]

    # Se o curso não for reconhecido, não restringe tempo para evitar erro.
    return []


def write_activity_allowed_time_slots_constraint(f, activity_id: int, allowed_slots: list[tuple[str, str]], weight: int = 100, comments: str = ""):
    """Restringe uma atividade a uma lista de slots permitidos.

    Com Weight 100, funciona como bloqueio dos demais slots.
    Usaremos isso apenas para turmas de Arquitetura nesta etapa.
    """
    if not allowed_slots:
        return

    f.write("    <ConstraintActivityPreferredTimeSlots>\n")
    f.write(f"      <Weight_Percentage>{weight}</Weight_Percentage>\n")
    f.write(f"      <Activity_Id>{activity_id}</Activity_Id>\n")
    f.write(f"      <Number_of_Preferred_Time_Slots>{len(allowed_slots)}</Number_of_Preferred_Time_Slots>\n")
    for day, hour in allowed_slots:
        f.write("      <Preferred_Time_Slot>\n")
        f.write(f"        <Preferred_Day>{xml(day)}</Preferred_Day>\n")
        f.write(f"        <Preferred_Hour>{xml(hour)}</Preferred_Hour>\n")
        f.write("      </Preferred_Time_Slot>\n")
    f.write("      <Active>true</Active>\n")
    f.write(f"      <Comments>{xml(comments)}</Comments>\n")
    f.write("    </ConstraintActivityPreferredTimeSlots>\n")


def turma_arquitetura_from_activity(activity: dict) -> str:
    """Retorna a turma de Arquitetura a partir do campo Students, ex.: arq1222 -> 1222."""
    students = str(activity.get("students", "")).lower()
    m = re.search(r"arq(\d{4})", students)
    if m:
        return m.group(1)

    # Fallback para casos em que o grupo venha apenas como número.
    m = re.search(r"\b(122[1-6])\b", students)
    if m:
        return m.group(1)

    return ""


def is_atividade_arquitetura(activity: dict) -> bool:
    if turma_arquitetura_from_activity(activity):
        return True
    course = norm_key(activity.get("course", ""))
    return "arquitet" in course


def calcular_turma_arquitetura_maior_ch(activities: list[dict]) -> str:
    carga_por_turma = {}
    for a in activities:
        turma = turma_arquitetura_from_activity(a)
        if not turma:
            continue
        carga_por_turma[turma] = carga_por_turma.get(turma, 0) + int(a.get("duration", 0))

    if not carga_por_turma:
        return ""

    # Maior CH; em empate, pega a turma de menor número para ser previsível.
    return sorted(carga_por_turma.items(), key=lambda item: (-item[1], item[0]))[0][0]


def slots_manha_sem_sabado() -> list[tuple[str, str]]:
    return [
        (day, hour)
        for day in DAYS
        if day != "SAB"
        for hour in PERIOD_HOURS["manha"]
    ]


def slots_manha_mais_um_tempo_tarde_sem_sabado() -> list[tuple[str, str]]:
    slots = slots_manha_sem_sabado()

    # Apenas um horário a mais no período da tarde.
    # Aqui usamos o primeiro tempo listado em PERIOD_HOURS["tarde"].
    hora_extra_tarde = PERIOD_HOURS["tarde"][0] if PERIOD_HOURS.get("tarde") else None
    if hora_extra_tarde:
        for day in DAYS:
            if day != "SAB":
                slots.append((day, hora_extra_tarde))

    return slots


def write_students_not_available_constraint(f, students: str, allowed_hours: list[str]):
    """Restringe turno por turma/grupo usando tag reconhecida pelo FET.

    O FET não possui ConstraintStudentsSetPreferredTimeSlots no modo oficial.
    Para dizer que uma turma só pode estudar em certos turnos, geramos
    ConstraintStudentsSetNotAvailableTimes com o COMPLEMENTO dos horários
    permitidos. Assim a regra continua sendo por turma/grupo, não por
    professor e não por atividade individual.
    """
    allowed = set(allowed_hours or [])
    if not allowed:
        return

    blocked_hours = [h for h in HOURS if h not in allowed]
    blocked_slots = [(day, hour) for day in DAYS for hour in blocked_hours]

    if not blocked_slots:
        return

    f.write("    <ConstraintStudentsSetNotAvailableTimes>\n")
    f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
    f.write(f"      <Students>{xml(students)}</Students>\n")
    f.write(f"      <Number_of_Not_Available_Times>{len(blocked_slots)}</Number_of_Not_Available_Times>\n")
    for day, hour in blocked_slots:
        f.write("      <Not_Available_Time>\n")
        f.write(f"        <Day>{xml(day)}</Day>\n")
        f.write(f"        <Hour>{xml(hour)}</Hour>\n")
        f.write("      </Not_Available_Time>\n")
    f.write("      <Active>true</Active>\n")
    f.write("      <Comments></Comments>\n")
    f.write("    </ConstraintStudentsSetNotAvailableTimes>\n")

def write_teachers_max_days_constraint(f, max_days: int = 3):
    """Restrição global: todos os professores com no máximo N dias por semana.

    Evita criar uma ConstraintTeacherMaxDaysPerWeek para cada professor.
    """
    f.write("    <ConstraintTeachersMaxDaysPerWeek>\n")
    f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
    f.write(f"      <Max_Days_Per_Week>{max_days}</Max_Days_Per_Week>\n")
    f.write("      <Active>true</Active>\n")
    f.write("      <Comments></Comments>\n")
    f.write("    </ConstraintTeachersMaxDaysPerWeek>\n")

def write_teachers_no_gaps_constraints(f):
    """Restrições globais para compactar o horário dos professores.

    Usa as versões coletivas do FET, em vez de uma restrição por professor.
    """
    f.write("    <ConstraintTeachersMaxGapsPerDay>\n")
    f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
    f.write("      <Max_Gaps>0</Max_Gaps>\n")
    f.write("      <Active>true</Active>\n")
    f.write("      <Comments></Comments>\n")
    f.write("    </ConstraintTeachersMaxGapsPerDay>\n")

    f.write("    <ConstraintTeachersMaxGapsPerWeek>\n")
    f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
    f.write("      <Max_Gaps>0</Max_Gaps>\n")
    f.write("      <Active>true</Active>\n")
    f.write("      <Comments></Comments>\n")
    f.write("    </ConstraintTeachersMaxGapsPerWeek>\n")

def main():
    if len(sys.argv) != 3:
        print("uso: python etapa4.py entrada.csv saida.fet")
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
    student_time_rules = {}
    student_time_audit = {}
    next_id = 1

    for row in rows:
        curso = norm(row.get("curso", ""))
        turma = norm(row.get("turma", ""))
        disc = norm(row.get("disciplina", ""))
        prof = norm(row.get("professor", ""))
        profs = split_teachers(prof)

        if not disc:
            warnings.append(f"Disciplina vazia: {row}")
            continue
        if not profs:
            warnings.append(f"Professor vazio em '{disc}'")
            continue

        for p in profs:
            if p not in teachers:
                teachers.append(p)

        year_name = curso if curso else "Cursos"
        base_group_name = infer_group(curso, turma)

        years.setdefault(year_name, [])
        if base_group_name not in years[year_name]:
            years[year_name].append(base_group_name)

        parts = build_subject_parts(row, warnings)
        if not parts:
            warnings.append(f"CH inválida em '{disc}'")
            continue

        for subj, ch_total, tipo in parts:
            group_name = group_for_part(base_group_name, tipo)
            if group_name not in years[year_name]:
                years[year_name].append(group_name)

            if subj not in subjects:
                subjects.append(subj)

            # Restrição de horário por turma/grupo.
            # Exemplos:
            # - grupo regular do Integrado/Arquitetura: manhã;
            # - grupo regular da Licenciatura/PROEJA: noite;
            # - grupo -ts: manhã + tarde;
            # - grupo -ead: tarde + noite.
            hours_for_group = time_hours_for_activity(curso, tipo)
            if hours_for_group:
                if group_name in student_time_rules:
                    student_time_rules[group_name] = unique_list(student_time_rules[group_name] + hours_for_group)
                else:
                    student_time_rules[group_name] = hours_for_group
                student_time_audit.setdefault(group_name, set()).add(tipo)

            for dur in split_duration(ch_total):
                activities.append({
                    "teachers": profs,
                    "subject": subj,
                    "students": group_name,
                    "activity_tags": tags_for_activity(curso, tipo),
                    "duration": dur,
                    "id": next_id,
                    "rooms": rooms_for_activity(curso, turma, subj, tipo, row),
                    "time_hours": time_hours_for_activity(curso, tipo),
                    "course": curso,
                    "tipo": tipo,
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
        for tag in ["EAD-manha", "TS-manha-e-tarde", "manha", "noite"]:
            f.write("    <Activity_Tag>\n")
            f.write(f"      <Name>{xml(tag)}</Name>\n")
            f.write("      <Printable>true</Printable>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Activity_Tag>\n")
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
            for teacher in a["teachers"]:
                f.write(f"      <Teacher>{xml(teacher)}</Teacher>\n")
            f.write(f"      <Subject>{xml(a['subject'])}</Subject>\n")
            for tag in a.get("activity_tags", []):
                f.write(f"      <Activity_Tag>{xml(tag)}</Activity_Tag>\n")
            f.write(f"      <Students>{xml(a['students'])}</Students>\n")
            f.write(f"      <Duration>{a['duration']}</Duration>\n")
            f.write(f"      <Total_Duration>{a['duration']}</Total_Duration>\n")
            f.write(f"      <Id>{a['id']}</Id>\n")
            f.write("      <Activity_Group_Id>0</Activity_Group_Id>\n")
            f.write("      <Active>true</Active>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Activity>\n")
        f.write("  </Activities_List>\n")

        f.write("  <Buildings_List>\n")
        f.write("  </Buildings_List>\n")

        f.write("  <Rooms_List>\n")
        for room in ROOMS:
            f.write("    <Room>\n")
            f.write(f"      <Name>{xml(room)}</Name>\n")
            f.write("      <Building></Building>\n")
            f.write("      <Capacity>0</Capacity>\n")
            f.write("      <Virtual>false</Virtual>\n")
            f.write("      <Comments></Comments>\n")
            f.write("    </Room>\n")
        f.write("  </Rooms_List>\n")

        f.write("  <Time_Constraints_List>\n")
        f.write("    <ConstraintBasicCompulsoryTime>\n")
        f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
        f.write("      <Active>true</Active>\n")
        f.write("      <Comments></Comments>\n")
        f.write("    </ConstraintBasicCompulsoryTime>\n")

        # ETAPA: restrições somente para turmas de Arquitetura.
        # - Todas as turmas de Arquitetura: somente manhã, sem sábado.
        # - A turma de Arquitetura com maior carga horária recebe 1 tempo extra da tarde.
        turma_arq_maior_ch = calcular_turma_arquitetura_maior_ch(activities)

        for a in activities:
            if not is_atividade_arquitetura(a):
                continue

            turma_arq = turma_arquitetura_from_activity(a)
            if turma_arq and turma_arq == turma_arq_maior_ch:
                allowed_slots = slots_manha_mais_um_tempo_tarde_sem_sabado()
                comentario = f"Arquitetura {turma_arq}: manhã + 1 tempo da tarde; sábado proibido"
            else:
                allowed_slots = slots_manha_sem_sabado()
                comentario = f"Arquitetura {turma_arq or 'sem turma'}: manhã; sábado proibido"

            write_activity_allowed_time_slots_constraint(
                f,
                a["id"],
                allowed_slots,
                weight=100,
                comments=comentario,
            )

        # Demais cursos seguem sem restrições específicas.

        # Professores concentrados em até 3 dias e sem buracos.
        # Usar restrições globais/coletivas reduz drasticamente a quantidade
        # de restrições individuais no arquivo FET.
        # write_teachers_max_days_constraint(f, 3)
        # write_teachers_no_gaps_constraints(f)

        # Sem validação de time_hours nesta versão-base sem restrições de turno.

        f.write("  </Time_Constraints_List>\n")

        f.write("  <Space_Constraints_List>\n")
        f.write("    <ConstraintBasicCompulsorySpace>\n")
        f.write("      <Weight_Percentage>100</Weight_Percentage>\n")
        f.write("      <Active>true</Active>\n")
        f.write("      <Comments></Comments>\n")
        f.write("    </ConstraintBasicCompulsorySpace>\n")
        # Restrições de sala removidas nesta versão-base.
        # Vamos aplicar depois, passo a passo, se necessário.

        f.write("  </Space_Constraints_List>\n")

        f.write("</fet>\n")

    # Validação final: o arquivo precisa ser XML bem-formado antes de abrir no FET.
    try:
        import xml.etree.ElementTree as ET
        ET.parse(out)
    except Exception as exc:
        warnings.append(f"ERRO XML: arquivo gerado não está bem-formado: {exc}")

    turma_arq_maior_ch_relatorio = calcular_turma_arquitetura_maior_ch(activities)
    audit_lines = [
        "ETAPA - RESTRIÇÕES APLICADAS ÀS TURMAS DE ARQUITETURA",
        "- Todas as atividades de Arquitetura foram restringidas à manhã.",
        "- Sábado foi proibido para Arquitetura, pois não aparece nos slots permitidos.",
        f"- Turma de Arquitetura com maior carga horária: {turma_arq_maior_ch_relatorio or 'não identificada'}.",
        "- Apenas essa turma recebeu 1 tempo extra no período da tarde.",
        "- Nenhuma restrição foi aplicada aos demais cursos.",
    ]

    warnings_path = out.with_suffix(".warnings.txt")
    report = audit_lines + ["", "AVISOS:"] + (warnings if warnings else ["Nenhum aviso."])
    warnings_path.write_text("\n".join(report), encoding="utf-8")

    print(f"OK - FET gerado: {out}")
    print(f"Avisos: {warnings_path}")
    print(f"Linhas lidas: {len(rows)}")
    print(f"Teachers: {len(teachers)} | Subjects: {len(subjects)} | Activities: {len(activities)}")

if __name__ == "__main__":
    main()
