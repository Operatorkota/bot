import asyncio
import os
import json # Added for loading JSON files
from discord.ext import commands, tasks
from aiohttp import web
import aiohttp_cors # Import cors library

# --- Web Server Configuration ---
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 20851

# --- File Paths (Copied from main.py for web server's direct access) ---
PATIENT_CARDS_FILE = 'patient_cards.json'
USER_DATA_FILE = 'user_data.json'

# --- Data Loading Functions (Copied from main.py for web server's direct access) ---
def load_patient_cards():
    """Wczytuje dane kart pacjentów z pliku JSON."""
    if not os.path.exists(PATIENT_CARDS_FILE):
        return {}
    try:
        with open(PATIENT_CARDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def load_user_data():
    """Wczytuje dane użytkowników z pliku JSON."""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f: # Ensure utf-8 for consistency
            return json.load(f)
    except json.JSONDecodeError:
        return {}

# --- Logging Middleware ---
@web.middleware
async def logging_middleware(request, handler):
    """Middleware to log every incoming request."""
    print(f"INFO: [WEB] Otrzymano żądanie: {request.method} {request.path} od {request.remote}")
    print(f"INFO: [WEB] Nagłówki: {request.headers}")
    try:
        response = await handler(request)
        print(f"INFO: [WEB] Odpowiedź: Status {response.status}")
        return response
    except Exception as e:
        print(f"BŁĄD: [WEB] Błąd podczas obsługi żądania {request.path}: {e}")
        # Re-raise the exception to be handled by aiohttp's default error handling
        raise

class WebServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server_task.start()

    def cog_unload(self):
        self.web_server_task.cancel()

    async def api_status_handler(self, request):
        """Zwraca podstawowe statystyki bota w formacie JSON."""
        status_data = {
            "bot_status": "online",
            "latency": f"{self.bot.latency * 1000:.2f} ms",
            "guild_count": len(self.bot.guilds)
        }
        return web.json_response(status_data)

    async def api_patient_cards_handler(self, request):
        """Zwraca wszystkie karty pacjentów w formacie JSON."""
        cards = load_patient_cards()
        return web.json_response(cards)

    async def api_user_data_handler(self, request):
        """Zwraca dane użytkowników w formacie JSON."""
        user_data = load_user_data()
        return web.json_response(user_data)

    async def handle_frontend(self, request):
        """Obsługuje serwowanie frontendu (index.html) dla routingu SPA."""
        try:
            static_path = os.path.abspath('frontend/dist')
            return web.FileResponse(os.path.join(static_path, 'index.html'))
        except FileNotFoundError:
            return web.Response(text="Nie znaleziono pliku index.html. Czy frontend został zbudowany (`npm run build`)?", status=404)

    @tasks.loop(count=1)
    async def web_server_task(self):
        # Add the logging middleware to the app
        app = web.Application(middlewares=[logging_middleware])
        static_path = os.path.abspath('frontend/dist')

        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
        })

        # API routes should be specific and come first
        api_status_route = app.router.add_get('/api/status', self.api_status_handler)
        api_patient_cards_route = app.router.add_get('/api/patient_cards', self.api_patient_cards_handler)
        api_user_data_route = app.router.add_get('/api/user_data', self.api_user_data_handler)

        # Add CORS to API routes
        cors.add(api_status_route)
        cors.add(api_patient_cards_route)
        cors.add(api_user_data_route)

        # Static file serving for assets (js, css, images, etc.)
        if os.path.exists(os.path.join(static_path, 'assets')):
            app.router.add_static('/assets', os.path.join(static_path, 'assets'))
        
        # Serve specific files from the root of the dist folder if they exist
        for filename in ['vite.svg', 'favicon.ico']: # Add other root files here
             if os.path.exists(os.path.join(static_path, filename)):
                # This lambda captures the filename for the closure
                file_handler = lambda req, f=filename: web.FileResponse(os.path.join(static_path, f))
                app.router.add_get(f'/{filename}', file_handler)

        # The catch-all handler for SPA routing.
        # This serves index.html for any path that wasn't matched above.
        frontend_route = app.router.add_get('/{path:.*}', self.handle_frontend)
        cors.add(frontend_route) # Also add CORS to the frontend route

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEB_SERVER_HOST, WEB_SERVER_PORT)
        
        try:
            await site.start()
            print(f"INFO: Serwer webowy uruchomiony na http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
        except Exception as e:
            print(f"BŁĄD: Nie udało się uruchomić serwera webowego: {e}")
            return

        # Wait until the cog is unloaded
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            await runner.cleanup()
            print("INFO: Serwer webowy został zatrzymany.")

    @web_server_task.before_loop
    async def before_web_server_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(WebServerCog(bot))
