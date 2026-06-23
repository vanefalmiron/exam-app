from docx import Document
import re

OPTION_STRICT_RE = re.compile(r'^([A-Z])\.\s+\S.+')
OPTION_SPLIT_RE  = re.compile(r'(?<!\A)(?=[A-Z]\.\s)')

ELIGE_N_RE = re.compile(
    r'\(elige\s+(\w+)\)'
    r'|\(selecciona\s+(\w+)\)'
    r'|\(choose\s+(\w+)\)'
    r'|select\s+(\w+)\s+answer'
    r'|elige\s+(\w+)\s+(?:respuestas?|opciones?)'
    r'|selecciona\s+(\w+)\s+(?:respuestas?|opciones?)'
    r'|elija\s+(\w+)\s+(?:respuestas?|opciones?)'
    r'|choose\s+(\w+)\s+(?:answers?|options?)'
    r'|(?:qué|que|cuáles?|cuales?|which)\s+(\w+)\s+\w+'
    r'|(\w+)\s+(?:archivos?|acciones?|opciones?|pasos?|métodos?|formas?|maneras?|comandos?|servicios?|configuraciones?|medidas?|tareas?|elementos?)\s+(?:deberías?|debe|debería|should|would|necesitas?)',
    re.IGNORECASE
)
PALABRAS_NUM = {"dos": 2, "two": 2, "tres": 3, "three": 3, "cuatro": 4, "four": 4,
                "cinco": 5, "five": 5, "2": 2, "3": 3, "4": 4, "5": 5}

def _num_respuestas_enunciado(texto):
    for m in ELIGE_N_RE.finditer(texto):
        token = next((g for g in m.groups() if g is not None), None)
        if token:
            n = PALABRAS_NUM.get(token.lower())
            if n:
                return n
    return None

def _looks_like_option_letter(text):
    return bool(OPTION_STRICT_RE.match(text)) and len(text) >= 5

def _is_option(text, expected_letters):
    m = OPTION_STRICT_RE.match(text)
    if not m:
        return False
    letra = m.group(1)
    if len(text) < 5:
        return False
    if not expected_letters and letra != 'A':
        return False
    if expected_letters:
        next_expected = chr(ord(max(expected_letters)) + 1)
        if letra not in (next_expected, 'A'):
            return False
    return True


def parse_exam(file):
    doc = Document(file)
    MARKER_RE = re.compile(r'(Pregunta\s+\d+\s+Respuesta)')

    tokens = []

    for para in doc.paragraphs:
        if not para.text.strip():
            continue

        run_chunks = []
        for run in para.runs:
            if run.text:
                run_chunks.append((run.text, bool(run.bold)))

        merged = []
        for text, bold in run_chunks:
            if merged and merged[-1][1] == bold:
                merged[-1] = (merged[-1][0] + text, bold)
            else:
                merged.append([text, bold])

        for chunk_text, chunk_bold in merged:
            parts = MARKER_RE.split(chunk_text)
            for part in parts:
                for line in part.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    subparts = OPTION_SPLIT_RE.split(line)
                    for sp in subparts:
                        sp = sp.strip()
                        if sp:
                            tokens.append((sp, chunk_bold))

    questions = []
    current_q = None

    for text, is_bold in tokens:
        is_marker   = bool(re.match(r'^Pregunta\s+\d+\s+Respuesta$', text))
        is_unit     = text.lower().startswith("unidad ")
        is_correcta = text.lower().startswith("respuesta correcta")

        if is_unit or is_marker:
            continue

        if is_correcta and current_q:
            m = re.search(r'[Rr]espuesta correcta[:\s]+(.+)', text)
            if m:
                correcta_texto = m.group(1).strip()
                for op in current_q["opciones"]:
                    if op.strip() == correcta_texto or op.strip().endswith(correcta_texto):
                        current_q["correctas"].add(op)
                        break
                if not current_q["correctas"]:
                    current_q["correctas"].add(correcta_texto)
            continue

        letras_actuales = current_q["_letras"] if current_q else set()
        starts_option = _is_option(text, letras_actuales)

        # Caso: negrita con patrón "Letra. texto" pero NO es opción válida en secuencia
        # y todavía no hay opciones → es un fragmento del enunciado, concatenar
        es_fragmento_enunciado = (
            is_bold
            and not starts_option
            and _looks_like_option_letter(text)
            and current_q is not None
            and not current_q["opciones"]
        )

        if es_fragmento_enunciado:
            current_q["pregunta"] += " " + text
            n = _num_respuestas_enunciado(text)
            if n and not current_q.get("_n_requeridas"):
                current_q["_n_requeridas"] = n

        elif is_bold and not starts_option and not _looks_like_option_letter(text):
            # Nuevo título de pregunta real
            if current_q and current_q["opciones"]:
                questions.append(current_q)
            n_requeridas = _num_respuestas_enunciado(text)
            current_q = {
                "pregunta": text,
                "opciones": [],
                "correctas": set(),
                "_letras": set(),
                "_n_requeridas": n_requeridas,
            }

        elif current_q is not None and starts_option:
            letra = text[0].upper()
            if letra in current_q["_letras"]:
                continue
            current_q["_letras"].add(letra)
            current_q["opciones"].append(text)
            if is_bold:
                current_q["correctas"].add(text)

    if current_q and current_q["opciones"]:
        questions.append(current_q)

    def sort_key(op):
        m = re.match(r'^([A-Z])[.\s]', op)
        return m.group(1) if m else op

    result = []
    for q in questions:
        q["opciones"] = sorted(q["opciones"], key=sort_key)
        del q["_letras"]
        q["correctas"] = sorted(q["correctas"], key=sort_key)
        q["correcta"] = q["correctas"][0] if q["correctas"] else None

        n_req = q.pop("_n_requeridas", None)
        if n_req and n_req > 1:
            q["multi"] = True
            q["n_correctas"] = n_req
        elif len(q["correctas"]) > 1:
            q["multi"] = True
            q["n_correctas"] = len(q["correctas"])
        else:
            q["multi"] = False
            q["n_correctas"] = 1

        if q["correctas"]:
            result.append(q)

    return result
