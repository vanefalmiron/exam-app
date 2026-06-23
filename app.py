import streamlit as st
import random
import re
from parser import parse_exam

st.set_page_config(page_title="Examen ASIR", page_icon="📝", layout="centered")
st.title("📝 Práctica de examen")

LIMITE = 50

# ─────────────────────────────────────────────
# DETECCIÓN DE TIPO DE PREGUNTA
# ─────────────────────────────────────────────

def detectar_tipo(q):
    """
    Devuelve el tipo visual de la pregunta:
    - 'objetivo': opciones son solo Sí / No (ej: "¿Cumple el objetivo?")
    - 'sinono': opciones con patrón "X: Sí / Y: No / ..."  (tabla de afirmaciones)
    - 'normal': pregunta estándar
    """
    opciones = q.get("opciones", [])
    textos = [o.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ. ").strip().lower() for o in opciones]

    # Tipo objetivo: exactamente 2 opciones y son "sí" / "no"
    if len(opciones) == 2 and set(textos) <= {"sí", "no", "si", "yes", "no"}:
        return "objetivo"

    # Tipo tabla sí/no: opciones con patrón "X: Sí / Y: No"
    si_no_re = re.compile(r'.+:\s*(sí|no|si)\b', re.IGNORECASE)
    slash_count = sum(1 for o in opciones if "/" in o and si_no_re.search(o))
    if slash_count >= 2:
        return "sinono"

    return "normal"


def parsear_sinono(opcion):
    """
    De "A. UserA: Sí / UserB: No / User1: No" extrae lista de (entidad, valor).
    """
    texto = re.sub(r'^[A-Z]\.\s*', '', opcion).strip()
    partes = [p.strip() for p in texto.split("/")]
    resultado = []
    for p in partes:
        m = re.match(r'(.+?):\s*(Sí|No|Si)', p, re.IGNORECASE)
        if m:
            resultado.append((m.group(1).strip(), m.group(2).capitalize()))
    return resultado


# ─────────────────────────────────────────────
# RENDERIZADO DE OPCIONES POR TIPO
# ─────────────────────────────────────────────

def render_opciones_normal(q, prefix, is_multi):
    opciones = q["opciones"]
    if is_multi:
        seleccion = []
        for op in opciones:
            if st.checkbox(op, key=f"{prefix}_check_{op}"):
                seleccion.append(op)
        confirmar_disabled = len(seleccion) != len(q["correctas"])
        if confirmar_disabled and seleccion:
            st.caption(f"Selecciona exactamente {len(q['correctas'])} opciones (llevas {len(seleccion)})")
        return seleccion, confirmar_disabled
    else:
        eleccion = st.radio("Elige una opción:", opciones, key=f"{prefix}_radio", index=None)
        return eleccion, eleccion is None


def render_opciones_objetivo(q, prefix):
    """Solo Sí / No, con botones grandes."""
    opciones = q["opciones"]
    col1, col2 = st.columns(2)
    textos = [o.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ. ").strip() for o in opciones]
    eleccion = st.radio(
        "¿Cumple el objetivo?",
        opciones,
        key=f"{prefix}_objetivo",
        index=None,
        horizontal=True,
    )
    return eleccion, eleccion is None


def render_opciones_sinono(q, prefix):
    """
    Muestra las opciones como tabla estilo Microsoft:
    columna de entidades + columna de valores para cada opción.
    """
    opciones = q["opciones"]
    # Extraer cabeceras de entidades desde la primera opción
    primera = parsear_sinono(opciones[0])
    entidades = [e for e, _ in primera]

    # Cabecera de la tabla
    cols = st.columns([3] + [1] * len(entidades))
    cols[0].markdown("**Opción**")
    for i, ent in enumerate(entidades):
        cols[i + 1].markdown(f"**{ent}**")

    st.divider()

    eleccion = st.radio(
        "Selecciona la combinación correcta:",
        opciones,
        key=f"{prefix}_sinono",
        index=None,
        label_visibility="collapsed",
        format_func=lambda op: "",   # ocultamos el label del radio, lo mostramos manualmente
    )

    # Mostrar cada opción como fila de tabla con el radio a la izquierda
    # Streamlit no permite radio con formato custom, así que renderizamos
    # la tabla por separado y el radio debajo
    for op in opciones:
        partes = parsear_sinono(op)
        letra = re.match(r'^([A-Z])\.', op)
        letra_str = letra.group(1) if letra else "?"
        row_cols = st.columns([0.4, 2.6] + [1] * len(partes))
        selected = (eleccion == op)
        row_cols[0].markdown(f"{'🔵' if selected else '⚪'}")
        row_cols[1].markdown(f"**{letra_str}.**")
        for i, (_, val) in enumerate(partes):
            color = "green" if val.lower() in ("sí", "si") else "red"
            row_cols[i + 2].markdown(f":{color}[**{val}**]")

    return eleccion, eleccion is None


def render_feedback(q, eleccion, tipo):
    """Muestra el resultado tras confirmar, según el tipo."""
    correctas = q["correctas"]
    acierto = es_correcta(eleccion, q)
    opciones = q["opciones"]

    if acierto:
        st.success("✅ ¡Correcto!")
    else:
        st.error("❌ Incorrecto")

    if tipo == "sinono":
        # Tabla comparativa: tu respuesta vs correcta
        correcta_op = correctas[0] if correctas else ""
        partes_correcta = parsear_sinono(correcta_op)
        partes_eleccion = parsear_sinono(eleccion) if eleccion else []
        entidades = [e for e, _ in partes_correcta]

        st.markdown("**Respuesta correcta:**")
        cols = st.columns([2] + [1] * len(entidades))
        cols[0].markdown("*Entidad*")
        for i, ent in enumerate(entidades):
            cols[i + 1].markdown(f"**{ent}**")

        for i, (ent, val_correcto) in enumerate(partes_correcta):
            val_dado = partes_eleccion[i][1] if i < len(partes_eleccion) else "—"
            ok = val_dado.lower() == val_correcto.lower()
            row = st.columns([2] + [1] * len(entidades))
            row[0].write(ent)
            # Mostramos solo la columna de este item
            for j in range(len(entidades)):
                if j == i:
                    if ok:
                        row[j + 1].markdown(f":green[**{val_correcto}** ✅]")
                    else:
                        row[j + 1].markdown(f":red[~~{val_dado}~~ → **{val_correcto}**]")
                else:
                    row[j + 1].write("")

    else:
        for op in opciones:
            es_c = op in correctas
            es_e = op in eleccion if isinstance(eleccion, list) else op == eleccion
            if es_c and es_e:
                st.success(f"✅ {op}")
            elif es_c:
                st.success(f"✅ {op} ← Respuesta correcta")
            elif es_e:
                st.error(f"❌ {op}  ← Tu respuesta")
            else:
                st.write(f"　{op}")


# ─────────────────────────────────────────────
# LÓGICA PRINCIPAL
# ─────────────────────────────────────────────

def es_correcta(eleccion, q):
    if q.get("multi"):
        return sorted(eleccion) == sorted(q["correctas"])
    else:
        return eleccion == q["correcta"]


def _init_exam(questions):
    shuffled = random.sample(questions, min(LIMITE, len(questions)))
    st.session_state.questions = shuffled
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.incorrectas = 0
    st.session_state.answers = {}
    st.session_state.show_result = False
    st.session_state.feedback_idx = None
    st.session_state.repaso_mode = False
    st.session_state.repaso_list = []
    st.session_state.repaso_index = 0
    st.session_state.repaso_answers = {}
    st.session_state.repaso_feedback_idx = None
    st.session_state.repaso_done = False


def render_pregunta(q, prefix, feedback_active, stored_answer):
    """
    Renderiza una pregunta completa (enunciado + opciones o feedback).
    Devuelve (eleccion_actual, confirmar_disabled) si no hay feedback,
    o None si estamos en modo feedback.
    """
    tipo = detectar_tipo(q)
    is_multi = q.get("multi", False)

    st.subheader(q["pregunta"])

    # Indicadores de tipo
    if tipo == "sinono":
        st.caption("📊 Selecciona la combinación correcta de Sí / No")
    elif tipo == "objetivo":
        st.caption("🎯 ¿Cumple esto el objetivo?")
    elif is_multi:
        st.caption(f"⚠️ Selecciona las {len(q['correctas'])} respuestas correctas")

    if feedback_active:
        render_feedback(q, stored_answer, tipo)
        return None, None

    # Modo normal: elegir
    if tipo == "sinono":
        return render_opciones_sinono(q, prefix)
    elif tipo == "objetivo":
        return render_opciones_objetivo(q, prefix)
    else:
        return render_opciones_normal(q, prefix, is_multi)


uploaded = st.file_uploader("Sube tu archivo Word (.docx)", type="docx")

if uploaded:
    questions = parse_exam(uploaded)

    if not questions:
        st.error("No se encontraron preguntas. Revisa el formato del Word.")
        st.stop()

    if "questions" not in st.session_state:
        _init_exam(questions)

    if st.sidebar.button("🔄 Reiniciar examen"):
        _init_exam(questions)
        st.rerun()

    q_list = st.session_state.questions
    total = len(q_list)
    idx = st.session_state.index

    st.sidebar.markdown(f"**Total preguntas en el banco:** {len(questions)}")
    st.sidebar.markdown(f"**Preguntas en este examen:** {total}")

    # ─────────────────────────────────────────────
    # MODO REPASO DE INCORRECTAS
    # ─────────────────────────────────────────────
    if st.session_state.repaso_mode:
        repaso_list = st.session_state.repaso_list
        r_total = len(repaso_list)
        r_idx = st.session_state.repaso_index

        st.info(f"🔁 Modo repaso — {r_total} preguntas incorrectas")

        if st.session_state.repaso_done:
            aciertos_repaso = sum(
                1 for i, q in enumerate(repaso_list)
                if es_correcta(st.session_state.repaso_answers.get(i, [] if q.get("multi") else ""), q)
            )
            pct = round(aciertos_repaso / r_total * 100)
            if pct >= 70:
                st.success(f"## ✅ Repaso completado — {aciertos_repaso}/{r_total} ({pct}%)")
            else:
                st.warning(f"## 🔁 Repaso completado — {aciertos_repaso}/{r_total} ({pct}%)")

            col1, col2 = st.columns(2)
            if col1.button("🔄 Repetir repaso"):
                st.session_state.repaso_index = 0
                st.session_state.repaso_answers = {}
                st.session_state.repaso_feedback_idx = None
                st.session_state.repaso_done = False
                st.rerun()
            if col2.button("🏠 Volver al inicio"):
                _init_exam(questions)
                st.rerun()

        elif r_idx < r_total:
            q = repaso_list[r_idx]

            st.progress(r_idx / r_total)
            col1, col2 = st.columns(2)
            col1.metric("Pregunta", f"{r_idx + 1} / {r_total}")

            feedback_active = st.session_state.repaso_feedback_idx == r_idx
            stored = st.session_state.repaso_answers.get(r_idx)

            eleccion_actual, confirmar_disabled = render_pregunta(
                q, f"repaso_{r_idx}", feedback_active, stored
            )

            if feedback_active:
                if st.button("➡️ Siguiente", key="repaso_next"):
                    st.session_state.repaso_feedback_idx = None
                    st.session_state.repaso_index += 1
                    if st.session_state.repaso_index >= r_total:
                        st.session_state.repaso_done = True
                    st.rerun()
            else:
                if st.button("✅ Confirmar", disabled=confirmar_disabled, key="repaso_confirmar"):
                    st.session_state.repaso_answers[r_idx] = eleccion_actual
                    st.session_state.repaso_feedback_idx = r_idx
                    st.rerun()

    # ─────────────────────────────────────────────
    # EXAMEN NORMAL
    # ─────────────────────────────────────────────
    elif idx < total and not st.session_state.show_result:
        q = q_list[idx]

        st.progress(idx / total)
        col1, col2, col3 = st.columns(3)
        col1.metric("Pregunta", f"{min(idx + 1, total)} / {total}")
        col2.metric("✅ Correctas", st.session_state.score)
        col3.metric("❌ Incorrectas", st.session_state.incorrectas)

        feedback_active = st.session_state.feedback_idx == idx
        stored = st.session_state.answers.get(idx)

        eleccion_actual, confirmar_disabled = render_pregunta(
            q, f"q_{idx}", feedback_active, stored
        )

        if feedback_active:
            if st.button("➡️ Siguiente pregunta"):
                st.session_state.feedback_idx = None
                st.session_state.index += 1
                if st.session_state.index >= total:
                    st.session_state.show_result = True
                st.rerun()
        else:
            if st.button("✅ Confirmar respuesta", disabled=confirmar_disabled):
                st.session_state.answers[idx] = eleccion_actual
                st.session_state.feedback_idx = idx
                if es_correcta(eleccion_actual, q):
                    st.session_state.score += 1
                else:
                    st.session_state.incorrectas += 1
                st.rerun()

    # ─────────────────────────────────────────────
    # RESULTADOS FINALES
    # ─────────────────────────────────────────────
    elif st.session_state.show_result or idx >= total:
        score = st.session_state.score
        incorrectas_count = st.session_state.incorrectas
        pct = round(score / total * 100)

        if pct >= 70:
            st.balloons()
            st.success(f"## ✅ Aprobado — {score}/{total} ({pct}%)")
        else:
            st.error(f"## ❌ Suspenso — {score}/{total} ({pct}%)")
            st.info("Revisa las preguntas incorrectas abajo y vuelve a intentarlo 💪")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", total)
        col2.metric("✅ Correctas", score)
        col3.metric("❌ Incorrectas", incorrectas_count)

        errores = [(i, q) for i, q in enumerate(q_list)
                   if not es_correcta(st.session_state.answers.get(i, [] if q.get("multi") else ""), q)]

        if errores:
            st.divider()
            if st.button(f"🔁 Repasar {len(errores)} preguntas incorrectas", type="primary"):
                st.session_state.repaso_mode = True
                st.session_state.repaso_list = [q for _, q in errores]
                st.session_state.repaso_index = 0
                st.session_state.repaso_answers = {}
                st.session_state.repaso_feedback_idx = None
                st.session_state.repaso_done = False
                st.rerun()

        st.divider()
        tab1, tab2 = st.tabs(["📋 Todas las respuestas", "❌ Solo errores"])

        def render_revision(i, q):
            tu_resp = st.session_state.answers.get(i, [] if q.get("multi") else "—")
            acierto = es_correcta(tu_resp, q)
            icono = "✅" if acierto else "❌"
            tipo = detectar_tipo(q)
            with st.expander(f"{icono} {q['pregunta'][:80]}"):
                if tipo == "sinono":
                    correcta_op = q["correctas"][0] if q["correctas"] else ""
                    partes_c = parsear_sinono(correcta_op)
                    partes_e = parsear_sinono(tu_resp) if isinstance(tu_resp, str) else []
                    if partes_c:
                        cols = st.columns([2] + [1] * len(partes_c))
                        cols[0].markdown("*Entidad*")
                        for j, (ent, _) in enumerate(partes_c):
                            cols[j + 1].markdown(f"**{ent}**")
                        for j, (ent, val_c) in enumerate(partes_c):
                            val_e = partes_e[j][1] if j < len(partes_e) else "—"
                            ok = val_e.lower() == val_c.lower()
                            row = st.columns([2] + [1] * len(partes_c))
                            row[0].write(ent)
                            for k in range(len(partes_c)):
                                if k == j:
                                    if ok:
                                        row[k + 1].markdown(f":green[**{val_c}** ✅]")
                                    else:
                                        row[k + 1].markdown(f":red[~~{val_e}~~ → **{val_c}**]")
                                else:
                                    row[k + 1].write("")
                    else:
                        st.markdown(f"✅ **Correcta:** {correcta_op}")
                else:
                    for op in q["opciones"]:
                        es_c = op in q["correctas"]
                        es_e = op in tu_resp if isinstance(tu_resp, list) else op == tu_resp
                        if es_c and es_e:
                            st.markdown(f"✅ **{op}** ← Correcto")
                        elif es_c:
                            st.markdown(f"✅ **{op}** ← Respuesta correcta")
                        elif es_e:
                            st.markdown(f"❌ ~~{op}~~ ← Tu respuesta")
                        else:
                            st.markdown(f"　{op}")

        with tab1:
            for i, q in enumerate(q_list):
                render_revision(i, q)

        with tab2:
            if not errores:
                st.success("¡Sin errores! 🎉")
            else:
                st.caption(f"{len(errores)} preguntas incorrectas")
                for i, q in errores:
                    render_revision(i, q)
