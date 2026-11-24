
import streamlit as st
import requests
import random
import string
import json
import time
from streamlit_autorefresh import st_autorefresh

# ==================================================
# QUIZ ARENA 3.0 - TIMER EDITION
# STREAMLIT + SUPABASE
# ==================================================

st.set_page_config(
    page_title="QUIZ ARENA 3.0",
    page_icon="🎮",
    layout="wide"
)

# ---------------- CONFIGURATION -------------------

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
except Exception:
    st.error("Configuration Supabase introuvable.")
    st.stop()

if "/rest/v1" in SUPABASE_URL:
    st.error("La SUPABASE_URL doit se terminer par .supabase.co")
    st.stop()

API = SUPABASE_URL + "/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ---------------- DATABASE FUNCTIONS ---------------

def db_get(table, params=None):
    r = requests.get(
        f"{API}/{table}",
        headers=HEADERS,
        params=params or {},
        timeout=15
    )
    if not r.ok:
        raise Exception(r.text)
    return r.json()


def db_post(table, data):
    r = requests.post(
        f"{API}/{table}",
        headers=HEADERS,
        json=data,
        timeout=15
    )
    if not r.ok:
        raise Exception(r.text)
    return r.json()


def db_patch(table, params, data):
    r = requests.patch(
        f"{API}/{table}",
        headers=HEADERS,
        params=params,
        json=data,
        timeout=15
    )
    if not r.ok:
        raise Exception(r.text)
    return r.json()


# ---------------- TIMER SYSTEM ---------------------

TIME_LIMIT = 15


def calculate_points(elapsed):
    if elapsed <= 2:
        return 1000
    elif elapsed <= 5:
        return 800
    elif elapsed <= 8:
        return 600
    elif elapsed <= 11:
        return 400
    else:
        return 200


def show_timer(start_time, key):
    st_autorefresh(
        interval=250,
        key=key
    )

    elapsed = max(0, time.time() - start_time)
    remaining = max(0, TIME_LIMIT - elapsed)

    if remaining > 10:
        color = "#67e8f9"
    elif remaining > 5:
        color = "#fbbf24"
    else:
        color = "#fb7185"

    st.markdown(
        f"""
        <div style="
            background:#151d32;
            border:1px solid #344263;
            border-radius:16px;
            padding:14px;
            text-align:center;">
            <div style="font-size:14px;color:#cbd5e1;">
                TEMPS RESTANT
            </div>
            <div style="
                font-size:40px;
                font-weight:900;
                color:{color};">
                {remaining:04.1f} s
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(remaining / TIME_LIMIT)

    return elapsed, remaining


# ---------------- DESIGN ---------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

.stApp {
    background:
    radial-gradient(circle at 10% 10%, #30205b 0%, transparent 35%),
    radial-gradient(circle at 90% 20%, #103e58 0%, transparent 35%),
    #090d1b;
    color: white;
    font-family: Inter, sans-serif;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
}

.hero {
    background: linear-gradient(120deg,#44258b,#155b83);
    border: 1px solid #6551b7;
    border-radius: 25px;
    padding: 35px 15px;
    text-align: center;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 55px;
    font-weight: 900;
    letter-spacing: -3px;
    background: linear-gradient(90deg,#fff,#67e8f9,#d8b4fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: #dbeafe;
    font-size: 16px;
}

.panel {
    background: #151d32;
    border: 1px solid #344263;
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 15px;
}

div.stButton > button {
    width: 100%;
    background: linear-gradient(100deg,#7045d5,#167ca4);
    color: white;
    font-weight: 800;
    border: 0;
    border-radius: 12px;
    min-height: 45px;
}

div.stButton > button:hover {
    border: 1px solid #67e8f9;
    color: white;
}

h1,h2,h3,p,label {
    color: white !important;
}

.metric {
    background: #151d32;
    border: 1px solid #344263;
    padding: 18px;
    border-radius: 15px;
    text-align: center;
}

.code {
    background: #102b43;
    border: 2px dashed #67e8f9;
    border-radius: 15px;
    padding: 20px;
    font-size: 36px;
    font-weight: 900;
    color: #67e8f9;
    text-align: center;
    letter-spacing: 8px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION --------------------------

defaults = {
    "player": None,
    "page": "home",
    "game": None,
    "solo_questions": [],
    "solo_index": 0,
    "solo_score": 0,
    "solo_answered": False,
    "solo_feedback": None,
    "solo_started_at": None,
    "solo_points_earned": 0,
    "solo_timeout": False,
    "multi_timer_question": None,
    "multi_started_at": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def navigate(page):
    st.session_state.page = page
    st.rerun()


# ---------------- PLAYER --------------------------

def login(pseudo):
    pseudo = pseudo.strip()

    if not pseudo:
        st.warning("Entre un pseudo.")
        return

    try:
        players = db_get(
            "players",
            {"pseudo": f"eq.{pseudo}", "limit": "1"}
        )

        if players:
            st.session_state.player = players[0]
        else:
            result = db_post(
                "players",
                {"pseudo": pseudo}
            )

            if not result:
                st.error("Création du joueur impossible.")
                return

            st.session_state.player = result[0]

        st.session_state.page = "home"
        st.rerun()

    except Exception as e:
        st.error(f"Création du joueur impossible : {e}")


# ---------------- QUESTIONS -----------------------

def get_questions(category="Toutes"):
    params = {"select": "*", "limit": "500"}

    if category != "Toutes":
        params["category"] = f"eq.{category}"

    return db_get("questions", params)


def get_categories():
    questions = get_questions()

    return sorted(set(
        q["category"] for q in questions
        if q.get("category")
    ))


def get_options(question):
    options = question.get("options", [])

    if isinstance(options, str):
        options = json.loads(options)

    return options


# ---------------- MULTIPLAYER ---------------------

def create_game():
    player = st.session_state.player

    code = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    try:
        games = db_post("games", {
            "code": code,
            "host_id": player["id"],
            "status": "waiting"
        })

        game = games[0]

        db_post("game_players", {
            "game_id": game["id"],
            "player_id": player["id"],
            "score": 0
        })

        st.session_state.game = game
        navigate("lobby")

    except Exception as e:
        st.error(f"Création de salle impossible : {e}")


def join_game(code):
    try:
        games = db_get("games", {
            "code": f"eq.{code.strip().upper()}",
            "status": "eq.waiting",
            "limit": "1"
        })

        if not games:
            st.error("Salle introuvable.")
            return

        game = games[0]
        player = st.session_state.player

        existing = db_get("game_players", {
            "game_id": f"eq.{game['id']}",
            "player_id": f"eq.{player['id']}",
            "limit": "1"
        })

        if not existing:
            db_post("game_players", {
                "game_id": game["id"],
                "player_id": player["id"],
                "score": 0
            })

        st.session_state.game = game
        navigate("lobby")

    except Exception as e:
        st.error(f"Impossible de rejoindre la salle : {e}")


def get_room_players(game_id):
    links = db_get("game_players", {
        "game_id": f"eq.{game_id}"
    })

    result = []

    for link in links:
        people = db_get("players", {
            "id": f"eq.{link['player_id']}",
            "limit": "1"
        })

        if people:
            result.append({
                "pseudo": people[0]["pseudo"],
                "score": link.get("score", 0)
            })

    return result


def refresh_game():
    game = st.session_state.game

    games = db_get("games", {
        "id": f"eq.{game['id']}",
        "limit": "1"
    })

    if games:
        st.session_state.game = games[0]


def start_game():
    game = st.session_state.game

    questions = get_questions()

    if not questions:
        st.error("Aucune question disponible.")
        return

    db_patch("games", {
        "id": f"eq.{game['id']}"
    }, {"status": "playing"})

    st.session_state.game = {
        **game,
        "status": "playing"
    }

    st.session_state.multi_timer_question = None
    st.session_state.multi_started_at = None

    navigate("multiplayer")


# ---------------- ANSWERS --------------------------

def has_answered(game_id, player_id, question_id):
    answers = db_get("game_answers", {
        "game_id": f"eq.{game_id}",
        "player_id": f"eq.{player_id}",
        "question_id": f"eq.{question_id}",
        "limit": "1"
    })

    return bool(answers)


def submit_multiplayer_answer(question, answer_index, points=0):
    game = st.session_state.game
    player = st.session_state.player

    try:
        if has_answered(
            game["id"],
            player["id"],
            question["id"]
        ):
            return None

        db_post("game_answers", {
            "game_id": game["id"],
            "player_id": player["id"],
            "question_id": question["id"],
            "answer_index": answer_index
        })

        correct = (
            answer_index >= 0
            and answer_index == int(question["correct_index"])
        )

        if correct and points > 0:
            links = db_get("game_players", {
                "game_id": f"eq.{game['id']}",
                "player_id": f"eq.{player['id']}",
                "limit": "1"
            })

            if links:
                score = links[0].get("score", 0)

                db_patch("game_players", {
                    "id": f"eq.{links[0]['id']}"
                }, {
                    "score": score + int(points)
                })

        return correct

    except Exception as e:
        st.error(f"Erreur de réponse : {e}")
        return False


# ---------------- LEADERBOARD -------------------

def show_leaderboard():
    st.markdown("## 🏆 CLASSEMENT")

    try:
        links = db_get("game_players", {
            "select": "*",
            "limit": "500"
        })

        scores = {}

        for link in links:
            pid = link["player_id"]
            scores[pid] = (
                scores.get(pid, 0) + link.get("score", 0)
            )

        ranking = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for i, (pid, score) in enumerate(ranking, 1):

            players = db_get("players", {
                "id": f"eq.{pid}",
                "limit": "1"
            })

            if players:
                medal = (
                    "🥇" if i == 1 else
                    "🥈" if i == 2 else
                    "🥉" if i == 3 else
                    "🏅"
                )

                st.markdown(
                    f"""
                    <div class="panel">
                    {medal} <b>{i}. {players[0]['pseudo']}</b>
                    <span style="float:right;color:#67e8f9">
                    {score} points
                    </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        if not ranking:
            st.info("Le classement est encore vide.")

    except Exception as e:
        st.error(f"Classement indisponible : {e}")


# ==================================================
# APPLICATION
# ==================================================

st.markdown("""
<div class="hero">
<h1>QUIZ ARENA</h1>
<p>3.0 · PLAY · COMPETE · WIN</p>
</div>
""", unsafe_allow_html=True)

player = st.session_state.player


# ---------------- LOGIN ----------------------------

if not player:

    st.markdown("## 👤 Bienvenue dans l'arène")

    st.markdown(
        '<div class="panel">Entre ton pseudo pour commencer à jouer.</div>',
        unsafe_allow_html=True
    )

    pseudo = st.text_input(
        "Ton pseudo",
        placeholder="Choisis ton pseudo..."
    )

    if st.button("ENTRER DANS L'ARÈNE"):
        login(pseudo)

    st.stop()


# ---------------- NAVIGATION -----------------------

col1, col2 = st.columns([4, 1])

with col1:
    st.markdown(f"### 👤 {player['pseudo']}")

with col2:
    if st.button("Déconnexion"):
        st.session_state.player = None
        st.session_state.game = None
        st.session_state.multi_timer_question = None
        st.session_state.multi_started_at = None
        navigate("home")

st.divider()


# ---------------- HOME -----------------------------

if st.session_state.page == "home":

    st.markdown("## Bienvenue, champion !")
    st.write("Choisis ton mode de jeu.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="panel">
        <h2>🎯 SOLO</h2>
        Entraîne-toi et bats ton record.
        </div>
        """, unsafe_allow_html=True)

        if st.button("JOUER EN SOLO"):
            navigate("solo_setup")

    with c2:
        st.markdown("""
        <div class="panel">
        <h2>⚡ MULTIJOUEUR</h2>
        Défie tes amis en ligne.
        </div>
        """, unsafe_allow_html=True)

        if st.button("JOUER EN MULTI"):
            navigate("multi")

    with c3:
        st.markdown("""
        <div class="panel">
        <h2>🏆 CLASSEMENT</h2>
        Découvre les meilleurs joueurs.
        </div>
        """, unsafe_allow_html=True)

        if st.button("VOIR LE CLASSEMENT"):
            navigate("ranking")


# ---------------- SOLO SETUP ----------------------

elif st.session_state.page == "solo_setup":

    st.markdown("## 🎯 MODE SOLO")

    try:
        categories = ["Toutes"] + get_categories()

        category = st.selectbox(
            "Choisir une catégorie",
            categories
        )

        number = st.selectbox(
            "Nombre de questions",
            [5, 10, 15, 20]
        )

        if st.button("COMMENCER LA PARTIE"):

            questions = get_questions(category)
            random.shuffle(questions)

            st.session_state.solo_questions = questions[:number]
            st.session_state.solo_index = 0
            st.session_state.solo_score = 0
            st.session_state.solo_answered = False
            st.session_state.solo_feedback = None
            st.session_state.solo_points_earned = 0
            st.session_state.solo_timeout = False
            st.session_state.solo_started_at = time.time()

            if not questions:
                st.warning("Aucune question disponible.")
            else:
                navigate("solo_game")

    except Exception as e:
        st.error(f"Erreur : {e}")

    if st.button("RETOUR"):
        navigate("home")


# ---------------- SOLO GAME -----------------------

elif st.session_state.page == "solo_game":

    questions = st.session_state.solo_questions
    index = st.session_state.solo_index

    if index >= len(questions):

        st.balloons()
        st.markdown("## 🏁 PARTIE TERMINÉE !")

        st.metric(
            "TON SCORE",
            st.session_state.solo_score
        )

        if st.button("RETOUR À L'ACCUEIL"):
            navigate("home")

    else:

        q = questions[index]

        st.progress((index + 1) / len(questions))

        st.caption(
            f"QUESTION {index + 1}/{len(questions)}"
        )

        st.markdown(f"## {q['question']}")

        options = get_options(q)

        if not st.session_state.solo_answered:

            if st.session_state.solo_started_at is None:
                st.session_state.solo_started_at = time.time()

            elapsed, remaining = show_timer(
                st.session_state.solo_started_at,
                f"solo_timer_{index}"
            )

            if remaining <= 0:
                st.session_state.solo_answered = True
                st.session_state.solo_feedback = False
                st.session_state.solo_timeout = True
                st.session_state.solo_points_earned = 0
                st.rerun()

            choice = st.radio(
                "Choisis ta réponse :",
                options,
                index=None,
                key=f"solo_{index}"
            )

            if st.button("VALIDER MA RÉPONSE"):

                elapsed = (
                    time.time()
                    - st.session_state.solo_started_at
                )

                if choice is None:
                    st.warning("Choisis une réponse.")

                elif elapsed >= TIME_LIMIT:

                    st.session_state.solo_answered = True
                    st.session_state.solo_feedback = False
                    st.session_state.solo_timeout = True
                    st.session_state.solo_points_earned = 0
                    st.rerun()

                else:

                    answer = options.index(choice)

                    correct = (
                        answer == int(q["correct_index"])
                    )

                    points = (
                        calculate_points(elapsed)
                        if correct else 0
                    )

                    if correct:
                        st.session_state.solo_score += points

                    st.session_state.solo_feedback = correct
                    st.session_state.solo_answered = True
                    st.session_state.solo_points_earned = points
                    st.session_state.solo_timeout = False

                    st.rerun()

        else:

            if st.session_state.solo_timeout:
                st.error("⏰ TEMPS ÉCOULÉ ! 0 POINTS")

            elif st.session_state.solo_feedback:
                st.success(
                    f"Bonne réponse ! +{st.session_state.solo_points_earned} points"
                )

            else:
                st.error("Mauvaise réponse. 0 point.")

            if q.get("explanation"):
                st.info(q["explanation"])

            if st.button("QUESTION SUIVANTE"):

                st.session_state.solo_index += 1
                st.session_state.solo_answered = False
                st.session_state.solo_feedback = None
                st.session_state.solo_points_earned = 0
                st.session_state.solo_timeout = False
                st.session_state.solo_started_at = time.time()

                st.rerun()

    if st.button("QUITTER"):
        st.session_state.solo_started_at = None
        navigate("home")


# ---------------- MULTIPLAYER MENU -----------------

elif st.session_state.page == "multi":

    st.markdown("## ⚡ MULTIJOUEUR")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="panel">
        <h2>➕ CRÉER UNE SALLE</h2>
        Crée ta propre partie et invite tes amis.
        </div>
        """, unsafe_allow_html=True)

        if st.button("CRÉER UNE SALLE"):
            create_game()

    with c2:
        st.markdown("""
        <div class="panel">
        <h2>🔑 REJOINDRE</h2>
        Entre le code de ton ami.
        </div>
        """, unsafe_allow_html=True)

        code = st.text_input(
            "Code de la salle",
            max_chars=6
        )

        if st.button("REJOINDRE LA SALLE"):
            join_game(code)

    if st.button("RETOUR"):
        navigate("home")


# ---------------- LOBBY ----------------------------

elif st.session_state.page == "lobby":

    refresh_game()
    game = st.session_state.game

    st.markdown("## 🎮 SALLE D'ATTENTE")

    st.markdown(
        f'<div class="code">{game["code"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 👥 JOUEURS CONNECTÉS")

    try:
        people = get_room_players(game["id"])

        for person in people:
            st.markdown(
                f"- 🟢 **{person['pseudo']}**"
            )

        st.caption(f"{len(people)} joueur(s)")

    except Exception as e:
        st.error(str(e))

    is_host = (
        str(game["host_id"]) == str(player["id"])
    )

    if is_host:

        if st.button("🚀 LANCER LA PARTIE"):
            try:
                start_game()
            except Exception as e:
                st.error(f"Impossible de lancer : {e}")

    else:
        st.info("En attente du lancement par l'hôte...")

    if st.button("ACTUALISER LA SALLE"):
        st.rerun()

    if st.button("QUITTER LA SALLE"):
        st.session_state.game = None
        navigate("multi")


# ---------------- MULTIPLAYER GAME -----------------

elif st.session_state.page == "multiplayer":

    refresh_game()
    game = st.session_state.game

    if game["status"] == "finished":

        st.markdown("## 🏁 PARTIE TERMINÉE")

        try:
            people = get_room_players(game["id"])

            for person in sorted(
                people,
                key=lambda x: x["score"],
                reverse=True
            ):
                st.write(
                    f"🏆 {person['pseudo']} — {person['score']} points"
                )

        except Exception as e:
            st.error(str(e))

        if st.button("ACCUEIL"):
            st.session_state.game = None
            st.session_state.multi_timer_question = None
            st.session_state.multi_started_at = None
            navigate("home")

    else:

        st.markdown("## ⚡ PARTIE MULTIJOUEUR")

        try:
            all_questions = get_questions()

            # Same question order for all players in the room.
            rng = random.Random(game["code"])
            rng.shuffle(all_questions)

            questions = all_questions[:10]

            if not questions:
                st.warning("Aucune question disponible.")

            else:

                player_answers = db_get("game_answers", {
                    "game_id": f"eq.{game['id']}",
                    "player_id": f"eq.{player['id']}"
                })

                answered_ids = {
                    str(a["question_id"])
                    for a in player_answers
                }

                remaining_questions = [
                    q for q in questions
                    if str(q["id"]) not in answered_ids
                ]

                if not remaining_questions:

                    st.success(
                        "Tu as terminé toutes les questions !"
                    )

                    st.markdown("### 🏆 SCORES")

                    people = get_room_players(game["id"])

                    for person in sorted(
                        people,
                        key=lambda x: x["score"],
                        reverse=True
                    ):
                        st.write(
                            f"**{person['pseudo']}** — {person['score']} points"
                        )

                    if str(game["host_id"]) == str(player["id"]):

                        if st.button("TERMINER LA PARTIE"):

                            db_patch("games", {
                                "id": f"eq.{game['id']}"
                            }, {
                                "status": "finished"
                            })

                            st.rerun()

                    else:
                        st.info(
                            "En attente de la fin de partie par l'hôte."
                        )

                else:

                    q = remaining_questions[0]

                    timer_question = (
                        f"{game['id']}_{q['id']}"
                    )

                    # One timer per player and question.
                    if (
                        st.session_state.multi_timer_question
                        != timer_question
                    ):
                        st.session_state.multi_timer_question = timer_question
                        st.session_state.multi_started_at = time.time()

                    if st.session_state.multi_started_at is None:
                        st.session_state.multi_started_at = time.time()

                    elapsed, remaining_time = show_timer(
                        st.session_state.multi_started_at,
                        f"multi_timer_{timer_question}"
                    )

                    st.progress(
                        len(answered_ids) / len(questions)
                    )

                    st.caption(
                        f"QUESTION {len(answered_ids) + 1}/10"
                    )

                    st.markdown(f"## {q['question']}")

                    if remaining_time <= 0:

                        result = submit_multiplayer_answer(
                            q,
                            -1,
                            0
                        )

                        st.session_state.multi_timer_question = None
                        st.session_state.multi_started_at = None

                        st.warning(
                            "⏰ Temps écoulé. 0 point."
                        )

                        st.rerun()

                    options = get_options(q)

                    choice = st.radio(
                        "Ta réponse :",
                        options,
                        index=None,
                        key=f"multi_{game['id']}_{q['id']}"
                    )

                    if st.button("VALIDER MA RÉPONSE"):

                        elapsed = (
                            time.time()
                            - st.session_state.multi_started_at
                        )

                        if choice is None:
                            st.warning("Choisis une réponse.")

                        elif elapsed >= TIME_LIMIT:

                            submit_multiplayer_answer(
                                q,
                                -1,
                                0
                            )

                            st.session_state.multi_timer_question = None
                            st.session_state.multi_started_at = None

                            st.warning(
                                "⏰ Temps écoulé. 0 point."
                            )

                            st.rerun()

                        else:

                            answer_index = options.index(choice)

                            correct = (
                                answer_index
                                == int(q["correct_index"])
                            )

                            points = (
                                calculate_points(elapsed)
                                if correct else 0
                            )

                            result = submit_multiplayer_answer(
                                q,
                                answer_index,
                                points
                            )

                            st.session_state.multi_timer_question = None
                            st.session_state.multi_started_at = None

                            if result is True:
                                st.success(
                                    f"Bonne réponse ! +{points} points"
                                )

                            elif result is False:
                                st.info(
                                    "Réponse incorrecte. 0 point."
                                )

                            st.rerun()

                if st.button("ACTUALISER"):
                    st.rerun()

        except Exception as e:
            st.error(
                f"Erreur pendant la partie : {e}"
            )


# ---------------- LEADERBOARD ----------------------

elif st.session_state.page == "ranking":

    show_leaderboard()

    if st.button("RETOUR À L'ACCUEIL"):
        navigate("home")


# ---------------- FOOTER ---------------------------

st.divider()

st.markdown(
    """
    <p style="text-align:center;color:#8291b2">
    QUIZ ARENA 3.0 · PLAY · COMPETE · WIN
    </p>
    """,
    unsafe_allow_html=True
)

