import streamlit as st
import random
from parser import parse_exam

st.set_page_config(page_title="Examen ASIR", page_icon="📝", layout="centered")
st.title("📝 Práctica de examen")

LIMITE = 50

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

def render_opciones(q, prefix, is_multi):
    opciones = q["opciones"]
    n = q.get("n_correctas", len(q["correctas"]))
    if is_multi:
        seleccion = []
        for op in opciones:
            if st.checkbox(op, key=f"{prefix}_check_{op}"):
                seleccion.append(op)
        confirmar_disabled = len(seleccion) != n
        if seleccion and confirmar_disabled:
            st.caption(f"Selecciona exactamente {n} opciones (llevas {len(seleccion)})")
        return seleccion, confirmar_disabled
    else:
        eleccion = st.radio("Elige una opción:", opciones, key=f"{prefix}_radio", index=None)
        return eleccion, eleccion is None

def render_feedback(q, eleccion):
    correctas = q["correctas"]
    acierto = es_correcta(eleccion, q)
    if acierto:
        st.success("✅ ¡Correcto!")
    else:
        st.error("❌ Incorrecto")
    for op in q["opciones"]:
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
            is_multi = q.get("multi", False)

            st.progress(r_idx / r_total)
            col1, col2 = st.columns(2)
            col1.metric("Pregunta", f"{r_idx + 1} / {r_total}")
            col2.metric("Tipo", f"☝️ {q.get('n_correctas',1)} respuesta(s)")

            st.subheader(q["pregunta"])
            if is_multi:
                st.caption(f"⚠️ Selecciona las {q.get('n_correctas', len(q['correctas']))} respuestas correctas")

            if st.session_state.repaso_feedback_idx == r_idx:
                render_feedback(q, st.session_state.repaso_answers[r_idx])
                if st.button("➡️ Siguiente", key="repaso_next"):
                    st.session_state.repaso_feedback_idx = None
                    st.session_state.repaso_index += 1
                    if st.session_state.repaso_index >= r_total:
                        st.session_state.repaso_done = True
                    st.rerun()
            else:
                eleccion_actual, confirmar_disabled = render_opciones(q, f"repaso_{r_idx}", is_multi)
                if st.button("✅ Confirmar", disabled=confirmar_disabled, key="repaso_confirmar"):
                    st.session_state.repaso_answers[r_idx] = eleccion_actual
                    st.session_state.repaso_feedback_idx = r_idx
                    st.rerun()

    # ─────────────────────────────────────────────
    # EXAMEN NORMAL
    # ─────────────────────────────────────────────
    elif idx < total and not st.session_state.show_result:
        q = q_list[idx]
        is_multi = q.get("multi", False)

        st.progress(idx / total)
        col1, col2, col3 = st.columns(3)
        col1.metric("Pregunta", f"{min(idx + 1, total)} / {total}")
        col2.metric("✅ Correctas", st.session_state.score)
        col3.metric("❌ Incorrectas", st.session_state.incorrectas)

        st.subheader(q["pregunta"])
        if is_multi:
            st.caption(f"⚠️ Selecciona las {q.get('n_correctas', len(q['correctas']))} respuestas correctas")

        if st.session_state.feedback_idx == idx:
            render_feedback(q, st.session_state.answers[idx])
            if st.button("➡️ Siguiente pregunta"):
                st.session_state.feedback_idx = None
                st.session_state.index += 1
                if st.session_state.index >= total:
                    st.session_state.show_result = True
                st.rerun()
        else:
            eleccion_actual, confirmar_disabled = render_opciones(q, f"q_{idx}", is_multi)
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
            with st.expander(f"{icono} {q['pregunta'][:80]}"):
                if q.get("multi"):
                    st.caption(f"Pregunta de {q.get('n_correctas', len(q['correctas']))} respuestas correctas")
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
