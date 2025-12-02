# -*- coding: utf-8 -*- 

import discord
from discord import app_commands
from discord.ext import tasks # Import tasks for background loops
import config
import json
import os
from datetime import datetime, timedelta, time
import random
import unicodedata
import re
from itertools import cycle
import google.generativeai as genai
import asyncio # New import
from zoneinfo import ZoneInfo # New import



# --- ŚCIEŻKA DO PLIKU GŁOSOWANIA ---
VOTES_FILE = 'votes.json'

# --- FUNKCJE ZARZĄDZANIA GŁOSAMI ---

def load_votes():
    """Wczytuje dane głosowania z pliku JSON."""
    if not os.path.exists(VOTES_FILE):
        return {"votes": {}, "voted_users": []}
    try:
        with open(VOTES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                return {"votes": {}, "voted_users": []}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"votes": {}, "voted_users": []}

def save_votes(data):
    """Zapisuje dane głosowania do pliku JSON."""
    with open(VOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


# --- ŚCIEŻKA DO PLIKU Z DANYMI UŻYTKOWNIKÓW ---
USER_DATA_FILE = 'user_data.json'

# --- FUNKCJE ZARZĄDZANIA DANYMI UŻYTKOWNIKÓW ---

def load_user_data():
    """Wczytuje dane użytkowników z pliku JSON."""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_user_data(data):
    """Zapisuje dane użytkowników do pliku JSON."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- FUNKCJE ZARZĄDZANIA BLOKADAMI KANAŁÓW GŁOSOWYCH ---












# --- ŚCIEŻKA DO PLIKU KART PACJENTÓW ---
PATIENT_CARDS_FILE = 'patient_cards.json'

# --- FUNKCJE ZARZĄDZANIA KARTAMI PACJENTÓW ---

def load_patient_cards():
    """Wczytuje dane kart pacjentów z pliku JSON."""
    if not os.path.exists(PATIENT_CARDS_FILE):
        return {}
    try:
        with open(PATIENT_CARDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_patient_cards(data):
    """Zapisuje dane kart pacjentów do pliku JSON."""
    with open(PATIENT_CARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- ŚCIEŻKA DO PLIKU USTAWIEŃ AI ---
AI_SETTINGS_FILE = 'ai_settings.json'

# --- FUNKCJE ZARZĄDZANIA USTAWAMIENIAMI AI ---

def load_ai_settings():
    """Wczytuje ustawienia AI z pliku JSON."""
    if not os.path.exists(AI_SETTINGS_FILE):
        return {"persona": ""}
    try:
        with open(AI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"persona": ""}

def save_ai_settings(data):
    """Zapisuje ustawienia AI do pliku JSON."""
    with open(AI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def parse_duration(duration_str: str) -> timedelta | None:
    """Parsuje ciąg znaków czasu (np. '10m', '2h', '1d') na obiekt timedelta."""
    if not duration_str:
        return None
    
    try:
        duration_str = duration_str.lower().strip()
        value = int(duration_str[:-1])
        unit = duration_str[-1]

        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        else:
            return None # Invalid unit
    except (ValueError, IndexError):
        return None

# --- KOMENDY MODERACYJNE ---







def get_user_data(user_id: int):
    """Pobiera dane użytkownika, inicjalizując je, jeśli nie istnieją."""
    users_data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            "active_temp_roles": [],
            "sentences": []
        }
        save_user_data(users_data)
    else:
        user_data = users_data[user_id_str]
        # Ensure essential non-economy fields exist for older data structures
        if "active_temp_roles" not in user_data or "sentences" not in user_data:
            user_data.setdefault("active_temp_roles", [])
            user_data.setdefault("sentences", [])
            save_user_data(users_data)
            
    return users_data[user_id_str]

def update_user_data(user_id: int, data: dict):
    """Aktualizuje dane użytkownika."""
    users_data = load_user_data()
    users_data[str(user_id)] = data
    save_user_data(users_data)




# Definicja struktury serwera: (nazwa_kategorii, [lista_kanałów_tekstowych], [lista_kanałów_głosowych])
SERVER_STRUCTURE = [
    ("📜 INFORMACJE 📜", ["#️⃣・weryfikacja", "#️⃣・regulamin", "#️⃣・regulamin-rp", "#️⃣・ogłoszenia", "#️⃣・role"], []),
    ("💬 GŁÓWNE 💬", ["#️⃣・czat-ogólny", "#️⃣・status", "#️⃣・komendy-botów", "#️⃣・multimedia"], []),
    ("ORDERLY", ["#️⃣・radio", "#️⃣・protokół"], []),
    ("🔊 GŁOSOWE 🔊", [], ["🎤・Rozmowy #1", "🎤・Rozmowy #2", "🎧・Muzyka"]),
    ("🔒 ADMINISTRACJA 🔒", ["#logi", "#chat-adm"], []),
]


# --- ŚCIEŻKA DO PLIKU RÓL ---
ROLES_FILE = 'roles.json'

# --- FUNKCJE ZARZĄDZANIA ROLAMI ---

def load_roles():
    """Wczytuje dane ról z pliku JSON."""
    if not os.path.exists(ROLES_FILE):
        return {"ROLES_TO_CREATE": [], "SECTOR_ROLE_IDS": {}}
    try:
        with open(ROLES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                return {"ROLES_TO_CREATE": [], "SECTOR_ROLE_IDS": {}}
            data = json.loads(content)
            
            # Convert color integers back to discord.Color objects for ROLES_TO_CREATE
            if "ROLES_TO_CREATE" in data:
                converted_roles = []
                for role_data in data["ROLES_TO_CREATE"]:
                    if "color" in role_data:
                        converted_roles.append((role_data["name"], discord.Color(role_data["color"])))
                    else:
                        converted_roles.append((role_data["name"], discord.Color.default())) # Default color if not specified
                data["ROLES_TO_CREATE"] = converted_roles
            
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {"ROLES_TO_CREATE": [], "SECTOR_ROLE_IDS": {}}

def save_roles(data):
    """Zapisuje dane ról do pliku JSON."""
    # Convert discord.Color objects to integers before saving
    serializable_data = data.copy()
    if "ROLES_TO_CREATE" in serializable_data:
        converted_roles = []
        for role_name, color_obj in serializable_data["ROLES_TO_CREATE"]:
            converted_roles.append({"name": role_name, "color": color_obj.value})
        serializable_data["ROLES_TO_CREATE"] = converted_roles

    with open(ROLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, indent=4)


# Definicja struktury serwera: (nazwa_kategorii, [lista_kanałów_tekstowych], [lista_kanałów_głosowych])
RULES_TITLE = "📜 Regulamin Serwera"
RULES_DESCRIPTION = """
**1. Kultura i szacunek:**
> 1.1. Zakaz obrażania, nękania, rasizmu, seksizmu i innych form toksycznego zachowania.
> 1.2. Szanuj innych użytkowników i ich opinie.

**2. Treści:**
> 2.1. Zakaz publikowania treści NSFW (18+), brutalnych, nielegalnych lub w jakikolwiek sposób szkodliwych.
> 2.2. Zakaz spamu, floodu i nadmiernego używania CAPS LOCKA.
> 2.3. Reklamowanie się jest dozwolone tylko na wyznaczonym kanale (jeśli istnieje) i za zgodą administracji.

**3. Bezpieczeństwo:**
> 3.1. Zakaz udostępniania danych osobowych swoich oraz innych osób.
> 3.2. Nie klikaj w podejrzane linki.

**4. Postanowienia końcowe:**
> 4.1. Administracja ma zawsze rację i jej decyzje są ostateczne.
> 4.2. Nieznajomość regulaminu nie zwalnia z jego przestrzegania.

*Miłego pobytu na serwerze!* 
"""


# Treść protokołu
PROTOCOL_TITLE = "📜 Protokół Postępowania"
PROTOCOL_PART_1_DESCRIPTION = """
Poniżej znajdują się zasady i procedury obowiązujące w naszej placówce. Ich celem jest zapewnienie bezpieczeństwa zarówno pacjentom, jak i personelowi.

### **Podstawowe Wykroczenia**

Każde zachowanie niezgodne z regulaminem spotka się z odpowiednią reakcją. Poniżej kilka przykładów:
> - **Próba ucieczki:** Skutkuje nadaniem statusu Max Security (MS) na 20 minut.
> - **Raid na placówkę z użyciem broni:** To poważne wykroczenie, karane statusem Max Security (MS) na 60 minut. Na czas raidu dozwolone jest użycie broni długiej.
> - **Atak na personel:** Usiłowanie zabójstwa to 20 minut statusu MS. Dokonanie zabójstwa również skutkuje 20 minutami MS.
> - **Posiadanie kontrabandy:** Wykrycie niedozwolonych przedmiotów (np. noży, łomów) kończy się nadaniem statusu Forensic.
> - **Niewykonywanie poleceń:** Po ostrzeżeniu, dalszy opór skutkuje umieszczeniem w izolatce (Iso/Holding Cells) na 10 minut.

### **Kary Pieniężne**
Poniżej przedstawiono kary pieniężne za poszczególne przewinienia:
> - **Passive escaping:** 2000 PLN
> - **Kontrabanda:** 1500 PLN
> - **Usiłowanie zabójstwa:** 3000 PLN
> - **Zabójstwo na personelu:** 3500 PLN
> - **Stawianie oporu:** 500 PLN
"""
PROTOCOL_PART_2_DESCRIPTION = """
### **Statusy Specjalne Pacjentów**

W zależności od zachowania, pacjent może otrzymać jeden z poniższych statusów:

> **1. Forensic**
> Nadawany za posiadanie kontrabandy lub próby ucieczki, o ile nie towarzyszyła im znacząca przemoc. Pacjenci z tym statusem są oddzieleni od reszty i jest to domyślny status dla uciekinierów.
> 
> **2. Max Security (MS)**
> Zarezerwowany dla najcięższych przypadków: morderstw, użycia niebezpiecznej kontrabandy, czy organizowania raidów. Pacjenci MS są pod stałym, ścisłym nadzorem.
> 
> **3. Isolation**
> Stosowany w przypadku powtarzających się, agresywnych lub skrajnie destrukcyjnych zachowań. Umieszczenie w izolatce jest poprzedzone ostrzeżeniem i ma na celu uspokojenie i ochronę, a nie karę.

### **Zasady Ogólne i Dotyczące Personelu**

> - **Zasady Użycia Siły (ŚPB):** Środki przymusu bezpośredniego mogą być stosowane przez uprawniony personel w sposób proporcjonalny do zagrożenia i w celu osiągnięcia określonego celu.
>   - **1. Kiedy można użyć ŚPB?**
>     - W celu odparcia bezpośredniego, bezprawnego zamachu na życie lub zdrowie własne lub innej osoby.
>     - W celu przeciwdziałania czynnościom zmierzającym bezpośrednio do takiego zamachu.
>     - W celu przeciwdziałania naruszeniu bezpieczeństwa placówki o wysokim stopniu zabezpieczenia.
>     - W celu ujęcia osoby, która stwarza bezpośrednie zagrożenie.
>     - W celu pokonania czynnego oporu pacjenta.
>   - **2. Gradacja środków:**
>     - Personel jest zobowiązany do stosowania najpierw najłagodniejszych dostępnych środków, adekwatnych do sytuacji (np. polecenia słowne).
>     - W przypadku nieskuteczności, można zastosować siłę fizyczną (chwyty obezwładniające), a w dalszej kolejności inne środki (np. kajdanki, pałka służbowa).
>   - **3. Obowiązki po użyciu ŚPB:**
>     - Każde użycie ŚPB musi być niezwłocznie zaraportowane przełożonemu.
>     - Pacjent, wobec którego użyto ŚPB, musi zostać zbadany przez personel medyczny.
> - **Procedury zakładnicze:** W przypadku wzięcia zakładnika przez pacjenta, priorytetem jest bezpieczeństwo zakładnika. Należy natychmiast powiadomić przełożonych, a także, jeśli to możliwe, szefa Orderly. Należy postępować zgodnie z instrukcjami zespołu negocjacyjnego, unikając eskalacji konfliktu.
> - **Użycie broni palnej:** Dozwolone jest **tylko i wyłącznie w ostateczności**, gdy wszystkie inne środki zawiodą.
> - **ZAKAZ JEBANYCH AK-47 I SVDM:** Używanie tych konkretnych modeli broni jest surowo zabronione.
> - **Agresja i prowokacje:** Jakiekolwiek chamskie zachowanie lub atak na personel będzie surowo karane ("pałowanie").
> - **Nadużycia personelu:** Personel, który bezprawnie wypuszcza lub celowo prowokuje pacjentów, spotka się z identycznymi konsekwencjami ("pałowanie"). Pamiętajcie, zasady obowiązują obie strony.

### **Rejestrowanie Kar**
Wszystkie oficjalne kary, zwłaszcza te wpływające na status pacjenta lub jego finanse, **muszą być** zarejestrowane przy użyciu komendy `/sentenced`. Zapewnia to transparentność i pozwala na prowadzenie oficjalnego rejestru.
"""



# Treść regulaminu RP
RP_RULES_TITLE = "📜 Regulamin RP"
RP_RULES_DESCRIPTION = """
> **NLR (New Life Rule):** Po śmierci Twoja postać zapomina wszystko, co doprowadziło do jej śmierci. Nie możesz wrócić w miejsce, gdzie zginąłeś, ani mścić się na osobach, które Cię zabiły. Zaczynasz "nowe życie" z nową historią.
> **FearRP:** Jeżeli ktoś celuje do Ciebie z broni, masz obowiązek wykonywać jego polecenia, tak jak zrobiłbyś to w prawdziwym życiu, obawiając się o swoje życie.
"""

# --- Konfiguracja statusu RP ---
RP_STATUS_CHANNEL_ID = 1439041710570213376
RP_FIXED_LINK = "https://www.roblox.com/share?code=c7cc28921989b046bdba75d822c11643&type=Server"
RP_STATUS_FILE = 'status.json'
RP_THUMBNAIL_URL = "https://png.pngtree.com/png-vector/20220623/ourmid/pngtree-rp-letter-logo-design-on-black-background-rp-creative-initials-letter-png-image_5276433.png"

def load_rp_status_message_id():
    """Wczytuje ID wiadomości statusu RP z pliku JSON."""
    if not os.path.exists(RP_STATUS_FILE):
        return None
    try:
        with open(RP_STATUS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("rp_status_message_id")
    except json.JSONDecodeError:
        return None

def save_rp_status_message_id(message_id):
    """Zapisuje ID wiadomości statusu RP do pliku JSON."""
    with open(RP_STATUS_FILE, 'w') as f:
        json.dump({"rp_status_message_id": message_id}, f, indent=4)

# Zmienne globalne do przechowywania ID
verification_message_id = None

async def check_and_update_messages(guild: discord.Guild, client: discord.Client):
    """Automatycznie sprawdza i aktualizuje wiadomości informacyjne przy starcie bota, używając ID kanałów."""
    print(f"INFO: Rozpoczynam sprawdzanie wiadomości na serwerze: {guild.name}")

    messages_to_check = [
        {"key": "regulamin", "title": RULES_TITLE, "desc": RULES_DESCRIPTION, "color": discord.Color.from_rgb(66, 135, 245)},
        {"key": "protokół_1", "title": f"{PROTOCOL_TITLE} (Część 1)", "desc": PROTOCOL_PART_1_DESCRIPTION, "color": discord.Color.from_rgb(245, 66, 66)},
        {"key": "protokół_2", "title": f"{PROTOCOL_TITLE} (Część 2)", "desc": PROTOCOL_PART_2_DESCRIPTION, "color": discord.Color.from_rgb(245, 66, 66)},
        {"key": "regulamin-rp", "title": RP_RULES_TITLE, "desc": RP_RULES_DESCRIPTION, "color": discord.Color.from_rgb(66, 245, 100)},
    ]

    for msg_data in messages_to_check:
        channel_id = config.INFO_CHANNEL_IDS.get(msg_data["key"])
        if not channel_id:
            print(f"INFO: Brak ID kanału dla '{msg_data['key']}' w config.py. Pomięto.")
            continue

        channel = guild.get_channel(channel_id)
        if not channel:
            print(f"INFO: Nie znaleziono kanału o ID {channel_id} dla '{msg_data['key']}' na serwerze '{guild.name}'.")
            continue

        try:
            found_message = False
            async for message in channel.history(limit=100):
                if message.author == client.user and message.embeds and message.embeds[0].title == msg_data["title"]:
                    found_message = True
                    existing_desc = message.embeds[0].description
                    new_desc = msg_data["desc"]

                    if existing_desc != new_desc:
                        new_embed = discord.Embed(title=msg_data["title"], description=msg_data["desc"], color=msg_data["color"])
                        await message.edit(embed=new_embed)
                        print(f"INFO: Zaktualizowano '{msg_data['title']}' na serwerze '{guild.name}'.")
                    break
            
            if not found_message:
                new_embed = discord.Embed(title=msg_data["title"], description=msg_data["desc"], color=msg_data["color"])
                await channel.send(embed=new_embed)
                print(f"INFO: Wysłano nową wiadomość '{msg_data['title']}' na kanale '{channel.name}'.")
        except discord.Forbidden:
            print(f"BŁĄD: Brak uprawnień do czytania historii na kanale '{channel.name}' (ID: {channel_id}) na serwerze '{guild.name}'.")
        except Exception as e:
            print(f"BŁĄD: Nieoczekiwany błąd podczas sprawdzania kanału '{channel.name}' (ID: {channel_id}): {e}")


# --- Komendy do zarządzania statusem RP ---
rp_status_group = app_commands.Group(name="rp-status", description="Zarządza statusem RP (włączone/wyłączone).")

@rp_status_group.command(name="wlacz", description="Ustawia status RP na 'Włączone' i wyświetla link.")
@app_commands.checks.has_permissions(administrator=True)
async def rp_status_on(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.errors.NotFound:
        print("INFO: Interakcja 'wlacz' wygasła, zanim można było ją odroczyć.")
        return
    
    channel = interaction.guild.get_channel(RP_STATUS_CHANNEL_ID)
    if not channel:
        await interaction.followup.send(f"❌ Nie znaleziono kanału statusu RP o ID {RP_STATUS_CHANNEL_ID}.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🟢 Rozgrywka Role-Play została włączona!",
        description="Serwer jest teraz w trybie RP. Zapraszamy do aktywnej gry!",
        color=discord.Color.from_rgb(87, 242, 135) # Green
    )
    embed.set_author(name="Status RP")
    embed.add_field(name="🔗 Link do serwera", value=f"[Kliknij tutaj, aby dołączyć]({RP_FIXED_LINK})", inline=False)
    embed.set_thumbnail(url=RP_THUMBNAIL_URL)
    embed.set_footer(text=f"Zaktualizowano przez: {interaction.user.display_name}")
    embed.timestamp = datetime.now()

    message_id = load_rp_status_message_id()
    try:
        if message_id:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            await interaction.followup.send("✅ Status RP zaktualizowany na 'Włączone'.", ephemeral=True)
        else:
            message = await channel.send(embed=embed)
            save_rp_status_message_id(message.id)
            await interaction.followup.send("✅ Nowa wiadomość statusu RP wysłana i ustawiona na 'Włączone'.", ephemeral=True)
    except discord.NotFound:
        message = await channel.send(embed=embed)
        save_rp_status_message_id(message.id)
        await interaction.followup.send("✅ Poprzednia wiadomość statusu RP nie znaleziona. Wysłano nową i ustawiono na 'Włączone'.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do wysyłania/edycji wiadomości na kanale statusu RP.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd podczas ustawiania statusu RP: {e}", ephemeral=True)

@rp_status_group.command(name="wylacz", description="Ustawia status RP na 'Wyłączone'.")
@app_commands.checks.has_permissions(administrator=True)
async def rp_status_off(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.errors.NotFound:
        print("INFO: Interakcja 'wylacz' wygasła, zanim można było ją odroczyć.")
        return

    channel = interaction.guild.get_channel(RP_STATUS_CHANNEL_ID)
    if not channel:
        await interaction.followup.send(f"❌ Nie znaleziono kanału statusu RP o ID {RP_STATUS_CHANNEL_ID}.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔴 Rozgrywka Role-Play została wyłączona.",
        description="Serwer powrócił do trybu OOC (Out of Character). Dziękujemy za wspólną grę!",
        color=discord.Color.from_rgb(237, 66, 69) # Red
    )
    embed.set_author(name="Status RP")
    embed.add_field(name="Kiedy następne RP?", value="Śledź kanał z ogłoszeniami, aby być na bieżąco!", inline=False)
    embed.set_thumbnail(url=RP_THUMBNAIL_URL)
    embed.set_footer(text=f"Zaktualizowano przez: {interaction.user.display_name}")
    embed.timestamp = datetime.now()

    message_id = load_rp_status_message_id()
    try:
        if message_id:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            await interaction.followup.send("✅ Status RP zaktualizowany na 'Wyłączone'.", ephemeral=True)
        else:
            message = await channel.send(embed=embed)
            save_rp_status_message_id(message.id)
            await interaction.followup.send("✅ Nowa wiadomość statusu RP wysłana i ustawiona na 'Wyłączone'.", ephemeral=True)
    except discord.NotFound:
        message = await channel.send(embed=embed)
        save_rp_status_message_id(message.id)
        await interaction.followup.send("✅ Poprzednia wiadomość statusu RP nie znaleziona. Wysłano nową i ustawiono na 'Wyłączone'.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do wysyłania/edycji wiadomości na kanale statusu RP.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd podczas ustawiania statusu RP: {e}", ephemeral=True)


# --- Widok ankiety Roleplay ---
class RoleplayPollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_vote(self, interaction: discord.Interaction, option: str):
        await interaction.response.defer(ephemeral=True)
        votes_data = load_votes()

        if interaction.user.id in votes_data.get("voted_users", []):
            await interaction.followup.send("Już zagłosowałeś/aś w tej ankiecie.", ephemeral=True)
            return

        votes_data.setdefault("votes", {}).setdefault(option, 0)
        votes_data["votes"][option] += 1
        votes_data.setdefault("voted_users", []).append(interaction.user.id)

        save_votes(votes_data)
        await interaction.followup.send(f"Twój głos na **{option}** został zapisany. Dziękujemy!", ephemeral=True)

    @discord.ui.button(label="14:00", style=discord.ButtonStyle.primary, custom_id="rp_poll_1400")
    async def time_14(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "14:00")

    @discord.ui.button(label="15:00", style=discord.ButtonStyle.primary, custom_id="rp_poll_1500")
    async def time_15(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "15:00")

    @discord.ui.button(label="16:00", style=discord.ButtonStyle.primary, custom_id="rp_poll_1600")
    async def time_16(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "16:00")

    @discord.ui.button(label="17:00", style=discord.ButtonStyle.primary, custom_id="rp_poll_1700")
    async def time_17(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "17:00")


# --- Zadania w tle dla ankiety RP ---
POLL_CHANNEL_ID = 1437132763827540029
TIMEZONE = ZoneInfo("Europe/Warsaw")
POLL_SEND_TIME = time(22, 0, tzinfo=TIMEZONE)
RESULTS_ANNOUNCE_TIME = time(13, 0, tzinfo=TIMEZONE)

@tasks.loop(time=POLL_SEND_TIME)
async def send_rp_poll(client: discord.Client):
    print("INFO: Uruchamiam zadanie wysyłania ankiety RP.")
    channel = client.get_channel(POLL_CHANNEL_ID)
    if not channel:
        print(f"BŁĄD: Nie znaleziono kanału ankiety o ID {POLL_CHANNEL_ID}.")
        return

    # Reset votes file for the new poll
    save_votes({"votes": {}, "voted_users": []})

    embed = discord.Embed(
        title="⏰ Kiedy jutro gramy w Roleplay?",
        description="Wybierz preferowaną godzinę rozpoczęcia jutrzejszej sesji RP. Głosowanie trwa do jutra do 13:00.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Głosować można tylko raz.")
    
    view = RoleplayPollView()
    await channel.send(embed=embed, view=view)
    print(f"INFO: Ankieta RP została wysłana na kanał #{channel.name}.")

@tasks.loop(time=RESULTS_ANNOUNCE_TIME)
async def announce_rp_results(client: discord.Client):
    print("INFO: Uruchamiam zadanie ogłaszania wyników ankiety RP.")
    channel = client.get_channel(POLL_CHANNEL_ID)
    if not channel:
        print(f"BŁĄD: Nie znaleziono kanału ankiety o ID {POLL_CHANNEL_ID}.")
        return

    votes_data = load_votes()
    votes = votes_data.get("votes", {})

    if not votes:
        embed = discord.Embed(
            title="📊 Wyniki ankiety RP",
            description="Niestety, nikt nie zagłosował w ankiecie dotyczącej jutrzejszego Roleplay.",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)
        # Clear votes even if no one voted, to be safe
        save_votes({"votes": {}, "voted_users": []})
        return

    # Find the best time(s)
    max_votes = 0
    best_times = []
    for time, count in sorted(votes.items()): # sorted to have deterministic output on ties
        if count > max_votes:
            max_votes = count
            best_times = [time]
        elif count == max_votes:
            best_times.append(time)
    
    # Prepare result message
    if len(best_times) == 1:
        result_text = f"Najwięcej głosów ({max_votes}) zdobyła godzina **{best_times[0]}**! 🎉"
    else:
        result_text = f"Mamy remis! Godziny z największą liczbą głosów ({max_votes}) to: **{', '.join(best_times)}**. Administracja podejmie ostateczną decyzję."

    embed = discord.Embed(
        title="📊 Wyniki ankiety RP",
        description=result_text,
        color=discord.Color.green()
    )

    votes_summary = "\n".join([f"**{time}**: {count} głos(ów)" for time, count in sorted(votes.items())])
    embed.add_field(name="Podsumowanie głosów", value=votes_summary if votes_summary else "Brak głosów.", inline=False)
    
    await channel.send(embed=embed)
    print(f"INFO: Wyniki ankiety RP zostały ogłoszone na kanale #{channel.name}.")

    # Clear votes after announcing
    save_votes({"votes": {}, "voted_users": []})


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.first_ready = True
        self.gemini_api_key_cycler = None
        
        # Status cycle
        self.rp_on_statuses = cycle([
            "{rp_count} pacjentów online",
            "{voice_count} osób w rozmowach",
            "pomoc | /help"
        ])
        self.rp_off_status = "RP jest wyłączone"

    async def setup_hooks(self) -> None:
        # Register the persistent view for the RP poll
        # This ensures the view works even after the bot restarts.
        self.add_view(RoleplayPollView())

    async def on_ready(self):
        await self.tree.sync()
        print(f'Zalogowano jako {self.user}! Bot jest gotowy do działania.')

        if self.first_ready:
            self.first_ready = False
            for guild in self.guilds:
                await check_and_update_messages(guild, self)
            print("INFO: Zakończono automatyczną weryfikację wiadomości na wszystkich serwerach.")


        # Configure Gemini AI Key Cycler
        if hasattr(config, 'GEMINI_API_KEYS') and isinstance(config.GEMINI_API_KEYS, list) and config.GEMINI_API_KEYS:
            self.gemini_api_key_cycler = cycle(config.GEMINI_API_KEYS)
            print(f"INFO: Załadowano {len(config.GEMINI_API_KEYS)} kluczy API Gemini. Rotacja kluczy jest gotowa.")

            # --- DIAGNOSTYKA: Listowanie dostępnych modeli ---
            print("\n--- DIAGNOSTYKA MODELI GEMINI ---")
            for i, api_key in enumerate(config.GEMINI_API_KEYS):
                try:
                    genai.configure(api_key=api_key)
                    print(f"--- Klucz API #{i+1} (końcówka: ...{api_key[-4:]}) ---")
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            print(f"  -> Dostępny model: {m.name}")
                    print("-" * (35 + len(api_key[-4:])))
                except Exception as e:
                    print(f"  -> BŁĄD przy listowaniu modeli dla klucza #{i+1}: {e}")
            print("--- KONIEC DIAGNOSTYKI ---\n")
            # --- KONIEC DIAGNOSTYKI ---

        else:
            print("OSTRZEŻENIE: Brak listy GEMINI_API_KEYS w config.py. Funkcjonalność Gemini AI będzie niedostępna.")
        
        # Start background tasks
        self.check_expired_roles.start()
        self.change_status.start()
        
        # Start RP poll tasks
        send_rp_poll.start(self)
        announce_rp_results.start(self)

    @tasks.loop(seconds=15)
    async def change_status(self):
        status_text = "..." # Default status

        if not self.guilds:
            await self.change_presence(activity=discord.Game(name=status_text))
            return

        guild = self.guilds[0]

        # Check RP status
        rp_is_on = False
        message_id = load_rp_status_message_id()
        if message_id:
            channel = guild.get_channel(RP_STATUS_CHANNEL_ID)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message.embeds and message.embeds[0].title.startswith("🟢"):
                        rp_is_on = True
                except (discord.NotFound, discord.Forbidden):
                    pass # RP status remains False

        if rp_is_on:
            status_text = next(self.rp_on_statuses)
            
            # Calculate dynamic values
            roles_data = load_roles()
            pacjent_role_id = roles_data.get("SECTOR_ROLE_IDS", {}).get("Pacjent")
            rp_role = guild.get_role(pacjent_role_id) if pacjent_role_id else None
            rp_count = 0
            if rp_role:
                rp_count = sum(1 for member in guild.members if rp_role in member.roles and member.status != discord.Status.offline)
            
            voice_count = sum(len(vc.members) for vc in guild.voice_channels)

            # Format status
            status_text = status_text.format(rp_count=rp_count, voice_count=voice_count)
            
        else:
            status_text = self.rp_off_status

        await self.change_presence(activity=discord.Game(name=status_text))

    @tasks.loop(minutes=1)
    async def check_expired_roles(self):
        print("INFO: Sprawdzam wygasłe role tymczasowe...")
        users_data = load_user_data()
        current_time = datetime.now()
        
        for user_id_str, user_data in list(users_data.items()): # Use list() to allow modification during iteration
            user_id = int(user_id_str)
            if "active_temp_roles" in user_data and user_data["active_temp_roles"]:
                roles_to_keep = []
                member = None # Fetch member once per user if needed
                
                for temp_role_entry in user_data["active_temp_roles"]:
                    expires_at_str = temp_role_entry["expires_at"]
                    expires_at = datetime.fromisoformat(expires_at_str)

                    if current_time >= expires_at:
                        # Role has expired
                        role_id = temp_role_entry["role_id"]
                        return_role_id = temp_role_entry.get("return_role_id")

                        # Find the member across all guilds the bot is in
                        for guild in self.guilds:
                            member = guild.get_member(user_id)
                            if member:
                                break
                        
                        if member:
                            # Remove the expired role
                            expired_role = discord.utils.get(member.guild.roles, id=role_id)
                            if expired_role and expired_role in member.roles:
                                try:
                                    await member.remove_roles(expired_role, reason="Wygasła rola tymczasowa.")
                                    print(f"INFO: Usunięto wygasłą rolę '{expired_role.name}' z użytkownika {member.display_name}.")
                                except discord.Forbidden:
                                    print(f"BŁĄD: Brak uprawnień do usunięcia roli '{expired_role.name}' z użytkownika {member.display_name}.")
                                except Exception as e:
                                    print(f"BŁĄD: Nieoczekiwany błąd podczas usuwania roli '{expired_role.name}': {e}")
                            
                            # Add the return role, if specified
                            if return_role_id:
                                return_role = discord.utils.get(member.guild.roles, id=return_role_id)
                                if return_role:
                                    try:
                                        await member.add_roles(return_role, reason="Automatyczny powrót po upływie czasu przypisania.")
                                        print(f"INFO: Przywrócono rolę '{return_role.name}' dla użytkownika {member.display_name}.")
                                    except discord.Forbidden:
                                        print(f"BŁĄD: Brak uprawnień do przywrócenia roli '{return_role.name}' dla {member.display_name}.")
                                    except Exception as e:
                                        print(f"BŁĄD: Nieoczekiwany błąd podczas przywracania roli '{return_role.name}': {e}")
                                else:
                                    print(f"BŁĄD: Nie znaleziono roli powrotu o ID {return_role_id} na serwerze.")
                        else:
                            print(f"INFO: Użytkownik {user_id} nie znaleziony na żadnym serwerze, nie można zarządzać rolami.")
                    else:
                        roles_to_keep.append(temp_role_entry)
                
                user_data["active_temp_roles"] = roles_to_keep
                users_data[user_id_str] = user_data
        
        save_user_data(users_data)
        print("INFO: Zakończono sprawdzanie wygasłych ról tymczasowych.")

    async def on_message(self, message: discord.Message):
        # Ignore messages from itself
        if message.author == self.user:
            return

        # Check for bumps from DISBOARD (ID: 302050872383242240)
        if message.author.id == 302050872383242240 and message.embeds:
            for embed in message.embeds:
                if embed.description and "Bump done!" in embed.description:
                    # Using regex to find the user ID more reliably
                    match = re.search(r'<@!?(\d+)>', embed.description)
                    if match:
                        user_id = int(match.group(1))
                        bumper = self.get_user(user_id)
                        
                        if bumper:
                            try:
                                # Send notification to admin channel
                                admin_channel_id = config.ADMIN_COMMANDS_CHANNEL_ID
                                admin_role_id = config.ADMIN_COMMANDS_ROLE_ID
                                
                                admin_channel = self.get_channel(admin_channel_id)
                                if admin_channel:
                                    role_mention = f"<@&{admin_role_id}>"
                                    
                                    embed = discord.Embed(
                                        title="💰 Nagroda za Bump!",
                                        description=f"Użytkownik {bumper.mention} podbił serwer. Użyj poniższej komendy, aby przyznać nagrodę.",
                                        color=discord.Color.gold()
                                    )
                                    embed.add_field(name="Komenda do skopiowania", value=f"```!economy add {user_id} 200```")
                                    
                                    await admin_channel.send(content=role_mention, embed=embed)
                                    print(f"INFO: Sent bump reward notification for {bumper.display_name}.")
                                else:
                                    print(f"BŁĄD: Nie znaleziono kanału dla powiadomień admina o ID: {admin_channel_id}")

                                # Add a reaction to confirm processing
                                await message.add_reaction("✅")
                            except discord.Forbidden:
                                print(f"BŁĄD: Brak uprawnień do wysłania wiadomości na kanale admina lub dodania reakcji.")
                            except Exception as e:
                                print(f"BŁĄD: Nieoczekiwany błąd podczas wysyłania powiadomienia o nagrodzie za bump: {e}")
        # Gemini AI integration
        if hasattr(config, 'GEMINI_CHANNEL_ID') and message.channel.id == config.GEMINI_CHANNEL_ID and not message.author.bot:
            if self.gemini_api_key_cycler:
                await message.channel.typing()
                
                success = False
                ai_settings = load_ai_settings()
                persona_prefix = ai_settings.get("persona", "")
                
                full_prompt = f"{persona_prefix}\n\n{message.content}" if persona_prefix else message.content

                # Loop through all available keys once
                for _ in range(len(config.GEMINI_API_KEYS)):
                    try:
                        api_key = next(self.gemini_api_key_cycler)
                        genai.configure(api_key=api_key)
                        
                        # Reverted to prepending the prompt instead of using system_instruction
                        model = genai.GenerativeModel("gemini-flash-latest")
                        response = model.generate_content(full_prompt)
                        
                        if response.candidates:
                            text_response = ''.join(part.text for part in response.candidates[0].content.parts)
                            if len(text_response) > 2000:
                                await message.channel.send(f"Odpowiedź Gemini AI (skrócona):\n{text_response[:1990]}...")
                            else:
                                await message.channel.send(text_response)
                        else:
                            # This case might happen if the content is blocked by safety settings
                            await message.channel.send("Przepraszam, Gemini AI nie zwróciło odpowiedzi. Mogło to być spowodowane filtrami bezpieczeństwa.")
                        
                        success = True
                        break # Exit loop on success

                    except Exception as e:
                        print(f"BŁĄD Gemini AI z kluczem kończącym się na '...{api_key[-4:]}': {e}")
                        # The loop will continue to the next key

                if not success:
                    await message.channel.send("Przepraszam, wystąpił błąd podczas komunikacji z Gemini AI. Wszystkie dostępne klucze API zawiodły lub zwróciły błąd.")
            else:
                await message.channel.send("Przepraszam, klucze API Gemini AI nie zostały poprawnie skonfigurowane.")
            return # Prevent further processing if this was an AI message

client = MyClient()
client.tree.add_command(rp_status_group)
        






@client.tree.command(name="setup", description="Inteligentnie konfiguruje lub aktualizuje strukturę serwera.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_server(interaction: discord.Interaction):
    """
    Inteligentnie tworzy lub aktualizuje strukturę serwera, role i wiadomości.
    - Sprawdza istnienie kategorii i kanałów, tworząc tylko brakujące.
    - Sprawdza istnienie ról, tworząc tylko brakujące.
    - Wyszukuje kluczowe wiadomości (regulamin, weryfikacja) i edytuje je, jeśli są nieaktualne,
      lub tworzy je, jeśli ich brakuje.
    """
    global verification_message_id
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Ta komenda może być użyta tylko na serwerze.", ephemeral=True)
        return

    status_updates = []

    # --- Krok 1: Tworzenie ról ---
    await interaction.edit_original_response(content="⏳ Weryfikuję i tworzę role...")
    created_roles = {}
    roles_data = load_roles()
    for role_name, color in reversed(roles_data.get("ROLES_TO_CREATE", [])):
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            created_roles[role_name] = existing_role
        else:
            role = await guild.create_role(name=role_name, color=color, reason="Automatyczna konfiguracja serwera.")
            created_roles[role_name] = role
            status_updates.append(f"✅ Utworzono rolę: {role_name}")

    # --- Krok 2: Weryfikacja i czyszczenie struktury kanałów ---
    await interaction.edit_original_response(content="⏳ Weryfikuję i czyszczę strukturę kanałów...")
    created_channels = {}
    for category_name, text_channels, voice_channels in SERVER_STRUCTURE:
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            status_updates.append(f"⚠️ Nie znaleziono kategorii '{category_name}'. Pomięto.")
            continue

        # Weryfikuj i czyść kanały tekstowe
        for channel_name in text_channels:
            sanitized_name = channel_name.lower().replace(' ', '-')
            if sanitized_name.startswith("#️⃣・"):
                sanitized_name = sanitized_name[3:]
            elif sanitized_name.startswith("#"):
                sanitized_name = sanitized_name[1:]
            sanitized_name = ''.join(c for c in sanitized_name if c.isalnum() or c == '-')

            matching_channels = [ch for ch in category.text_channels if ch.name == sanitized_name]

            channel = None
            if matching_channels:
                matching_channels.sort(key=lambda c: c.position)
                channel = matching_channels[0]
                if len(matching_channels) > 1:
                    for duplicate_channel in matching_channels[1:]:
                        await duplicate_channel.delete(reason="Automatyczne usuwanie duplikatów.")
                        status_updates.append(f"🗑️ Usunięto zduplikowany kanał: {duplicate_channel.name}")
            else:
                status_updates.append(f"⚠️ Nie znaleziono kanału '{channel_name}'. Nie zostanie utworzony.")

            if channel:
                key_name = channel_name.replace("#️⃣・", "").replace("#", "")
                created_channels[key_name] = channel

        # Weryfikuj i czyść kanały głosowe
        for channel_name in voice_channels:
            matching_channels = [ch for ch in category.voice_channels if ch.name == channel_name]

            if matching_channels:
                matching_channels.sort(key=lambda c: c.position)
                if len(matching_channels) > 1:
                    for duplicate_channel in matching_channels[1:]:
                        await duplicate_channel.delete(reason="Automatyczne usuwanie duplikatów.")
                        status_updates.append(f"🗑️ Usunięto zduplikowany kanał głosowy: {duplicate_channel.name}")
            else:
                status_updates.append(f"⚠️ Nie znaleziono kanału głosowego '{channel_name}'. Nie zostanie utworzony.")

    # --- Krok 3: Konfiguracja uprawnień ---
    await interaction.edit_original_response(content="⏳ Konfiguruję uprawnienia...")
    everyone_role = guild.default_role
    pacjent_role = created_roles.get("Pacjent")
    admin_role = created_roles.get("Administracja")
    dyrektor_role = created_roles.get("Dyrektor Placówki")

    # Ustawienia dla kanału weryfikacji
    weryfikacja_channel = created_channels.get("weryfikacja")
    if weryfikacja_channel:
        await weryfikacja_channel.set_permissions(everyone_role, view_channel=True, read_message_history=True, send_messages=True)
        await weryfikacja_channel.set_permissions(pacjent_role, view_channel=False)

    # Ustawienia dla kategorii informacyjnej
    info_category = discord.utils.get(guild.categories, name="📜 INFORMACJE 📜")
    if info_category and pacjent_role:
        await info_category.set_permissions(everyone_role, view_channel=False)
        await info_category.set_permissions(pacjent_role, view_channel=True, send_messages=False)
        # Nadpisz uprawnienia dla kanału weryfikacji, aby był widoczny dla @everyone
        if weryfikacja_channel:
            await weryfikacja_channel.set_permissions(everyone_role, view_channel=True, send_messages=True)


    # Ustawienia dla kategorii administracyjnej
    admin_category = discord.utils.get(guild.categories, name="🔒 ADMINISTRACJA 🔒")
    if admin_category and admin_role and dyrektor_role and pacjent_role:
        await admin_category.set_permissions(everyone_role, view_channel=False)
        await admin_category.set_permissions(pacjent_role, view_channel=False)
        await admin_category.set_permissions(admin_role, view_channel=True)
        await admin_category.set_permissions(dyrektor_role, view_channel=False)

    # --- Krok 4: Wysyłanie i aktualizacja wiadomości ---
    await interaction.edit_original_response(content="⏳ Aktualizuję kluczowe wiadomości...")

    # Funkcja pomocnicza do wysyłania lub edytowania embedów
    async def send_or_edit_embed(channel_key: str, embed_title: str, embed_description: str, embed_color: discord.Color):
        channel = created_channels.get(channel_key)
        if not channel:
            status_updates.append(f"❌ Nie znaleziono kanału '{channel_key}' do wysłania wiadomości.")
            return None

        new_embed = discord.Embed(title=embed_title, description=embed_description, color=embed_color)
        
        # Wyszukaj wiadomość od bota z tym samym tytułem embeda
        async for message in channel.history(limit=50):
            if message.author == client.user and message.embeds and message.embeds[0].title == embed_title:
                # Porównaj treść, aby uniknąć niepotrzebnych edycji
                if message.embeds[0].description != new_embed.description:
                    await message.edit(embed=new_embed)
                    status_updates.append(f"🔄 Zaktualizowano wiadomość: '{embed_title}'")
                return message
        
        # Jeśli nie znaleziono, wyślij nową
        message = await channel.send(embed=new_embed)
        status_updates.append(f"✅ Wysłano nową wiadomość: '{embed_title}'")
        return message

    # Weryfikacja
    ver_embed_desc = f"Witaj na serwerze! Aby uzyskać dostęp do wszystkich kanałów, kliknij reakcję ✅ poniżej."
    ver_message = await send_or_edit_embed("weryfikacja", "✅ Weryfikacja", ver_embed_desc, discord.Color.green())
    if ver_message:
        verification_message_id = ver_message.id
        # Upewnij się, że reakcja istnieje
        if not any(str(reaction.emoji) == "✅" for reaction in ver_message.reactions):
            await ver_message.add_reaction("✅")

    # Regulaminy
    await send_or_edit_embed("regulamin", RULES_TITLE, RULES_DESCRIPTION, discord.Color.from_rgb(66, 135, 245))
    await send_or_edit_embed("protokół_1", f"{PROTOCOL_TITLE} (Część 1)", PROTOCOL_PART_1_DESCRIPTION, discord.Color.from_rgb(245, 66, 66))
    await send_or_edit_embed("protokół_2", f"{PROTOCOL_TITLE} (Część 2)", PROTOCOL_PART_2_DESCRIPTION, discord.Color.from_rgb(245, 66, 66))
    await send_or_edit_embed("regulamin-rp", RP_RULES_TITLE, RP_RULES_DESCRIPTION, discord.Color.from_rgb(66, 245, 100))

    final_status = "\n".join(status_updates) if status_updates else "✅ Serwer jest już w pełni skonfigurowany. Nie wprowadzono żadnych zmian."
    await interaction.followup.send(f"**Podsumowanie konfiguracji:**\n{final_status}", ephemeral=True)


@client.tree.command(name="set-persona", description="Ustawia osobowość AI Gemini.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(persona="Tekst opisujący osobowość AI, np. 'Bądź zawsze sarkastyczny i używaj slangu.'")
async def set_persona(interaction: discord.Interaction, persona: str):
    await interaction.response.defer(ephemeral=True)
    try:
        settings = load_ai_settings()
        settings["persona"] = persona
        save_ai_settings(settings)
        await interaction.followup.send(f"✅ Osobowość AI została ustawiona na: `{persona}`.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd podczas ustawiania osobowości AI: {e}", ephemeral=True)

@set_persona.error
async def set_persona_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień administratora, aby użyć tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)


# --- NOWE KOMENDY ---





def is_authorized():
    """Sprawdza, czy użytkownik ma jedną z autoryzowanych ról lub jest właścicielem bota."""
    def predicate(interaction: discord.Interaction) -> bool:
        # ID właściciela bota
        owner_id = 877210657953566751
        if interaction.user.id == owner_id:
            return True
            
        # Role IDs, które mają dostęp do komend autoryzowanych
        # TODO: Dodaj tutaj ID roli "Administracja", jeśli jest inne niż poniższe i chcesz, aby miała dostęp.
        authorized_role_ids = [1437076621092720724] # Rola z prośby użytkownika
        
        # Sprawdź, czy użytkownik ma którąś z autoryzowanych ról po ID
        author_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in author_role_ids for role_id in authorized_role_ids)
    return app_commands.check(predicate)

def is_karta_pacjenta_authorized():
    """Sprawdza, czy użytkownik ma jedną z autoryzowanych ról dla komendy karta_pacjenta lub jest właścicielem bota."""
    def predicate(interaction: discord.Interaction) -> bool:
        owner_id = 877210657953566751 
        if interaction.user.id == owner_id:
            return True
            
        # Role IDs that are authorized for /karta_pacjenta
        authorized_role_ids = [1437895172624224347] # User specified role ID
        
        # Check if the user has any of the authorized roles by ID
        author_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in author_role_ids for role_id in authorized_role_ids)
    return app_commands.check(predicate)

@client.tree.command(name="sentenced", description="Wystawia oficjalną notatkę o nałożonej karze.")
@is_authorized()
@app_commands.describe(
    uzytkownik="Osoba, która otrzymuje karę.",
    rodzaj_kary="Typ nałożonej kary.",
    powod="Powód nałożenia kary.",
    kara_pieniezna="Kara pieniężna (odejmowana z konta).",
    czas_trwania="Czas trwania kary (np. '30m', '2h', '7d'). Opcjonalne."
)
@app_commands.choices(rodzaj_kary=[
    app_commands.Choice(name="[Forensic]", value="Forensic"),
    app_commands.Choice(name="[MS]", value="MS"),
    app_commands.Choice(name="[Padded]", value="Padded"),
    app_commands.Choice(name="[Bez zmian]", value="Bez zmian"),
])
async def sentenced(interaction: discord.Interaction, uzytkownik: discord.Member, rodzaj_kary: app_commands.Choice[str], powod: str, kara_pieniezna: app_commands.Range[int, 0], czas_trwania: str = None):
    target_channel_id = config.SENTENCED_CHANNEL_ID
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message(f"❌ Nie znaleziono kanału o ID {target_channel_id}.", ephemeral=True)
        return

    # Parse duration
    duration = parse_duration(czas_trwania)

    # Zapisanie kary w historii użytkownika
    user_data = get_user_data(uzytkownik.id)
    new_sentence = {
        "id": random.randint(10000, 99999), # Proste ID do ewentualnej identyfikacji
        "moderator_id": interaction.user.id,
        "rodzaj_kary": rodzaj_kary.value,
        "powod": powod,
        "kara_pieniezna": kara_pieniezna,
        "czas_trwania_str": czas_trwania,
        "timestamp": datetime.now().isoformat()
    }
    user_data.setdefault('sentences', []).append(new_sentence)
    update_user_data(uzytkownik.id, user_data)


    embed = discord.Embed(
        title="SENTENCED",
        color=discord.Color.dark_red(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Ukarany", value=uzytkownik.mention, inline=False)
    embed.add_field(name="Wystawiający", value=interaction.user.mention, inline=False)
    embed.add_field(name="Rodzaj Kary", value=rodzaj_kary.name, inline=True)
    embed.add_field(name="Kara Pieniężna", value=f"{kara_pieniezna:,} PLN", inline=True)
    
    if duration:
        embed.add_field(name="Czas Trwania", value=f"{czas_trwania}", inline=True)

    embed.add_field(name="Powód", value=powod, inline=False)
    embed.set_thumbnail(url=uzytkownik.avatar.url if uzytkownik.avatar else uzytkownik.default_avatar.url)

    await target_channel.send(embed=embed)
    
    # Send notification for the economy command
    if kara_pieniezna > 0:
        admin_channel_id = config.ADMIN_COMMANDS_CHANNEL_ID
        admin_role_id = config.ADMIN_COMMANDS_ROLE_ID
        
        admin_channel = interaction.guild.get_channel(admin_channel_id)
        if admin_channel:
            role_mention = f"<@&{admin_role_id}>"
            
            embed_admin = discord.Embed(
                title="💸 Nałożono Karę Pieniężną",
                description=f"Kara dla {uzytkownik.mention}. Użyj poniższej komendy, aby odjąć środki.",
                color=discord.Color.dark_red()
            )
            embed_admin.add_field(name="Komenda do skopiowania", value=f"```!economy remove {uzytkownik.id} {kara_pieniezna}```")
            
            try:
                await admin_channel.send(content=role_mention, embed=embed_admin)
                print(f"INFO: Sent sentence penalty notification for {uzytkownik.display_name}.")
            except discord.Forbidden:
                print(f"BŁĄD: Brak uprawnień do wysłania wiadomości na kanale admina.")
        else:
            print(f"BŁĄD: Nie znaleziono kanału dla powiadomień admina o ID: {admin_channel_id}")

    await interaction.response.send_message(f"✅ Pomyślnie wystawiono notatkę o karze dla {uzytkownik.display_name}. Kara została zapisana w jego historii.", ephemeral=True)

@client.tree.command(name="sentenced-history", description="Wyświetla historię kar użytkownika.")
@is_authorized() # Only authorized users should see this history
@app_commands.describe(
    uzytkownik="Użytkownik, którego historię kar chcesz zobaczyć."
)
async def sentenced_history(interaction: discord.Interaction, uzytkownik: discord.Member):
    await interaction.response.defer(ephemeral=True)

    user_data = get_user_data(uzytkownik.id)
    sentences = user_data.get("sentences", [])

    if not sentences:
        await interaction.followup.send(f"✅ Użytkownik {uzytkownik.display_name} nie posiada żadnej historii kar.", ephemeral=True)
        return

    # Sort sentences by timestamp in descending order (newest first)
    sentences.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=True)

    # Limit to the last 5 sentences for brevity
    display_sentences = sentences[:5]

    embed = discord.Embed(
        title=f"Historia Kar dla: {uzytkownik.display_name}",
        description=f"Ostatnie {len(display_sentences)} kary (z {len(sentences)} wszystkich kar).",
        color=discord.Color.dark_blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=uzytkownik.avatar.url if uzytkownik.avatar else uzytkownik.default_avatar.url)

    for sentence in display_sentences:
        moderator = interaction.guild.get_member(sentence["moderator_id"])
        moderator_name = moderator.display_name if moderator else "Nieznany Moderator"
        
        timestamp = datetime.fromisoformat(sentence["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

        value = (
            f"**Typ:** {sentence['rodzaj_kary']}\n"
            f"**Powód:** {sentence['powod']}\n"
            f"**Kara pieniężna:** {sentence['kara_pieniezna']:,} PLN\n"
            f"**Czas trwania:** {sentence['czas_trwania_str'] or 'Brak'}\n"
            f"**Moderator:** {moderator_name}\n"
            f"**Data:** {timestamp}"
        )
        embed.add_field(name=f"Kara ID: {sentence['id']}", value=value, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@sentenced_history.error
async def sentenced_history_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)


@client.tree.command(name="usun-sentenced", description="Usuwa określoną karę z historii użytkownika.")
@is_authorized()
@app_commands.describe(
    uzytkownik="Użytkownik, któremu chcesz usunąć karę.",
    kara_id="ID kary do usunięcia (znajdziesz je w /sentenced-history)."
)
async def usun_sentenced(interaction: discord.Interaction, uzytkownik: discord.Member, kara_id: int):
    await interaction.response.defer(ephemeral=True)

    user_data = get_user_data(uzytkownik.id)
    sentences = user_data.get("sentences", [])

    original_sentence_count = len(sentences)
    sentence_to_remove = next((s for s in sentences if s.get("id") == kara_id), None)

    if not sentence_to_remove:
        await interaction.followup.send(f"❌ Nie znaleziono kary o ID `{kara_id}` dla użytkownika {uzytkownik.display_name}.", ephemeral=True)
        return

    sentences.remove(sentence_to_remove)
    user_data["sentences"] = sentences
    update_user_data(uzytkownik.id, user_data)

    await interaction.followup.send(f"✅ Pomyślnie usunięto karę o ID `{kara_id}` z historii {uzytkownik.display_name}.", ephemeral=True)

    # Log deletion to the log channel
    log_channel = await get_log_channel(interaction.guild)
    if log_channel:
        embed = discord.Embed(
            title="Kara Usunięta",
            description=f"Moderator {interaction.user.mention} usunął karę z historii użytkownika {uzytkownik.mention}.",
            color=discord.Color.dark_green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="ID Usuniętej Kary", value=str(kara_id), inline=False)
        embed.add_field(name="Usunięta Kara", value=(
            f"**Typ:** {sentence_to_remove.get('rodzaj_kary', 'B/D')}\n"
            f"**Powód:** {sentence_to_remove.get('powod', 'B/D')}\n"
            f"**Kara pieniężna:** {sentence_to_remove.get('kara_pieniezna', 'B/D')} PLN"
        ), inline=False)
        await log_channel.send(embed=embed)


@client.tree.command(name="warn", description="Nadaje użytkownikowi ostrzeżenie w nowym systemie kar.")
@is_authorized()
@app_commands.describe(
    uzytkownik="Osoba, która otrzymuje ostrzeżenie.",
    poziom="Poziom ostrzeżenia (strefa kary).",
    powod="Powód nałożenia ostrzeżenia."
)
@app_commands.choices(poziom=[
    app_commands.Choice(name="0️⃣ Strefa Zero", value="zero"),
    app_commands.Choice(name="🟢 Strefa Zielona", value="green"),
    app_commands.Choice(name="🟡 Strefa Żółta", value="yellow"),
    app_commands.Choice(name="🔴 Strefa Czerwona", value="red"),
    app_commands.Choice(name="⚫ Strefa Czarna", value="black"),
])
async def warn(interaction: discord.Interaction, uzytkownik: discord.Member, poziom: app_commands.Choice[str], powod: str):
    await interaction.response.defer(ephemeral=True)

    # --- Data Handling ---
    user_data = get_user_data(uzytkownik.id)
    new_warning = {
        "id": random.randint(10000, 99999),
        "moderator_id": interaction.user.id,
        "level": poziom.value,
        "reason": powod,
        "timestamp": datetime.now().isoformat()
    }
    user_data.setdefault('warnings', []).append(new_warning)

    # --- Punishment Logic ---
    warnings = user_data.get('warnings', [])
    yellow_warnings = [w for w in warnings if w['level'] == 'yellow']
    red_warnings = [w for w in warnings if w['level'] == 'red']
    
    consequence_info = ""

    if poziom.value == 'black':
        update_user_data(uzytkownik.id, user_data)
        try:
            await uzytkownik.ban(reason=f"Ostrzeżenie w strefie czarnej: {powod}")
            consequence_info = "\n\n**Użytkownik został permanentnie zbanowany!**"
        except discord.Forbidden:
            consequence_info = "\n\n**Nie udało się zbanować użytkownika (brak uprawnień)!**"
    
    elif len(red_warnings) >= 2 or (len(red_warnings) >= 1 and len(yellow_warnings) >= 2):
        update_user_data(uzytkownik.id, user_data)
        try:
            await uzytkownik.ban(reason=f"Przekroczono limit ostrzeżeń (2 czerwone lub 1 czerwone + 2 żółte): {powod}")
            consequence_info = "\n\n**Użytkownik został permanentnie zbanowany z powodu przekroczenia limitu ostrzeżeń!**"
        except discord.Forbidden:
            consequence_info = "\n\n**Nie udało się zbanować użytkownika (brak uprawnień)!**"

    elif len(yellow_warnings) >= 3:
        user_data['cannot_apply_for_admin'] = True
        consequence_info = "\n\n**Użytkownik otrzymał 3 żółte ostrzeżenia i nie może już aplikować na stanowiska administracyjne.**"

    update_user_data(uzytkownik.id, user_data)


    # --- Role Management ---
    roles_data = load_roles()
    punishment_roles_map = roles_data.get("PUNISHMENT_ROLES", {})
    
    # Remove all other punishment roles
    all_punishment_role_ids = [role_id for roles in punishment_roles_map.values() for role_id in roles]
    roles_to_remove = [role for role in uzytkownik.roles if role.id in all_punishment_role_ids]
    if roles_to_remove:
        await uzytkownik.remove_roles(*roles_to_remove, reason="Aktualizacja roli ostrzeżenia")

    # Add the new role
    if poziom.value in punishment_roles_map and punishment_roles_map[poziom.value]:
        # Assign the first role from the list for the given level
        new_role_id = punishment_roles_map[poziom.value][0]
        new_role = interaction.guild.get_role(new_role_id)
        if new_role:
            await uzytkownik.add_roles(new_role, reason=f"Ostrzeżenie: {powod}")
            role_info = f"Nadano rolę: {new_role.mention}"
        else:
            role_info = f"Nie znaleziono roli dla strefy '{poziom.name}' o ID `{new_role_id}`."
    else:
        role_info = "Brak roli do nadania dla tej strefy."


    # --- Announcement ---
    target_channel_id = config.SENTENCED_CHANNEL_ID
    target_channel = interaction.guild.get_channel(target_channel_id)
    if not target_channel:
        await interaction.followup.send(f"✅ Ostrzeżenie zostało zapisane, ale nie znaleziono kanału do ogłoszeń o ID {target_channel_id}.", ephemeral=True)
        return

    level_colors = {
        "zero": discord.Color.light_grey(),
        "green": discord.Color.green(),
        "yellow": discord.Color.gold(),
        "red": discord.Color.red(),
        "black": discord.Color.darker_grey()
    }

    embed = discord.Embed(
        title=f"OSTRZEŻENIE - {poziom.name}",
        color=level_colors.get(poziom.value, discord.Color.default()),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Ukarany", value=uzytkownik.mention, inline=False)
    embed.add_field(name="Wystawiający", value=interaction.user.mention, inline=False)
    embed.add_field(name="Powód", value=powod, inline=False)
    embed.add_field(name="Zarządzanie Rolami", value=role_info, inline=False)

    if consequence_info:
        embed.description = consequence_info

    embed.set_thumbnail(url=uzytkownik.avatar.url if uzytkownik.avatar else uzytkownik.default_avatar.url)

    await target_channel.send(embed=embed)

    await interaction.followup.send(f"✅ Pomyślnie nadano ostrzeżenie w strefie '{poziom.name}' dla {uzytkownik.display_name}. Ostrzeżenie zostało zapisane.", ephemeral=True)

@warn.error
async def warn_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)


@client.tree.command(name="rp", description="Wysyła ogłoszenie RP na wyznaczony kanał.")
@is_authorized()
@app_commands.describe(ogloszenie="Treść ogłoszenia RP.")
async def rp(interaction: discord.Interaction, ogloszenie: str):
    target_channel_id = config.RP_ANNOUNCEMENT_CHANNEL_ID
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message(f"❌ Nie znaleziono kanału ogłoszeń RP o ID {target_channel_id}.", ephemeral=True)
        return

    embed = discord.Embed(
        title="OGŁOSZENIE RP",
        description=ogloszenie,
        color=discord.Color.from_rgb(255, 255, 255), # Biały
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Ogłoszenie od {interaction.user.display_name}")

    await target_channel.send(embed=embed)
    await interaction.response.send_message("✅ Pomyślnie wysłano ogłoszenie RP.", ephemeral=True)

@client.tree.command(name="suggest", description="Wyślij sugestię dla serwera.")
@app_commands.describe(sugestia="Twoja sugestia.")
async def suggest(interaction: discord.Interaction, sugestia: str):
    suggestions_channel_id = config.SUGGESTIONS_CHANNEL_ID
    suggestions_channel = interaction.guild.get_channel(suggestions_channel_id)

    if not suggestions_channel:
        await interaction.response.send_message(f"❌ Nie znaleziono kanału sugestii o ID {suggestions_channel_id}. Skontaktuj się z administracją.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Nowa Sugestia",
        description=sugestia,
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
    embed.set_footer(text=f"ID Użytkownika: {interaction.user.id}")

    try:
        message = await suggestions_channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        await interaction.response.send_message("✅ Twoja sugestia została wysłana!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot nie ma uprawnień do wysyłania wiadomości lub dodawania reakcji na kanale sugestii.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Wystąpił błąd podczas wysyłania sugestii: {e}", ephemeral=True)

@rp.error
async def rp_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)

@sentenced.error
async def sentenced_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)


# --- Komenda /przenies ---
roles_data = load_roles()
SECTOR_CHOICES = [
    app_commands.Choice(name=sector, value=sector) for sector in roles_data.get("SECTOR_ROLE_IDS", {}).keys()
]

@client.tree.command(name="przenies", description="Przenosi użytkownika do innego sektora na określony czas.")
@is_authorized()
@app_commands.describe(
    uzytkownik="Użytkownik do przeniesienia.",
    do_sektora="Sektor, do którego użytkownik jest tymczasowo przenoszony.",
    na_czas="Czas trwania przeniesienia (np. '30m', '2h', '7d').",
    z_powrotem_do="Sektor, do którego użytkownik wróci po upływie czasu.",
    powod="Powód przeniesienia."
)
@app_commands.choices(do_sektora=SECTOR_CHOICES, z_powrotem_do=SECTOR_CHOICES)
async def przenies(interaction: discord.Interaction, uzytkownik: discord.Member, do_sektora: app_commands.Choice[str], na_czas: str, z_powrotem_do: app_commands.Choice[str], powod: str):
    await interaction.response.defer(ephemeral=True)

    # --- Walidacja ---
    if uzytkownik.bot:
        await interaction.followup.send("❌ Nie można przenosić botów.", ephemeral=True)
        return

    duration = parse_duration(na_czas)
    if not duration:
        await interaction.followup.send("❌ Nieprawidłowy format czasu. Użyj np. '10m', '2h', '1d'.", ephemeral=True)
        return

    # --- Pobieranie ID ról i kanału z konfiguracji ---
    try:
        target_channel_id = config.PRZYPIS_CHANNEL_ID
        roles_data = load_roles()
        sector_roles_ids = roles_data.get("SECTOR_ROLE_IDS", {})
        temp_role_id = sector_roles_ids[do_sektora.value]
        return_role_id = sector_roles_ids[z_powrotem_do.value]
    except (AttributeError, KeyError):
        await interaction.followup.send("❌ Błąd konfiguracji. Upewnij się, że `PRZYPIS_CHANNEL_ID` w `config.py` i `SECTOR_ROLE_IDS` w `roles.json` są poprawnie ustawione.", ephemeral=True)
        return

    # --- Zarządzanie Rolami ---
    guild = interaction.guild
    temp_role = guild.get_role(temp_role_id)
    if not temp_role:
        await interaction.followup.send(f"❌ Nie znaleziono roli dla sektora '{do_sektora.name}' o ID `{temp_role_id}`.", ephemeral=True)
        return

    # Usunięcie wszystkich innych ról sektorowych z użytkownika
    roles_to_remove = [guild.get_role(role_id) for role_id in sector_roles_ids.values()]
    await uzytkownik.remove_roles(*[r for r in roles_to_remove if r and r in uzytkownik.roles], reason=f"Przeniesienie do {do_sektora.name}")

    # Dodanie nowej roli tymczasowej
    await uzytkownik.add_roles(temp_role, reason=f"Tymczasowe przeniesienie do {do_sektora.name}")

    # --- Zarządzanie Danymi ---
    user_data = get_user_data(uzytkownik.id)
    expires_at = datetime.now() + duration
    
    temp_role_entry = {
        "role_id": temp_role_id,
        "expires_at": expires_at.isoformat(),
        "return_role_id": return_role_id,
        "reason": powod,
        "moderator_id": interaction.user.id
    }
    user_data.setdefault('active_temp_roles', []).append(temp_role_entry)
    update_user_data(uzytkownik.id, user_data)

    # --- Potwierdzenie ---
    target_channel = guild.get_channel(target_channel_id)
    if not target_channel:
        await interaction.followup.send(f"⚠️ Pomyślnie przeniesiono użytkownika, ale nie znaleziono kanału do potwierdzeń o ID `{target_channel_id}`.", ephemeral=True)
    else:
        embed = discord.Embed(
            title="PRZENIESIENIE DO SEKTORA",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Przeniesiony", value=uzytkownik.mention, inline=False)
        embed.add_field(name="Wystawiający", value=interaction.user.mention, inline=False)
        embed.add_field(name="Nowy Sektor", value=do_sektora.name, inline=True)
        embed.add_field(name="Czas Trwania", value=na_czas, inline=True)
        embed.add_field(name="Powrót do", value=z_powrotem_do.name, inline=True)
        embed.add_field(name="Powód", value=powod, inline=False)
        embed.set_thumbnail(url=uzytkownik.avatar.url if uzytkownik.avatar else uzytkownik.default_avatar.url)
        
        await target_channel.send(embed=embed)

    await interaction.followup.send(f"✅ Pomyślnie przeniesiono {uzytkownik.display_name} do sektora {do_sektora.name}.", ephemeral=True)





@client.tree.command(name="karta-pacjenta", description="[Admin] Tworzy lub aktualizuje kartę pacjenta.")
@is_karta_pacjenta_authorized()
@app_commands.describe(
    imie_nazwisko="Imię i nazwisko pacjenta (postaci).",
    uzytkownik="Użytkownik Discord, do którego przypisana jest karta.",
    wiek="Wiek pacjenta.",
    pochodzenie="Kraj lub region pochodzenia pacjenta.",
    diagnoza="Oficjalna diagnoza medyczna.",
    recepta="Zapisane leki i dawkowanie.",
    zalecenia="Dodatkowe zalecenia dla personelu.",
    imiona_rodzicow="Imiona rodziców pacjenta.",
    rok_przybycia="Rok przyjęcia do placówki.",
    pokoj="Numer pokoju i/lub sektor."
)
async def karta_pacjenta(
    interaction: discord.Interaction,
    imie_nazwisko: str,
    uzytkownik: discord.Member,
    wiek: app_commands.Range[int, 1, 150],
    pochodzenie: str,
    diagnoza: str,
    recepta: str,
    zalecenia: str,
    imiona_rodzicow: str,
    rok_przybycia: app_commands.Range[int, 1900, 2100],
    pokoj: str
):
    """Tworzy nową kartę pacjenta i zapisuje ją w pliku JSON."""
    # Użyj ID kanału z config.py, jeśli istnieje
    try:
        target_channel_id = config.PATIENT_CARDS_CHANNEL_ID
        target_channel = interaction.guild.get_channel(target_channel_id)
    except AttributeError:
        target_channel_id = None
        target_channel = None

    if not target_channel:
        await interaction.response.send_message(
            f"❌ Nie zdefiniowano `PATIENT_CARDS_CHANNEL_ID` w `config.py` lub kanał nie istnieje.",
            ephemeral=True
        )
        return

    patient_card_data = {
        "imie_nazwisko": imie_nazwisko,
        "wiek": wiek,
        "pochodzenie": pochodzenie,
        "diagnoza": diagnoza,
        "recepta": recepta,
        "zalecenia": zalecenia,
        "imiona_rodzicow": imiona_rodzicow,
        "rok_przybycia": rok_przybycia,
        "pokoj": pokoj,
        "discord_id": uzytkownik.id,
        "author_id": interaction.user.id,
        "last_updated": datetime.now().isoformat()
    }

    # Zapis danych
    cards = load_patient_cards()
    cards[str(uzytkownik.id)] = patient_card_data
    save_patient_cards(cards)

    # Tworzenie embeda
    embed = discord.Embed(
        title=f"Kartoteka Pacjenta",
        description=f"**Pacjent:** {imie_nazwisko}",
        color=discord.Color.from_rgb(173, 216, 230), # Light Blue
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=uzytkownik.display_avatar.url)
    embed.add_field(name="👤 Dane Podstawowe", value=f"**Wiek:** {wiek}\n**Pochodzenie:** {pochodzenie}", inline=True)
    embed.add_field(name="🏥 Informacje o Pobytu", value=f"**Pokój:** {pokoj}\n**Rok przybycia:** {rok_przybycia}", inline=True)
    embed.add_field(name="🩺 Diagnoza", value=diagnoza, inline=False)
    embed.add_field(name="💊 Recepta", value=recepta, inline=False)
    embed.add_field(name="📋 Zalecenia", value=zalecenia, inline=False)
    embed.add_field(name="👪 Rodzice", value=imiona_rodzicow, inline=False)
    
    embed.set_footer(text=f"Karta przypisana do: {uzytkownik.name} ({uzytkownik.id})\nAktualizacja przez: {interaction.user.name}")

    await target_channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Pomyślnie utworzono/zaktualizowano kartę dla {imie_nazwisko} ({uzytkownik.mention}).", ephemeral=True)

@client.tree.command(name="karta", description="Wyświetla kartę pacjenta.")
@app_commands.describe(uzytkownik="Użytkownik, którego kartę chcesz zobaczyć.")
async def karta(interaction: discord.Interaction, uzytkownik: discord.Member):
    cards = load_patient_cards()
    user_id_str = str(uzytkownik.id)

    if user_id_str not in cards:
        await interaction.response.send_message("❌ Ten użytkownik nie posiada karty pacjenta.", ephemeral=True)
        return

    card_data = cards[user_id_str]

    embed = discord.Embed(
        title=f"Kartoteka Pacjenta",
        description=f"**Pacjent:** {card_data['imie_nazwisko']}",
        color=discord.Color.from_rgb(173, 216, 230), # Light Blue
        timestamp=datetime.fromisoformat(card_data['last_updated'])
    )
    embed.set_thumbnail(url=uzytkownik.display_avatar.url)
    embed.add_field(name="👤 Dane Podstawowe", value=f"**Wiek:** {card_data['wiek']}\n**Pochodzenie:** {card_data['pochodzenie']}", inline=True)
    embed.add_field(name="🏥 Informacje o Pobytu", value=f"**Pokój:** {card_data['pokoj']}\n**Rok przybycia:** {card_data['rok_przybycia']}", inline=True)
    embed.add_field(name="🩺 Diagnoza", value=card_data['diagnoza'], inline=False)
    embed.add_field(name="💊 Recepta", value=card_data['recepta'], inline=False)
    embed.add_field(name="📋 Zalecenia", value=card_data['zalecenia'], inline=False)
    embed.add_field(name="👪 Rodzice", value=card_data['imiona_rodzicow'], inline=False)
    
    author = interaction.guild.get_member(card_data['author_id'])
    author_name = author.name if author else "Nieznany"
    
    embed.set_footer(text=f"Karta przypisana do: {uzytkownik.name} ({uzytkownik.id})\nOstatnia aktualizacja przez: {author_name}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@karta_pacjenta.error
async def karta_pacjenta_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)



@client.tree.command(name="userinfo", description="Wyświetla szczegółowe informacje o użytkowniku.")
@app_commands.describe(uzytkownik="Użytkownik, którego informacje chcesz sprawdzić (opcjonalnie).")
async def userinfo(interaction: discord.Interaction, uzytkownik: discord.Member = None):
    target_user = uzytkownik or interaction.user
    
    # Discord Info
    embed = discord.Embed(
        title=f"Informacje o użytkowniku: {target_user.display_name}",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
    
    embed.add_field(name="ID Użytkownika", value=target_user.id, inline=False)
    embed.add_field(name="Nazwa Użytkownika", value=target_user.name, inline=True)
    embed.add_field(name="Nick na Serwerze", value=target_user.nick or "Brak", inline=True)
    
    embed.add_field(name="Konto Utworzone", value=target_user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Dołączył na Serwer", value=target_user.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    
    roles = [role.mention for role in target_user.roles if role.name != "@everyone"]
    if roles:
        embed.add_field(name="Role", value=", ".join(roles), inline=False)
    else:
        embed.add_field(name="Role", value="Brak", inline=False)

    # Economy Info
    user_economy_data = get_user_data(target_user.id)

    # Active Temporary Roles
    active_temp_roles = user_economy_data.get("active_temp_roles", [])
    if active_temp_roles:
        temp_role_names = []
        for temp_role_entry in active_temp_roles:
            role = interaction.guild.get_role(temp_role_entry["role_id"])
            if role:
                expires_at = datetime.fromisoformat(temp_role_entry["expires_at"])
                temp_role_names.append(f"{role.name} (do {expires_at.strftime('%Y-%m-%d %H:%M')})")
        if temp_role_names:
            embed.add_field(name="Aktywne Role Tymczasowe", value="\n".join(temp_role_names), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)







# --- NOWE EVENTY ---

async def get_log_channel(guild: discord.Guild):
    return discord.utils.get(guild.text_channels, name="logi")

@client.event
async def on_member_join(member: discord.Member):
    log_channel = await get_log_channel(member.guild)
    if log_channel:
        embed = discord.Embed(title="Użytkownik dołączył", description=f"{member.mention} ({member.id})", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Data dołączenia: {member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}")
        await log_channel.send(embed=embed)
    get_user_data(member.id) # Inicjalizuj dane dla nowego użytkownika

@client.event
async def on_member_remove(member: discord.Member):
    log_channel = await get_log_channel(member.guild)
    if log_channel:
        embed = discord.Embed(title="Użytkownik opuścił serwer", description=f"{member.mention} ({member.id})", color=discord.Color.red())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await log_channel.send(embed=embed)

@client.event
async def on_message_delete(message: discord.Message):
    if message.author.bot: return
    log_channel = await get_log_channel(message.guild)
    if log_channel:
        embed = discord.Embed(title="Wiadomość usunięta", description=f"**Autor:** {message.author.mention}\n**Kanał:** {message.channel.mention}", color=discord.Color.orange())
        embed.add_field(name="Treść", value=message.content if message.content else "[Brak treści - prawdopodobnie embed lub plik]", inline=False)
        await log_channel.send(embed=embed)

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or before.content == after.content: return
    log_channel = await get_log_channel(before.guild)
    if log_channel:
        embed = discord.Embed(title="Wiadomość edytowana", description=f"**Autor:** {before.author.mention}\n**Kanał:** {before.channel.mention}\n[Przejdź do wiadomości]({after.jump_url})", color=discord.Color.blue())
        embed.add_field(name="Przed edycją", value=before.content, inline=False)
        embed.add_field(name="Po edycji", value=after.content, inline=False)
        await log_channel.send(embed=embed)

@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    global verification_message_id
    if payload.message_id == verification_message_id and str(payload.emoji) == "✅":
        guild = client.get_guild(payload.guild_id)
        if not guild: return
        
        member = guild.get_member(payload.user_id)
        if not member or member.bot: return

        roles_data = load_roles()
        pacjent_role_id = roles_data.get("SECTOR_ROLE_IDS", {}).get("Pacjent")
        role = guild.get_role(pacjent_role_id) if pacjent_role_id else None

        if role and role not in member.roles:
            await member.add_roles(role, reason="Pomyślna weryfikacja")
            
            log_channel = await get_log_channel(guild)
            if log_channel:
                embed = discord.Embed(title="Użytkownik zweryfikowany", description=f"{member.mention} otrzymał rolę {role.mention}.", color=discord.Color.gold())
                await log_channel.send(embed=embed)


@setup_server.error
async def setup_server_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Nie masz uprawnień administratora, aby użyć tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił nieoczekiwany błąd: {error}", ephemeral=True)


if __name__ == "__main__":
    if not config.TOKEN:
        print("BŁĄD: Token bota nie został ustawiony w pliku config.py!")
    else:
        client.run(config.TOKEN)
