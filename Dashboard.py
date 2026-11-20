import tempfile
import speech_recognition as sr
import streamlit as st
import pandas as pd
import mysql.connector
import os

# 1. Page Configuration
st.set_page_config(page_title="Gen 9 Tactical Battle Assistant", layout="wide", page_icon="⚔️")

# Initialize Session State for Battle Tracking
if "battle_active" not in st.session_state:
    st.session_state.battle_active = False
if "current_battle_log" not in st.session_state:
    st.session_state.current_battle_log = []
if "show_post_battle_review" not in st.session_state:
    st.session_state.show_post_battle_review = False
if "pending_review_logs" not in st.session_state:
    st.session_state.pending_review_logs = []
if "enemy_active_pkmn" not in st.session_state:
    st.session_state.enemy_active_pkmn = None

# 2. Sidebar Theme Switcher & Controls
st.sidebar.markdown("### 🎨 Enterprise Theme")
theme_mode = st.sidebar.selectbox("Interface Theme:", ["Light Mode", "Dark Mode"], index=0, key="theme_mode_sel")

if theme_mode == "Light Mode":
    bg_color = "#f8f9fa"
    card_bg = "#ffffff"
    text_color = "#212529"
    sub_text = "#6c757d"
    border_color = "#dee2e6"
    header_color = "#0d6efd"
    attack_bg = "linear-gradient(135deg, #e7f5ff 0%, #d0ebff 100%)"
    attack_text = "#0b5ed7"
    switch_bg = "linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%)"
    switch_text = "#c92a2a"
    success_bg = "linear-gradient(135deg, #ebfbee 0%, #d3f9d8 100%)"
    success_text = "#2b8a3e"
    telemetry_bg = "#ffffff"
else:
    bg_color = "#0e1117"
    card_bg = "#1e1e2f"
    text_color = "#ffffff"
    sub_text = "#a0aabf"
    border_color = "#2d3748"
    header_color = "#ffcb05"
    attack_bg = "linear-gradient(135deg, #002244 0%, #003366 100%)"
    attack_text = "#ffffff"
    switch_bg = "linear-gradient(135deg, #4a0000 0%, #660000 100%)"
    switch_text = "#ffffff"
    success_bg = "linear-gradient(135deg, #004a14 0%, #00661c 100%)"
    success_text = "#ffffff"
    telemetry_bg = "#161a24"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .main {{ background-color: {bg_color}; color: {text_color}; }}
    
    p, span, label, div, h1, h2, h3, h4 {{ color: {text_color} !important; }}
    .game-title {{ text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: {header_color} !important; font-size: 38px; font-weight: 800; letter-spacing: 1px; margin-bottom: 0px; }}
    .project-subtitle {{ text-align: center; color: {sub_text} !important; font-size: 16px; font-style: italic; margin-top: -2px; margin-bottom: 20px; }}
    .section-header {{ font-size: 20px; font-weight: 700; margin-top: 15px; margin-bottom: 12px; color: {text_color} !important; border-bottom: 2px solid {header_color}; padding-bottom: 6px; }}
    
    .pokemon-card {{ background: {card_bg}; padding: 18px; border-radius: 12px; border-left: 6px solid {header_color}; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 15px; border-top: 1px solid {border_color}; border-right: 1px solid {border_color}; border-bottom: 1px solid {border_color}; }}
    .type-badge {{ background-color: {sub_text}; color: white !important; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
    
    .attack-directive {{ background: {attack_bg}; color: {attack_text} !important; padding: 20px; border-radius: 10px; border: 1px solid {border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 16px; }}
    .switch-directive {{ background: {switch_bg}; color: {switch_text} !important; padding: 20px; border-radius: 10px; border: 1px solid {border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 16px; }}
    .success-directive {{ background: {success_bg}; color: {success_text} !important; padding: 20px; border-radius: 10px; border: 1px solid {border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 16px; }}
    
    .highlight {{ font-weight: 800; font-size: 19px; }}
    .telemetry-box {{ background-color: {telemetry_bg}; padding: 12px 18px; border-radius: 8px; border: 1px solid {border_color}; font-family: monospace; font-size: 13px; color: {text_color} !important; margin-bottom: 8px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02); }}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='game-title'>GEN 9 TACTICAL BATTLE ASSISTANT</div>", unsafe_allow_html=True)
st.markdown("<div class='project-subtitle'>Enterprise Relational Database Analytics & Decision Engine</div>", unsafe_allow_html=True)

# 3. Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database="pokemon_analytics",
)

cursor = conn.cursor()
cursor.execute("SELECT Name FROM Creatures ORDER BY Name ASC")
all_creatures = [c[0] for c in cursor.fetchall()]
cursor.close()

MY_TEAM = ["Kingambit", "Iron-valiant", "Garchomp", "Gholdengo", "Dragapult", "Landorus"]

# Sidebar Controls: Squad Health
st.sidebar.markdown("### 🛡️ Active Squad Telemetry")
st.sidebar.caption("Squad Health Checkers (Uncheck if fainted):")

living_team = []
for member in MY_TEAM:
    is_alive = st.sidebar.checkbox(member, value=True, key=f"alive_{member}")
    if is_alive:
        living_team.append(member)

st.sidebar.divider()
st.sidebar.markdown("### ⚡ Dynamic Combat Modifiers")
enemy_scarfed = st.sidebar.checkbox("Enemy Choice Scarf (Speed x1.5)?", value=False, key="enemy_scarf_chk")
my_boost = st.sidebar.selectbox("Offensive Boost Stage (Swords Dance):", [0, 1, 2], index=0, key="my_boost_sel")
enemy_item = st.sidebar.selectbox("Suspected Target Item:", ["None", "Eviolite (1.5x Def/SpD)", "Choice Band / Specs"], index=0, key="enemy_item_sel")
eviolite_multiplier = 1.5 if "Eviolite" in enemy_item else 1.0

# Sidebar Controls: Voice Command Assistant
st.sidebar.divider()
st.sidebar.markdown("### 🎙️ Voice Command Assistant")
st.sidebar.caption("Record opponent Pokémon name hands-free:")

audio_value = st.sidebar.audio_input("Record Opponent Name", key="voice_audio_input")

if audio_value is not None:
    with st.sidebar.spinner("Processing voice input..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_value.getvalue())
            tmp_file_path = tmp_file.name

        r = sr.Recognizer()
        try:
            with sr.AudioFile(tmp_file_path) as source:
                audio_data = r.record(source)

            spoken_text = r.recognize_google(audio_data).title()
            spoken_text = spoken_text.replace(" ", "-")

            st.sidebar.success(f"Heard: '{spoken_text}'")
            if spoken_text in all_creatures:
                st.session_state.enemy_active_pkmn = spoken_text
                st.sidebar.success(f"Locked Target: {spoken_text}!")
                st.rerun()
            else:
                matches = [c for c in all_creatures if spoken_text.lower() in c.lower()]
                if matches:
                    st.session_state.enemy_active_pkmn = matches[0]
                    st.sidebar.success(f"Locked Target: {matches[0]}!")
                    st.rerun()
                else:
                    st.sidebar.warning(f"'{spoken_text}' not found in database.")

        except sr.UnknownValueError:
            st.sidebar.error("Could not understand audio. Speak clearly and try again.")
        except sr.RequestError:
            st.sidebar.error("Speech service unavailable (check internet connection).")

if not living_team:
    st.error("⚠️ All squad members fainted! Check at least one living Pokémon in the sidebar.")
    conn.close()
    st.stop()

# 4. Match Session Control Panel
st.markdown("<div class='section-header'>🏁 Automated Match Session Control Panel</div>", unsafe_allow_html=True)
col_btn1, col_btn2, col_info = st.columns([1, 1, 2])

with col_btn1:
    if not st.session_state.battle_active and not st.session_state.show_post_battle_review:
        if st.button("🚀 Start Battle Session", type="primary", use_container_width=True, key="start_battle_btn"):
            st.session_state.battle_active = True
            st.session_state.current_battle_log = []
            st.session_state.show_post_battle_review = False
            st.rerun()

with col_btn2:
    if st.session_state.battle_active:
        if st.button("🛑 End Battle & Review Feedback", type="secondary", use_container_width=True, key="end_battle_btn"):
            st.session_state.battle_active = False
            if st.session_state.current_battle_log:
                st.session_state.pending_review_logs = st.session_state.current_battle_log.copy()
                st.session_state.show_post_battle_review = True
            st.rerun()

with col_info:
    if st.session_state.battle_active:
        st.info(f"🔴 **PASSIVE RECORDING ACTIVE** ({len(st.session_state.current_battle_log)} turns captured seamlessly)")
    elif st.session_state.show_post_battle_review:
        st.success("📝 **BATTLE ENDED** — Please review and submit your turn feedback below.")
    else:
        st.warning("⚪ Session idle. Click **Start Battle Session** before playing.")

st.divider()

# --- POST-BATTLE FEEDBACK DEBRIEF VIEW ---
if st.session_state.show_post_battle_review:
    st.markdown("<div class='section-header'>📋 Post-Battle Debrief & Turn-by-Turn Feedback</div>", unsafe_allow_html=True)
    st.markdown("Review moves suggested during your session. Your feedback directly updates the **Feedback Memory Table** to optimize future recommendations:")

    with st.form("post_battle_review_form"):
        submitted_reviews = []
        for idx, turn in enumerate(st.session_state.pending_review_logs):
            st.markdown(f"**Turn {idx+1}:** Unit `{turn['my_active']}` vs Opponent `{turn['enemy_active']}`")
            st.markdown(f"🤖 *Suggested Move:* **{turn['best_move']}** (~{turn['max_damage']} damage)")
            
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                appropriateness = st.selectbox(f"Was suggestion {idx+1} appropriate?", ["Yes, highly appropriate", "Neutral", "No, poor suggestion"], key=f"app_{idx}")
            with col_rev2:
                damage_rated = st.selectbox(f"Did it deal good damage (Turn {idx+1})?", ["Yes, secured high damage / KO", "Moderate damage", "Low damage / Resisted"], key=f"dmg_{idx}")
            
            weight = 1 if "highly appropriate" in appropriateness or "high damage" in damage_rated else (-1 if "poor suggestion" in appropriateness else 0)

            submitted_reviews.append({
                "my_active": turn['my_active'],
                "enemy_active": turn['enemy_active'],
                "best_move": turn['best_move'],
                "max_damage": turn['max_damage'],
                "multiplier_str": turn['multiplier_str'],
                "feedback": f"Appropriate: {appropriateness} | Damage: {damage_rated}",
                "weight": weight,
                "notes": "Post-battle reviewed session log"
            })
            st.divider()

        commit_to_db = st.form_submit_button("💾 Save to MySQL & Update Adaptive Memory", type="primary")
        if commit_to_db:
            ins_cursor = conn.cursor()
            for r in submitted_reviews:
                ins_query = """
                    INSERT INTO Battle_History (My_Active_Pokemon, Enemy_Pokemon, Recommended_Move, Projected_Damage, Effectiveness_Rating, User_Feedback, Notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                ins_cursor.execute(ins_query, (
                    r["my_active"], r["enemy_active"], r["best_move"], 
                    int(r["max_damage"]), r["multiplier_str"], r["feedback"], r["notes"]
                ))
                
                mem_query = """
                    INSERT INTO Feedback_Memory (Pokemon_Name, Move_Name, Appropriateness_Rating, Damage_Rating, Score_Weight)
                    VALUES (%s, %s, %s, %s, %s)
                """
                parts = r["feedback"].split(" | ")
                app_val = parts[0].replace("Appropriate: ", "")
                dmg_val = parts[1].replace("Damage: ", "")
                ins_cursor.execute(mem_query, (r["my_active"], r["best_move"], app_val, dmg_val, r["weight"]))

            conn.commit()
            ins_cursor.close()
            st.success("✅ Feedback successfully committed to permanent memory and adaptive learning tables!")
            st.session_state.show_post_battle_review = False
            st.session_state.current_battle_log = []
            st.session_state.pending_review_logs = []
            st.rerun()

# Global Active Battler Controls (respecting voice input state if active)
default_enemy_idx = 0
if st.session_state.enemy_active_pkmn in all_creatures:
    default_enemy_idx = all_creatures.index(st.session_state.enemy_active_pkmn)

col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    my_active = st.selectbox("Your Active Unit:", living_team, key="my_active_pkmn_sel")
with col_ctrl2:
    enemy_active = st.selectbox("Target Opponent Unit:", all_creatures, index=default_enemy_idx, key="enemy_active_pkmn_sel")
    st.session_state.enemy_active_pkmn = enemy_active

st.divider()

# Fetch Stats via SQL Joins
query_my = f"""
    SELECT c.Name, t1.Type_Name AS Primary_Type, IFNULL(t2.Type_Name, 'None') AS Secondary_Type, 
           c.Base_Attack, c.Base_Defense, c.Base_Speed, c.Base_HP
    FROM Creatures c 
    JOIN Types t1 ON c.Primary_Type_ID = t1.Type_ID
    LEFT JOIN Types t2 ON c.Secondary_Type_ID = t2.Type_ID
    WHERE c.Name = '{my_active}'
"""
df_my = pd.read_sql(query_my, conn)

query_enemy = f"""
    SELECT c.Name, t1.Type_Name AS Primary_Type, IFNULL(t2.Type_Name, 'None') AS Secondary_Type, 
           c.Base_Attack, c.Base_Defense, c.Base_Speed, c.Base_HP
    FROM Creatures c 
    JOIN Types t1 ON c.Primary_Type_ID = t1.Type_ID
    LEFT JOIN Types t2 ON c.Secondary_Type_ID = t2.Type_ID
    WHERE c.Name = '{enemy_active}'
"""
df_enemy = pd.read_sql(query_enemy, conn)

my_stats = df_my.iloc[0]
enemy_stats = df_enemy.iloc[0]

# Damage & Speed Calculations
best_move = "None"
max_damage = 0
best_multiplier = 1.0

try:
    df_my_moves = pd.read_sql(f"""
        SELECT m.Move_Name FROM Moves m
        JOIN creature_moves cm ON m.Move_ID = cm.Move_ID
        JOIN Creatures c ON cm.Pokemon_ID = c.Pokemon_ID
        WHERE c.Name = '{my_active}'
    """, conn)
    allowed_moves = df_my_moves['Move_Name'].tolist()
except:
    allowed_moves = []

if not allowed_moves:
    team_move_sets = {
        "Kingambit": ["Kowtow Cleave", "Sucker Punch", "Iron Head"],
        "Garchomp": ["Earthquake", "Outrage"],
        "Gholdengo": ["Make It Rain", "Shadow Ball", "Thunderbolt", "Focus Blast"],
        "Dragapult": ["Dragon Darts", "Phantom Force", "U-turn", "Flamethrower"],
        "Iron-valiant": ["Moonblast", "Close Combat", "Thunderbolt", "Shadow Ball"],
        "Landorus": ["Earthquake", "U-turn"]
    }
    allowed_moves = team_move_sets.get(my_active, ['Earthquake', 'Surf', 'Thunderbolt'])

attack_multiplier_stage = 1.0 + (0.5 * my_boost)

#Feedback loop

for move in allowed_moves:
    query_damage = f"""
        SELECT ROUND(((( (2 * 100 / 5) + 2 ) * M.Power * ((A.Base_Attack * {attack_multiplier_stage}) / (D.Base_Defense * {eviolite_multiplier})) ) / 50 + 2) 
            * IF(M.Type_ID = A.Primary_Type_ID OR M.Type_ID = A.Secondary_Type_ID, 1.5, 1.0) 
            * (TM1.Multiplier * IFNULL(TM2.Multiplier, 1.0))) AS Estimated_Damage,
            (TM1.Multiplier * IFNULL(TM2.Multiplier, 1.0)) AS Multiplier
        FROM Creatures A CROSS JOIN Creatures D CROSS JOIN Moves M
        JOIN Type_Matchups TM1 ON M.Type_ID = TM1.Attacking_Type_ID AND D.Primary_Type_ID = TM1.Defending_Type_ID
        LEFT JOIN Type_Matchups TM2 ON M.Type_ID = TM2.Attacking_Type_ID AND D.Secondary_Type_ID = TM2.Defending_Type_ID
        WHERE A.Name = '{my_active}' AND M.Move_Name = '{move}' AND D.Name = '{enemy_active}'
    """
    result = pd.read_sql(query_damage, conn)
    if not result.empty:
        base_dmg = float(result['Estimated_Damage'].iloc[0])
        
        try:
            mem_cursor = conn.cursor()
            mem_cursor.execute("SELECT SUM(Score_Weight) FROM Feedback_Memory WHERE Pokemon_Name = %s AND Move_Name = %s", (my_active, move))
            weight_res = mem_cursor.fetchone()[0]
            mem_cursor.close()
            history_weight = float(weight_res) if weight_res else 0.0
        except:
            history_weight = 0.0

        adjusted_dmg = base_dmg + (history_weight * 5.0)

        if adjusted_dmg > max_damage:
            max_damage = adjusted_dmg
            best_move = move
            best_multiplier = float(result['Multiplier'].iloc[0])

effective_enemy_speed = enemy_stats['Base_Speed'] * 1.5 if enemy_scarfed else enemy_stats['Base_Speed']
my_speed = my_stats['Base_Speed']

# Silently capture turn in background if battle is active
if st.session_state.battle_active:
    turn_data = {
        "my_active": my_active,
        "enemy_active": enemy_active,
        "best_move": best_move,
        "max_damage": int(max_damage),
        "multiplier_str": f"{best_multiplier}x"
    }
    if not st.session_state.current_battle_log or st.session_state.current_battle_log[-1]["best_move"] != best_move or st.session_state.current_battle_log[-1]["enemy_active"] != enemy_active:
        st.session_state.current_battle_log.append(turn_data)

# Bench Switch Intelligence
other_living = [m for m in living_team if m != my_active]
safest_switch = "None"
switch_msg_type = ""

if other_living:
    placeholders_alive = ", ".join(["%s"] * len(other_living))
    query_bench = f"""
        SELECT c.Name, c.Base_Speed, c.Base_Defense, c.Base_SpDefense, c.Base_HP,
               t1.Type_Name AS Primary_Type, IFNULL(t2.Type_Name, 'None') AS Secondary_Type
        FROM Creatures c 
        JOIN Types t1 ON c.Primary_Type_ID = t1.Type_ID
        LEFT JOIN Types t2 ON c.Secondary_Type_ID = t2.Type_ID
        WHERE c.Name IN ({placeholders_alive})
    """
    df_bench = pd.read_sql(query_bench, conn, params=tuple(other_living))
    
    if not df_bench.empty:
        faster_bench = df_bench[df_bench['Base_Speed'] > effective_enemy_speed]
        if not faster_bench.empty:
            best_switch = faster_bench.sort_values(by='Base_Speed', ascending=False).iloc[0]
            safest_switch = best_switch['Name']
            switch_msg_type = f"🚀 **Speed Advantage:** Outspeeds enemy ({best_switch['Base_Speed']} SPD)"
        else:
            df_bench['Bulk_Score'] = df_bench['Base_Defense'] + df_bench['Base_SpDefense'] + (df_bench['Base_HP'] * 0.5)
            df_bench_filtered = df_bench[df_bench['Name'] != my_active]
            if not df_bench_filtered.empty:
                best_wall = df_bench_filtered.sort_values(by='Bulk_Score', ascending=False).iloc[0]
                safest_switch = best_wall['Name']
                switch_msg_type = f"⚠️ **No faster options!** Pivoting to bulkiest wall."
            else:
                safest_switch = living_team[0]
                switch_msg_type = "⚠️ No alternative bench options."
else:
    safest_switch = "None remaining!"
    switch_msg_type = "All squad members fainted."

# 5. Professional Tab Architecture
tab_combat, tab_telemetry, tab_codex, tab_synergy, tab_history = st.tabs([
    "⚔️ Combat Engine", 
    "📊 Matchup Telemetry", 
    "📘 Move Strategy Codex", 
    "🛡️ Type Synergy Matrix",
    "📜 Battle History & Memory"
])

with tab_combat:
    st.markdown("<div class='section-header'>🎯 Live Tactical Simulation & Field Control</div>", unsafe_allow_html=True)

    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        my_type_disp = f"{my_stats['Primary_Type']} / {my_stats['Secondary_Type']}" if my_stats['Secondary_Type'] != 'None' else my_stats['Primary_Type']
        st.markdown(f"""
        <div class='pokemon-card'>
            <h4 style='margin:0 0 4px 0;'>🔵 Unit Alpha: {my_stats['Name']}</h4>
            <span class='type-badge'>{my_type_disp}</span><br><br>
            <span style='color:{sub_text};'>ATK: <b>{my_stats['Base_Attack']}</b> | DEF: <b>{my_stats['Base_Defense']}</b> | SPD: <b>{my_stats['Base_Speed']}</b></span>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        en_type_disp = f"{enemy_stats['Primary_Type']} / {enemy_stats['Secondary_Type']}" if enemy_stats['Secondary_Type'] != 'None' else enemy_stats['Primary_Type']
        st.markdown(f"""
        <div class='pokemon-card' style='border-left-color: #dc3545;'>
            <h4 style='margin:0 0 4px 0; color:#dc3545;'>🔴 Unit Target: {enemy_stats['Name']}</h4>
            <span class='type-badge' style='background-color:#dc3545;'>{en_type_disp}</span><br><br>
            <span style='color:{sub_text};'>HP: <b>{enemy_stats['Base_HP']}</b> | DEF: <b>{enemy_stats['Base_Defense']}</b> | SPD: <b>{enemy_stats['Base_Speed']}</b></span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>📋 Action Directives & Direct Execution Output</div>", unsafe_allow_html=True)
    col_dir1, col_dir2 = st.columns(2)

    with col_dir1:
        st.markdown(f"""
        <div class='attack-directive'>
            <strong>⚔️ RECOMMENDED OFFENSIVE MOVE</strong><br><br>
            Execute <span class='highlight'>{best_move}</span><br>
            Projected Output: ~{int(max_damage)} Damage ({best_multiplier}x Multiplier)
        </div>
        """, unsafe_allow_html=True)
        
    with col_dir2:
        if effective_enemy_speed > my_speed:
            st.markdown(f"""
            <div class='switch-directive'>
                <strong>🔄 DEFENSIVE RETREAT DIRECTIVE</strong><br><br>
                {switch_msg_type}<br>
                Recommended Switch: <span class='highlight'>{safest_switch}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='success-directive'>
                <strong>⚡ INITIATIVE ADVANTAGE</strong><br><br>
                <strong>You outspeed the target!</strong><br>
                Do not switch. Maintain field presence and strike first.
            </div>
            """, unsafe_allow_html=True)

with tab_telemetry:
    st.markdown("<div class='section-header'>📊 Real-Time Telemetry & Combat Feed</div>", unsafe_allow_html=True)
    st.markdown("Automated operational telemetry stream capturing state queries and multi-table database joins:")

    st.markdown(f"<div class='telemetry-box'>[INFO] Database connection active on schema: pokemon_analytics</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='telemetry-box'>[EXEC] Query executed for active unit -> {my_active} (ATK: {my_stats['Base_Attack']}, SPD: {my_stats['Base_Speed']})</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='telemetry-box'>[EXEC] Query executed for target unit -> {enemy_active} (DEF: {enemy_stats['Base_Defense']}, Item Multiplier: {eviolite_multiplier}x)</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='telemetry-box'>[CALC] Optimal move resolved: {best_move} with estimated output ~{int(max_damage)} damage.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='telemetry-box'>[EVAL] Speed Tier Comparison -> User ({my_speed}) vs Target ({effective_enemy_speed}): {'Outsped' if effective_enemy_speed > my_speed else 'Outpaced Target'}</div>", unsafe_allow_html=True)

with tab_codex:
    st.markdown("<div class='section-header'>📘 Active Squad Move Codex & Tactical Directives</div>", unsafe_allow_html=True)
    st.markdown("Relational move mapping repository containing descriptive performance indices and matchup parameters.")

    move_codex_data = {
        "Kingambit": [
            ("Kowtow Cleave", "Dark | Physical | Power: 85", "Never misses. Deals high structural damage against Psychic and Ghost units.", "✅ Deploy against slow structural walls.\n❌ Avoid against Fairy or Fighting resist types."),
            ("Sucker Punch", "Dark | Physical | Power: 70", "Priority counter-strike that activates if the opponent attacks first.", "✅ Use for quick revenge elimination on fast sweepers.\n❌ Fails if the opponent uses status moves."),
            ("Iron Head", "Steel | Physical | Power: 80", "Has a 30% operational flinch probability.", "✅ Primary counter against Fairy and Rock configurations.\n❌ Avoid against Fire or Water tanks.")
        ],
        "Iron-valiant": [
            ("Moonblast", "Fairy | Special | Power: 95", "30% chance to degrade opponent Special Attack staging.", "✅ Primary weapon against Dragon and Dark threats.\n❌ Ineffective against Steel and Poison barriers."),
            ("Close Combat", "Fighting | Physical | Power: 120", "High impact damage output, degrades defensive metrics by 1 stage.", "✅ Perfect for breaking Steel and Normal heavy walls.\n❌ Avoid if defensive integrity is required next turn."),
            ("Thunderbolt", "Electric | Special | Power: 90", "10% paralyze configuration probability.", "✅ Effective coverage against Water and Flying targets."),
            ("Shadow Ball", "Ghost | Special | Power: 80", "20% chance to lower target Special Defense.", "✅ Neutral coverage across multiple archetypes.")
        ],
        "Gholdengo": [
            ("Make It Rain", "Steel | Special | Power: 120", "Signature heavy projectile that lowers user Special Attack by 1 stage.", "✅ Devastates Fairy and Ice archetypes.\n❌ Avoid blind spamming due to stat degradation."),
            ("Shadow Ball", "Ghost | Special | Power: 80", "Reliable STAB ghost attack.", "✅ Safe neutral coverage move.")
        ],
        "Garchomp": [
            ("Earthquake", "Ground | Physical | Power: 100", "Earthquake tremor attack.", "✅ Universal coverage against Electric, Fire, and Steel units.\n❌ Ineffective against Flying archetypes.")
        ]
    }

    current_codex = move_codex_data.get(my_active, [
        ("Standard Move", "Basic Type", "Standard combat operation move.", "✅ Deploy when super-effective.\n❌ Avoid when resisted.")
    ])

    for m_name, m_type, m_desc, m_advice in current_codex:
        with st.expander(f"📌 {m_name} ({m_type})"):
            st.write(f"**Operational Parameters:** {m_desc}")
            st.markdown(f"**Tactical Guidance:**\n{m_advice}")

with tab_synergy:
    st.markdown("<div class='section-header'>🛡️ Type Synergy Matrix & Vulnerability Mapping</div>", unsafe_allow_html=True)
    st.markdown("Normalized structural overview of squad typing parameters and tactical vulnerabilities:")

    synergy_df = pd.DataFrame([
        {"Squad Member": "Kingambit", "Primary Typing": "Dark / Steel", "Optimal Target Counters": "Psychic, Ghost, Fairy, Ice", "Primary Vulnerabilities": "Fighting (4x), Fire, Ground"},
        {"Squad Member": "Iron Valiant", "Primary Typing": "Fairy / Fighting", "Optimal Target Counters": "Dragon, Dark, Steel, Normal", "Primary Vulnerabilities": "Poison, Flying, Psychic, Fairy"},
        {"Squad Member": "Garchomp", "Primary Typing": "Dragon / Ground", "Optimal Target Counters": "Electric, Fire, Poison, Rock", "Primary Vulnerabilities": "Ice (4x), Dragon, Fairy"},
        {"Squad Member": "Gholdengo", "Primary Typing": "Steel / Ghost", "Optimal Target Counters": "Fairy, Rock, Ice, Psychic", "Primary Vulnerabilities": "Fire, Ghost, Dark, Ground"},
        {"Squad Member": "Dragapult", "Primary Typing": "Dragon / Ghost", "Optimal Target Counters": "Dragon, Ghost, Psychic", "Primary Vulnerabilities": "Ice, Dragon, Fairy, Dark, Ghost"},
        {"Squad Member": "Landorus", "Primary Typing": "Ground / Flying", "Optimal Target Counters": "Electric, Fire, Poison, Fighting", "Primary Vulnerabilities": "Ice (4x), Water"}
    ])
    
    st.dataframe(synergy_df, use_container_width=True, hide_index=True)

with tab_history:
    st.markdown("<div class='section-header'>📜 Permanent Historical Database & Adaptive Memory Logs</div>", unsafe_allow_html=True)
    st.markdown("Historical fight records and adaptive learning weights stored in MySQL:")
    try:
        df_history = pd.read_sql("SELECT * FROM Battle_History ORDER BY Timestamp DESC", conn)
        if not df_history.empty:
            st.markdown("### 🗄️ Past Battle Logs (`Battle_History`)")
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("No battle logs found yet.")
            
        df_memory = pd.read_sql("SELECT * FROM Feedback_Memory", conn)
        if not df_memory.empty:
            st.markdown("### 🧠 Adaptive Feedback Memory Table (`Feedback_Memory`)")
            st.dataframe(df_memory, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Tables need to be created in MySQL. (Error: {e})")

conn.close()