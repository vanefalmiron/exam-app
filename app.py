import streamlit as st
import random
from parser import parse_exam

st.set_page_config(page_title="Examen ASIR", page_icon="📝", layout="centered")
st.title("📝 Práctica de examen")

LIMITE = 50

uploaded = st.file_uploader("Sube tu archivo Word (.docx)", type="docx")

if uploaded:
    questions = parse_exam(uploaded)

    if not questions:
        st.error("No se encontraron preguntas. Revisa el formato del Word.")
        st.stop()

    # Inicializar sesión
    if "questions" not in st.session_state:
        shuffled = random.sample(questions, min(LIMITE, len(questions)))
        st.session_state.questions = shuffled
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.incorrectas = 0
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.session_state.feedback_idx = None

    # Botón reiniciar
    if st.sidebar.button("🔄 Reiniciar examen"):
        shuffled = random.sample(questions, min(LIMITE, len(questions)))
        st.session_state.questions = shuffled
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.incorrectas = 0
        st.session_state.answers = {}
        st.session_state.show_result = False
        st.session_state.feedback_idx = None
        st.rerun()

    q_list = st.session_state.questions
    total = len(q_list)
    idx = st.session_state.index

    st.sidebar.markdown(f"**Total preguntas en el banco:** {len(questions)}")
    st.sidebar.markdown(f"**Preguntas en este examen:** {total}")

    # Barra de progreso y contador
    st.progress(idx / total)
    col1, col2, col3 = st.columns(3)
    col1.metric("Pregunta", f"{min(idx + 1, total)} / {total}")
    col2.metric("✅ Correctas", st.session_state.score)
    col3.metric("❌ Incorrectas", st.session_state.incorrectas)

    # --- Pregunta activa ---
    if idx < total and not st.session_state.show_result:
        q = q_list[idx]
        st.subheader(q["pregunta"])

        # Las opciones vienen ordenadas A,B,C,D del parser — NO mezclar
        opciones = q["opciones"]

        # MODO FEEDBACK: mostrar resultado tras confirmar
        if st.session_state.feedback_idx == idx:
            eleccion = st.session_state.answers[idx]
            correcta = q["correcta"]

            if eleccion == correcta:
                st.success("✅ ¡Correcto!")
            else:
                st.error("❌ Incorrecto")

            # Mostrar opciones con colores, sin radio
            for op in opciones:
                if op == correcta:
                    st.success(f"✅ {op}")
                elif op == eleccion:
                    st.error(f"❌ {op}  ← Tu respuesta")
                else:
                    st.write(f"　{op}")

            if st.button("➡️ Siguiente pregunta"):
                st.session_state.feedback_idx = None
                st.session_state.index += 1
                if st.session_state.index >= total:
                    st.session_state.show_result = True
                st.rerun()

        # MODO NORMAL: elegir respuesta
        else:
            eleccion = st.radio("Elige una opción:", opciones, key=f"q_{idx}", index=None)

            if st.button("✅ Confirmar respuesta", disabled=eleccion is None):
                correcta = q["correcta"]
                st.session_state.answers[idx] = eleccion
                st.session_state.feedback_idx = idx

                if eleccion == correcta:
                    st.session_state.score += 1
                else:
                    st.session_state.incorrectas += 1

                st.rerun()

    # --- Resultados finales ---
    elif st.session_state.show_result or idx >= total:
        score = st.session_state.score
        incorrectas = st.session_state.incorrectas
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
        col3.metric("❌ Incorrectas", incorrectas)

        # Repaso
        st.divider()
        tab1, tab2 = st.tabs(["📋 Todas las respuestas", "❌ Solo errores"])

        with tab1:
            for i, q in enumerate(q_list):
                tu_resp = st.session_state.answers.get(i, "—")
                correcta = q["correcta"]
                icono = "✅" if tu_resp == correcta else "❌"
                with st.expander(f"{icono} {q['pregunta'][:80]}"):
                    for op in q["opciones"]:
                        if op == correcta:
                            st.markdown(f"✅ **{op}** ← Respuesta correcta")
                        elif op == tu_resp and tu_resp != correcta:
                            st.markdown(f"❌ ~~{op}~~ ← Tu respuesta")
                        else:
                            st.markdown(f"　{op}")

        with tab2:
            errores = [(i, q) for i, q in enumerate(q_list)
                       if st.session_state.answers.get(i) != q["correcta"]]
            if not errores:
                st.success("¡Sin errores! 🎉")
            else:
                st.caption(f"{len(errores)} preguntas incorrectas")
                for i, q in errores:
                    tu_resp = st.session_state.answers.get(i, "—")
                    with st.expander(f"❌ {q['pregunta'][:80]}"):
                        for op in q["opciones"]:
                            if op == q["correcta"]:
                                st.markdown(f"✅ **{op}** ← Respuesta correcta")
                            elif op == tu_resp:
                                st.markdown(f"❌ ~~{op}~~ ← Tu respuesta")
                            else:
                                st.markdown(f"　{op}")
