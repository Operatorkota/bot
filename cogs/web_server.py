import asyncio
import os
from discord.ext import commands, tasks
from aiohttp import web

# --- Web Server Configuration ---
WEB_SERVER_HOST = "192.168.8.151"
WEB_SERVER_PORT = 20851

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

    async def handle_frontend(self, request):
        """Obsługuje serwowanie frontendu (index.html) dla routingu SPA."""
        try:
            static_path = os.path.abspath('frontend/dist')
            return web.FileResponse(os.path.join(static_path, 'index.html'))
        except FileNotFoundError:
            return web.Response(text="Nie znaleziono pliku index.html. Czy frontend został zbudowany (`npm run build`)?", status=404)

    @tasks.loop(count=1)
    async def web_server_task(self):
        app = web.Application()
        static_path = os.path.abspath('frontend/dist')

        # API routes should be specific and come first
        app.router.add_get('/api/status', self.api_status_handler)

        # Static file serving for assets (js, css, images, etc.)
        # This needs to be specific.
        if os.path.exists(os.path.join(static_path, 'assets')):
            app.router.add_static('/assets', os.path.join(static_path, 'assets'))
        
        # Serve specific files from the root of the dist folder if they exist
        for filename in ['vite.svg', 'favicon.ico']: # Add other root files here
             if os.path.exists(os.path.join(static_path, filename)):
                app.router.add_get(f'/{filename}', lambda req, f=filename: web.FileResponse(os.path.join(static_path, f)))


        # The catch-all handler for SPA routing.
        # This serves index.html for any path that wasn't matched above.
        app.router.add_get('/{path:.*}', self.handle_frontend)

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