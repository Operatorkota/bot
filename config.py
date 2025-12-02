# -*- coding: utf-8 -*-

# 1. Wejdź na stronę https://discord.com/developers/applications
# 2. Kliknij "New Application" i nazwij swojego bota.
# 3. Przejdź do zakładki "Bot" po lewej stronie.
# 4. Pod sekcją "Privileged Gateway Intents" włącz WSZYSTKIE opcje (szczególnie "SERVER MEMBERS INTENT" i "MESSAGE CONTENT INTENT").
# 5. Kliknij "Reset Token", a następnie skopiuj token.
# 6. Wklej skopiowany token poniżej, w cudzysłowie.

TOKEN = "MTQzNzAzNDQxNjU0NjI1MDc2Mw.GA-TgX.grqQe7Uc6_Yoo_hJ0QrT_fCEfGPmwoGR9l0I_g"

PROTOCOL_RULES = [
    "ZAKAZ JEBANYCH AK-47 I SVDM",
]

FINANCIAL_PENALTIES = {
    "Passive escaping": 2000,
    "kontrabanda": 1500,
    "usiłowanie zabójstwa": 3000,
    "zabójstwo na personelu": 3500,
    "stawianie oporu": 500,
}

# --- Konfiguracja ID kanałów ---
# Wklej tutaj ID kanału, na który mają być wysyłane wiadomości o karach z komendy /sentenced
SENTENCED_CHANNEL_ID = 1437132768407453848

# Wklej tutaj ID kanałów informacyjnych, które bot ma aktualizować
INFO_CHANNEL_IDS = {
    "regulamin": 1437132761612812421,
    "protokół": 1437132776699859128,
    "protokół_1": 1437132776699859128,
    "protokół_2": 1437132776699859128,
    # Dodaj inne kanały informacyjne, jeśli są potrzebne
}

# Wklej tutaj ID kanału, na który mają być wysyłane ogłoszenia RP
RP_ANNOUNCEMENT_CHANNEL_ID = 1437132776699859128

# Wklej tutaj ID kanału, na który mają być wysyłane sugestie
SUGGESTIONS_CHANNEL_ID = 0 # Zastąp 0 rzeczywistym ID kanału

# Wklej tutaj ID kanału, na który mają być wysyłane karty pacjentów
PATIENT_CARDS_CHANNEL_ID = 1439236245594177598

# --- Konfiguracja komendy /przenies ---
# ID kanału, na który będą wysyłane potwierdzenia o przeniesieniu
PRZYPIS_CHANNEL_ID = 1437132768407453848



# --- Konfiguracja powiadomień dla admina o komendach ekonomii ---
ADMIN_COMMANDS_CHANNEL_ID = 1437132784237019137
ADMIN_COMMANDS_ROLE_ID = 1437076629548437515

# --- Kanały Moderacji ---
MOD_LOG_CHANNEL_ID = 1437132784237019137 # Kanał do logowania akcji moderacyjnych (kar, blokad itp.)




# --- Konfiguracja AI Gemini ---
# Wklej tutaj swoje klucze API Gemini. Bot będzie próbował użyć kolejnego, jeśli poprzedni zawiedzie.
GEMINI_API_KEYS = [
    "AIzaSyDnB6bqpATtzlpHhy8zS4xaCL_6OcGgDdo",
    "AIzaSyBft95wxSzmD8I4PFmzyA-hm6zAcvmg6fc",
    "AIzaSyBuelsVBhJdRP5MlddN0ClW7hirBONDwAs",
    "AIzaSyCRk5rKguCHVcQHE0_tJg2bTDOHrYcA5ns",
    "AIzaSyBQ3KeQCv-qTW-hdH6sWPUIiuOhP04y7PQ"
]
# Wklej tutaj ID kanału, na którym bot ma odpowiadać na wiadomości AI.
GEMINI_CHANNEL_ID = 1443212790486667325 # Zastąp 0 rzeczywistym ID kanału