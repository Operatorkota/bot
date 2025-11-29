# -*- coding: utf-8 -*-

# 1. Wejdź na stronę https://discord.com/developers/applications
# 2. Kliknij "New Application" i nazwij swojego bota.
# 3. Przejdź do zakładki "Bot" po lewej stronie.
# 4. Pod sekcją "Privileged Gateway Intents" włącz WSZYSTKIE opcje (szczególnie "SERVER MEMBERS INTENT" i "MESSAGE CONTENT INTENT").
# 5. Kliknij "Reset Token", a następnie skopiuj token.
# 6. Wklej skopiowany token poniżej, w cudzysłowie.

TOKEN = "MTQzNzAzNDQxNjU0NjI1MDc2Mw.GDssh1.29HAF4CtX1BRAwbnoT_3P_6TaCeMJZHBi-jr1g"

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

# Słownik mapujący nazwy sektorów na ID ról
SECTOR_ROLE_IDS = {
    "Pacjent": 1437055978100232322,
    "Forensic": 1437895062209036319,
    "Max Security": 1440071740905488436,
    "Piwnica": 1440071834161778709
}

# --- Konfiguracja powiadomień dla admina o komendach ekonomii ---
ADMIN_COMMANDS_CHANNEL_ID = 1437132784237019137
ADMIN_COMMANDS_ROLE_ID = 1437076629548437515

# --- Kanały Moderacji ---
MOD_LOG_CHANNEL_ID = 1437132784237019137 # Kanał do logowania akcji moderacyjnych (kar, blokad itp.)




# --- Konfiguracja AI Gemini ---
# Wklej tutaj swoje klucze API Gemini. Bot będzie próbował użyć kolejnego, jeśli poprzedni zawiedzie.
GEMINI_API_KEYS = [
    "AIzaSyAYl8O6bppy1LrL9eVWcgFKu9Z9ROTvhDE",
    "AIzaSyDXg3mP-4pfxRv8HjqVqZkTIHM7xuuS1i8",
    "AIzaSyAnlwaUMX9CZc0c8Qti4U4cwFBRaknwJVA",
    "AIzaSyALRgzEWWxwQ9Xxolwh78UJjcEXPXdI8mM",
    "AIzaSyCfZRc7v7BGEATGRGzXNeIZkuB14cKqydQ"
]
# Wklej tutaj ID kanału, na którym bot ma odpowiadać na wiadomości AI.
GEMINI_CHANNEL_ID = 1443212790486667325 # Zastąp 0 rzeczywistym ID kanału