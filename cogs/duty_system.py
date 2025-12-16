# cogs/duty_system.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import os
import json
import re

from data_manager import DataManager
import config

class PayrollApprovalView(discord.ui.View):
    def __init__(self, duty_data: DataManager, payroll_drafts: DataManager, payroll_history: DataManager):
        super().__init__(timeout=None)
        self.duty_data = duty_data
        self.payroll_drafts = payroll_drafts
        self.payroll_history = payroll_history

    @discord.ui.button(label="Zatwierdź", style=discord.ButtonStyle.green, custom_id="payroll_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        draft_id_str = interaction.message.embeds[0].description
        draft_id_match = re.search(r"`(draft_\d+)`", draft_id_str)
        if not draft_id_match:
            await interaction.response.send_message("Nie można znaleźć ID projektu w wiadomości.", ephemeral=True)
            return
        
        draft_id = draft_id_match.group(1)
        
        is_admin = any(role.id in config.ADMIN_ROLE_IDS for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("Nie masz uprawnień do zatwierdzania wypłat.", ephemeral=True)
            return

        draft = self.payroll_drafts.get(draft_id)
        if not draft:
            await interaction.response.send_message("Nie znaleziono tego projektu wypłat.", ephemeral=True)
            return

        if interaction.user.id in draft["approved_by"]:
            await interaction.response.send_message("Już zatwierdziłeś ten projekt.", ephemeral=True)
            return

        draft["approved_by"].append(interaction.user.id)

        if len(draft["approved_by"]) >= 2:
            self.payroll_history.set(draft_id, draft)
            self.payroll_drafts.set(draft_id, None) 

            all_users_data = self.duty_data.get_all()
            for user_id_str in all_users_data.keys():
                user_data = all_users_data[user_id_str]
                user_data["total_duty_time"] = 0
                user_data["interventions"] = 0
                user_data["warnings"] = 0
                user_data["last_payroll_date"] = datetime.datetime.now().isoformat()
            self.duty_data.update_all(all_users_data)
            
            await interaction.response.send_message(f"Projekt wypłat `{draft_id}` został zatwierdzony i sfinalizowany.", ephemeral=False)
            await interaction.message.edit(content=f"Projekt wypłat `{draft_id}` został sfinalizowany.", view=None)
        else:
            self.payroll_drafts.set(draft_id, draft)
            await interaction.response.send_message(f"Zatwierdziłeś projekt wypłat `{draft_id}`. Potrzebna jest jeszcze jedna aprobata.", ephemeral=False)

    @discord.ui.button(label="Odrzuć", style=discord.ButtonStyle.red, custom_id="payroll_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        draft_id_str = interaction.message.embeds[0].description
        draft_id_match = re.search(r"`(draft_\d+)`", draft_id_str)
        if not draft_id_match:
            await interaction.response.send_message("Nie można znaleźć ID projektu w wiadomości.", ephemeral=True)
            return

        draft_id = draft_id_match.group(1)

        is_admin = any(role.id in config.ADMIN_ROLE_IDS for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("Nie masz uprawnień do zatwierdzania wypłat.", ephemeral=True)
            return
            
        self.payroll_drafts.set(draft_id, None)
        await interaction.response.send_message(f"Odrzuciłeś projekt wypłat `{draft_id}`. Został on usunięty.", ephemeral=False)
        await interaction.message.edit(content=f"Projekt wypłat `{draft_id}` został odrzucony.", view=None)

class DutySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.duty_data = DataManager('duty_data.json')
        self.payroll_drafts = DataManager('payroll_drafts.json')
        self.payroll_history = DataManager('payroll_history.json')
        self.active_duty_sessions = self.load_active_sessions()
        self.payroll_generation_task.start()
        self.time_update_loop.start()

    def cog_unload(self):
        self.save_active_sessions()
        self.payroll_generation_task.cancel()
        self.time_update_loop.cancel()

    def load_active_sessions(self):
        """Loads active sessions from a file to persist across restarts."""
        try:
            with open('active_duty_sessions.json', 'r') as f:
                return {int(k): v for k, v in json.load(f).items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_active_sessions(self):
        """Saves active sessions to a file."""
        with open('active_duty_sessions.json', 'w') as f:
            json.dump(self.active_duty_sessions, f)

    def get_user_duty_data(self, user_id):
        user_data = self.duty_data.get(user_id)
        if user_data is None:
            user_data = {
                "total_duty_time": 0,
                "interventions": 0,
                "warnings": 0,
                "on_vacation": False,
                "vacation_start": None,
                "last_payroll_date": datetime.datetime.now().isoformat()
            }
            self.duty_data.set(user_id, user_data)
        return user_data

    async def start_duty(self, user: discord.Member):
        if user.id in self.active_duty_sessions:
            return "Już jesteś na służbie."

        if user.voice and user.voice.channel and user.voice.channel.id in config.DUTY_VOICE_CHANNEL_IDS:
            self.active_duty_sessions[user.id] = {
                "start_time": datetime.datetime.now().isoformat(),
                "last_update": datetime.datetime.now().isoformat(),
                "in_voice": True
            }
            self.save_active_sessions()
            
            duty_role = discord.utils.get(user.guild.roles, name=config.DUTY_ROLE_NAME)
            if duty_role:
                await user.add_roles(duty_role, reason="Rozpoczęcie służby")

            return "Rozpocząłeś służbę. Twój czas jest teraz liczony."
        else:
            return "Musisz być na jednym z wyznaczonych kanałów głosowych, aby rozpocząć służbę."

    async def end_duty(self, user: discord.Member):
        if user.id not in self.active_duty_sessions:
            return "Nie jesteś na służbie."

        session = self.active_duty_sessions.pop(user.id)
        start_time = datetime.datetime.fromisoformat(session["start_time"])
        duration = datetime.datetime.now() - start_time
        
        user_data = self.get_user_duty_data(user.id)
        user_data["total_duty_time"] += duration.total_seconds()
        self.duty_data.set(user.id, user_data)
        self.save_active_sessions()
        
        duty_role = discord.utils.get(user.guild.roles, name=config.DUTY_ROLE_NAME)
        if duty_role:
            await user.remove_roles(duty_role, reason="Zakończenie służby")

        return f"Zakończyłeś służbę. Twój czas na służbie w tej sesji: {str(duration).split('.')[0]}"

    @app_commands.command(name="on-duty", description="Rozpoczyna służbę.")
    async def on_duty(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await self.start_duty(interaction.user)
        await interaction.followup.send(message)

    @app_commands.command(name="off-duty", description="Kończy służbę.")
    async def off_duty(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await self.end_duty(interaction.user)
        await interaction.followup.send(message)

    @app_commands.command(name="duty-info", description="Wyświetla informacje o twojej służbie.")
    async def duty_info(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        user_data = self.get_user_duty_data(user_id)
        
        total_time_seconds = user_data["total_duty_time"]
        
        if user_id in self.active_duty_sessions and self.active_duty_sessions[user_id]["in_voice"]:
            last_update = datetime.datetime.fromisoformat(self.active_duty_sessions[user_id]["last_update"])
            total_time_seconds += (datetime.datetime.now() - last_update).total_seconds()

        embed = discord.Embed(title="Informacje o służbie", color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
        
        status = "Na służbie" if user_id in self.active_duty_sessions else "Poza służbą"
        embed.add_field(name="Status", value=status, inline=False)

        duty_time_str = str(datetime.timedelta(seconds=int(total_time_seconds)))
        embed.add_field(name="Całkowity czas służby", value=duty_time_str, inline=False)
        embed.add_field(name="Interwencje w tym okresie", value=user_data.get("interventions", 0), inline=False)
        embed.add_field(name="Ostrzeżenia w tym okresie", value=user_data.get("warnings", 0), inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="duty_sentenced", description="Rejestruje interwencję (kara).")
    @app_commands.describe(uzytkownik="Ukarany użytkownik", powod="Powód kary")
    async def duty_sentenced(self, interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
        await interaction.response.defer(ephemeral=True)
        moderator_id = interaction.user.id

        if moderator_id not in self.active_duty_sessions:
            await interaction.followup.send("Musisz być na służbie, aby używać tej komendy.", ephemeral=True)
            return

        user_data = self.get_user_duty_data(moderator_id)
        user_data["interventions"] = user_data.get("interventions", 0) + 1
        self.duty_data.set(moderator_id, user_data)
        
        await interaction.followup.send(f"Zarejestrowano interwencję dla {uzytkownik.mention}. Powód: {powod}. Masz teraz {user_data['interventions']} interwencji.", ephemeral=True)
    
    @app_commands.command(name="duty_warn", description="Rejestruje ostrzeżenie dla użytkownika.")
    @app_commands.describe(uzytkownik="Użytkownik otrzymujący ostrzeżenie", powod="Powód ostrzeżenia")
    async def duty_warn(self, interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
        await interaction.response.defer(ephemeral=True)
        moderator_id = interaction.user.id

        if moderator_id not in self.active_duty_sessions:
            await interaction.followup.send("Musisz być na służbie, aby używać tej komendy.", ephemeral=True)
            return

        user_data = self.get_user_duty_data(moderator_id)
        user_data["warnings"] = user_data.get("warnings", 0) + 1
        self.duty_data.set(moderator_id, user_data)

        await interaction.followup.send(f"Zarejestrowano ostrzeżenie dla {uzytkownik.mention}. Powód: {powod}. Masz teraz {user_data['warnings']} ostrzeżeń.", ephemeral=True)

    @app_commands.command(name="urlop-start", description="Rozpoczyna urlop.")
    async def urlop_start(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        user_data = self.get_user_duty_data(user_id)

        if user_data.get("on_vacation", False):
            await interaction.followup.send("Już jesteś na urlopie.", ephemeral=True)
            return

        user_data["on_vacation"] = True
        user_data["vacation_start"] = datetime.datetime.now().isoformat()
        self.duty_data.set(user_id, user_data)

        if user_id in self.active_duty_sessions:
            await self.end_duty(interaction.user)

        await interaction.followup.send("Rozpocząłeś urlop. Wymagania dotyczące aktywności są zawieszone.", ephemeral=True)

    @app_commands.command(name="urlop-end", description="Kończy urlop.")
    async def urlop_end(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        user_data = self.get_user_duty_data(user_id)

        if not user_data.get("on_vacation", False):
            await interaction.followup.send("Nie jesteś na urlopie.", ephemeral=True)
            return

        user_data["on_vacation"] = False
        user_data["vacation_start"] = None
        self.duty_data.set(user_id, user_data)
        await interaction.followup.send("Zakończyłeś urlop.", ephemeral=True)

    @app_commands.command(name="ranking", description="Wyświetla rankingi służby.")
    async def ranking(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        all_users_data = self.duty_data.get_all()
        guild = interaction.guild

        sorted_by_time = sorted(all_users_data.items(), key=lambda item: item[1].get('total_duty_time', 0), reverse=True)
        
        sorted_by_interventions = sorted(all_users_data.items(), key=lambda item: item[1].get('interventions', 0), reverse=True)

        embed = discord.Embed(title="🏆 Ranking Służby 🏆", color=discord.Color.gold())

        time_leaderboard = []
        for i, (user_id, data) in enumerate(sorted_by_time[:5]):
            member = guild.get_member(int(user_id))
            if member:
                time_seconds = data.get('total_duty_time', 0)
                time_str = str(datetime.timedelta(seconds=int(time_seconds)))
                time_leaderboard.append(f"{i+1}. {member.mention} - {time_str}")
        
        if time_leaderboard:
            embed.add_field(name="Najwięcej godzin", value="\n".join(time_leaderboard), inline=False)

        interventions_leaderboard = []
        for i, (user_id, data) in enumerate(sorted_by_interventions[:5]):
            member = guild.get_member(int(user_id))
            if member:
                interventions = data.get('interventions', 0)
                interventions_leaderboard.append(f"{i+1}. {member.mention} - {interventions} interwencji")

        if interventions_leaderboard:
            embed.add_field(name="Najwięcej interwencji", value="\n".join(interventions_leaderboard), inline=False)

        if not time_leaderboard and not interventions_leaderboard:
            embed.description = "Brak danych do wyświetlenia w rankingu."

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="duty-bonus", description="Dodaj bonus do wypłaty użytkownika.")
    @app_commands.describe(uzytkownik="Użytkownik, któremu chcesz dodać bonus", kwota="Kwota bonusu", powod="Powód bonusu")
    async def duty_bonus(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: float, powod: str):
        is_admin = any(role.id in config.ADMIN_ROLE_IDS for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("Nie masz uprawnień do dodawania bonusów.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        user_data = self.get_user_duty_data(uzytkownik.id)
        bonuses = user_data.get("bonuses", [])
        bonuses.append({"amount": kwota, "reason": powod})
        user_data["bonuses"] = bonuses
        self.duty_data.set(uzytkownik.id, user_data)
        await interaction.followup.send(f"Dodano bonus w wysokości {kwota} PLN dla {uzytkownik.mention}.", ephemeral=True)

    @app_commands.command(name="duty-deduction", description="Dodaj potrącenie do wypłaty użytkownika.")
    @app_commands.describe(uzytkownik="Użytkownik, któremu chcesz dodać potrącenie", kwota="Kwota potrącenia", powod="Powód potrącenia")
    async def duty_deduction(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: float, powod: str):
        is_admin = any(role.id in config.ADMIN_ROLE_IDS for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("Nie masz uprawnień do dodawania potrąceń.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        user_data = self.get_user_duty_data(uzytkownik.id)
        deductions = user_data.get("deductions", [])
        deductions.append({"amount": kwota, "reason": powod})
        user_data["deductions"] = deductions
        self.duty_data.set(uzytkownik.id, user_data)
        await interaction.followup.send(f"Dodano potrącenie w wysokości {kwota} PLN dla {uzytkownik.mention}.", ephemeral=True)


    @commands.Cog.listener() # This listener is duplicated, remove one
    async def on_voice_state_update(self, member, before, after):
        if member.id not in self.active_duty_sessions:
            return

        session = self.active_duty_sessions[member.id]
        now = datetime.datetime.now()
        last_update = datetime.datetime.fromisoformat(session["last_update"])

        if session["in_voice"]:
            duration = now - last_update
            user_data = self.get_user_duty_data(member.id)
            user_data["total_duty_time"] += duration.total_seconds()
            self.duty_data.set(member.id, user_data)

        if after.channel and after.channel.id in config.DUTY_VOICE_CHANNEL_IDS:
            session["in_voice"] = True
        else:
            session["in_voice"] = False
        
        session["last_update"] = now.isoformat()
        self.active_duty_sessions[member.id] = session
        self.save_active_sessions()

    @tasks.loop(minutes=1)
    async def time_update_loop(self):
        """Periodically updates duty time for users in voice channels."""
        now = datetime.datetime.now()
        for user_id, session in list(self.active_duty_sessions.items()):
            if session["in_voice"]:
                last_update = datetime.datetime.fromisoformat(session["last_update"])
                duration = now - last_update
                
                user_data = self.get_user_duty_data(user_id)
                user_data["total_duty_time"] += duration.total_seconds()
                self.duty_data.set(user_id, user_data)
                
                session["last_update"] = now.isoformat()
                self.active_duty_sessions[user_id] = session
        self.save_active_sessions()

    @time_update_loop.before_loop
    async def before_time_update_loop(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(days=config.PAYROLL_PERIOD_DAYS)
    async def payroll_generation_task(self):
        print("Generating payroll...")
        draft_reports = []
        all_users_data = self.duty_data.get_all()
        guild = self.bot.get_guild(self.bot.guilds[0].id)

        for user_id_str, user_data in all_users_data.items():
            user_id = int(user_id_str)
            
            if user_data.get("on_vacation", False):
                continue

            total_time_hours = user_data.get("total_duty_time", 0) / 3600
            interventions = user_data.get("interventions", 0)
            
            base_pay = 0
            position = "Brak"
            rate = 0
            if total_time_hours >= config.MIN_DUTY_HOURS_FOR_PAYOUT and interventions >= config.MIN_INTERVENTIONS_FOR_PAYOUT:
                member = guild.get_member(user_id)
                if not member:
                    continue

                for role in member.roles:
                    if role.name in config.ROLE_RATES:
                        if config.ROLE_RATES[role.name] > rate:
                            rate = config.ROLE_RATES[role.name]
                            position = role.name
                
                base_pay = total_time_hours * rate

            bonuses_total = sum(b['amount'] for b in user_data.get("bonuses", []))
            deductions_total = sum(d['amount'] for d in user_data.get("deductions", []))
            final_amount = base_pay + bonuses_total - deductions_total

            suspicious = total_time_hours > 10 and interventions == 0

            report = {
                "user_id": user_id,
                "position": position,
                "duty_time_hours": round(total_time_hours, 2),
                "interventions": interventions,
                "warnings": user_data.get("warnings", 0),
                "base_pay": round(base_pay, 2),
                "bonuses": round(bonuses_total, 2),
                "deductions": round(deductions_total, 2),
                "final_amount": round(final_amount, 2),
                "suspicious": suspicious
            }
            draft_reports.append(report)

        if draft_reports:
            draft_id = f"draft_{int(datetime.datetime.now().timestamp())}"
            self.payroll_drafts.set(draft_id, {"reports": draft_reports, "approved_by": []})
            
            drafts_channel = self.bot.get_channel(config.PAYROLL_DRAFTS_CHANNEL_ID)
            if drafts_channel:
                embed = discord.Embed(title=f"Projekt Wypłat - {datetime.date.today()}", description=f"ID projektu: `{draft_id}`\nProszę o zatwierdzenie przez dwóch administratorów.", color=discord.Color.gold())
                
                for report in draft_reports:
                    member = guild.get_member(report["user_id"])
                    suspicious_text = "⚠️ **PODEJRZANA AKTYWNOŚĆ**" if report["suspicious"] else ""
                    embed.add_field(
                        name=f"Wypłata dla {member.display_name if member else 'Nieznany Użytkownik'}",
                        value=f"**Stanowisko:** {report['position']}\n"
                              f"**Czas służby:** {report['duty_time_hours']}h\n"
                              f"**Kwota końcowa:** {report['final_amount']} PLN\n"
                              f"{suspicious_text}",
                        inline=False
                    )

                view = PayrollApprovalView(self.duty_data, self.payroll_drafts, self.payroll_history)
                await drafts_channel.send(embed=embed, view=view)

    @payroll_generation_task.before_loop
    async def before_payroll_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    cog = DutySystem(bot)
    await bot.add_cog(cog)
    bot.add_view(PayrollApprovalView(cog.duty_data, cog.payroll_drafts, cog.payroll_history))
    print("DutySystem Cog loaded.")