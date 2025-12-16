TOKEN = ""
PROTOCOL_RULES = [
    "ZAKAZ JEBANYCH AK-47 I SVDM",
]

FINANCIAL_PENALTIES = {
    "Passive escaping": 2000,
    "kontrabanda": 1500,
    "usiłowanie zabójstwa": 3000,
    "zabójstwo na personelu": 3500,
    "stawianie oporu": 500,
    "battery": 1500,
    "harrasment": 2500,
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

# Role-based hourly rates
ROLE_RATES = {
    "stażysta": 120,
    "lekarz": 250,
    "ordynator": 320,
    "dyrektor": 400,
}

# IDs of voice channels where duty time is tracked
# Please replace "ID_KANAŁU_1" with the actual channel IDs
DUTY_VOICE_CHANNEL_IDS = ["ID_KANAŁU_1", "ID_KANAŁU_2"]

# IDs of roles that can approve payroll
# Please replace "ID_ROLI_ADMINA_1" with the actual admin role IDs
ADMIN_ROLE_IDS = ["ID_ROLI_ADMINA_1", "ID_ROLI_ADMINA_2"]

# Payout requirements
MIN_DUTY_HOURS_FOR_PAYOUT = 20
MIN_INTERVENTIONS_FOR_PAYOUT = 15

# Payroll period in days
PAYROLL_PERIOD_DAYS = 5

# Channel where payroll reports will be sent
# Please replace "ID_KANAŁU_RAPORTOW" with the actual channel ID
PAYROLL_REPORTS_CHANNEL_ID = "ID_KANAŁU_RAPORTOW"

# Channel where payroll drafts will be sent for approval
# Please replace "ID_KANAŁU_PROJEKTOW" with the actual channel ID
PAYROLL_DRAFTS_CHANNEL_ID = "ID_KANAŁU_PROJEKTOW"

# Name of the duty role
DUTY_ROLE_NAME = "Na Służbie"
