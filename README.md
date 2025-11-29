# Discord Server Builder Bot

Ten bot Discord pozwala na automatyczne skonfigurowanie serwera poprzez stworzenie predefiniowanych kategorii, kanałów tekstowych i głosowych, a także wysłanie regulaminu w formie embeda.

## Konfiguracja Bota na Discord Developer Portal

1.  **Utwórz Aplikację:**
    *   Przejdź na stronę [Discord Developer Portal](https://discord.com/developers/applications).
    *   Zaloguj się i kliknij "New Application". Nadaj jej nazwę.

2.  **Dodaj Bota:**
    *   W menu po lewej stronie wybierz zakładkę "Bot".
    *   Kliknij "Add Bot" i potwierdź.
    *   **Ważne:** Pod sekcją "Privileged Gateway Intents" włącz **WSZYSTKIE** opcje (szczególnie "SERVER MEMBERS INTENT" i "MESSAGE CONTENT INTENT").

3.  **Skopiuj Token:**
    *   Pod sekcją "Build-A-Bot" znajdziesz przycisk "Reset Token". Kliknij go, a następnie skopiuj wyświetlony token.
    *   **Token został już wklejony do pliku `config.py` przez Gemini CLI.**

4.  **Uprawnienia Bota:**
    *   W zakładce "OAuth2" -> "URL Generator" wybierz zakresy (Scopes): `bot` i `applications.commands`.
    *   W sekcji "Bot Permissions" wybierz następujące uprawnienia:
        *   `Administrator` (najprostsze, ale daje botowi pełną kontrolę)
        *   Alternatywnie, jeśli chcesz ograniczyć uprawnienia: `Manage Channels`, `Manage Roles`, `Send Messages`, `Embed Links`.
    *   Skopiuj wygenerowany URL i wklej go do przeglądarki, aby zaprosić bota na swój serwer.

## Instalacja

1.  **Przejdź do katalogu projektu:**
    ```bash
    cd C:\Users\User\discord_server_builder
    ```

2.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

## Uruchamianie Bota

1.  **Uruchom bota:**
    ```bash
    python main.py
    ```
    Bot powinien się zalogować i wyświetlić komunikat `Zalogowano jako <nazwa_bota>! Bot jest gotowy do działania.`.

## Użycie

1.  **Na serwerze Discord:**
    *   Upewnij się, że bot jest online i ma odpowiednie uprawnienia na serwerze.
    *   W dowolnym kanale tekstowym wpisz komendę slash: `/setup`
    *   Naciśnij Enter. Bot rozpocznie tworzenie kategorii i kanałów, a następnie wyśle regulamin na kanale `#regulamin`.

## Edycja Struktury Serwera i Regulaminu

Możesz łatwo edytować strukturę serwera i treść regulaminu, modyfikując zmienne `SERVER_STRUCTURE`, `RULES_TITLE` i `RULES_DESCRIPTION` w pliku `main.py`.
