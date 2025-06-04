import sqlite3
import logging
from config.logging_config import setup_logging
import time
import re
import os
from dotenv import load_dotenv

load_dotenv()

logger = setup_logging()

class DatabaseClassement:
    def __init__(self):
        """Initialise la connexion à la base de données de classement"""
        self.db_path = 'discord.db'
        self.game_db_path = os.getenv('FTP_GAME_DB', 'ConanSandbox/Saved/game.db')  # Base de données du jeu
        self._initialize_db()
        self.valid_players_cache = {}  # Cache des joueurs valides
        self.last_cache_update = 0
        self.cache_duration = 300  # 5 minutes
        logger.info(f"DatabaseClassement initialisé avec game_db_path: {self.game_db_path}")

    def _initialize_db(self):
        """Initialise la table de classement si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS classement (
                player_id TEXT PRIMARY KEY,
                player_name TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                last_kill TIMESTAMP,
                last_death TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def check_death_in_logs(self, log_content):
        """Vérifie les logs pour détecter les morts et mettre à jour le classement"""
        try:
            # Filtrer les lignes contenant la mort
            death_lines = [line for line in log_content.splitlines() 
                         if '[FunCombat_PlayerController_C_10 DeathCameraActor_C_10]' in line]
            
            for line in death_lines:
                # Extraire le Character ID
                match = re.search(r'Character ID (\d+) has name ([^\s]+)', line)
                if match:
                    character_id = match.group(1)
                    victim_name = match.group(2)
                    
                    # Vérifier dans la table characters
                    conn = sqlite3.connect(self.game_db_path)
                    c = conn.cursor()
                    c.execute('''
                        SELECT killerName 
                        FROM characters 
                        WHERE id = ? AND isAlive = 0
                    ''', (character_id,))
                    
                    result = c.fetchone()
                    if result and result[0]:  # Si on a un tueur
                        killer_name = result[0]
                        logger.info(f"Kill détecté: {killer_name} a tué {victim_name}")
                        
                        # Mettre à jour le classement
                        self.update_kill_stats(
                            killer_id=character_id,  # On utilise le même ID pour l'instant
                            killer_name=killer_name,
                            victim_id=character_id,
                            victim_name=victim_name
                        )
                    
                    conn.close()
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des morts: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def is_valid_player(self, player_name: str) -> bool:
        """Vérifie si le nom du joueur existe dans la table characters du jeu"""
        # Vérifier le cache d'abord
        current_time = time.time()
        if current_time - self.last_cache_update > self.cache_duration:
            self.valid_players_cache.clear()
            self.last_cache_update = current_time

        if player_name in self.valid_players_cache:
            return self.valid_players_cache[player_name]

        try:
            conn = sqlite3.connect(self.game_db_path)
            c = conn.cursor()
            c.execute('''
                SELECT COUNT(*) 
                FROM characters 
                WHERE char_name = ?
            ''', (player_name,))
            count = c.fetchone()[0]
            is_valid = count > 0
            self.valid_players_cache[player_name] = is_valid
            return is_valid
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du joueur {player_name}: {e}")
            # En cas d'erreur, on considère le joueur comme valide pour ne pas bloquer le système
            return True
        finally:
            conn.close()

    def update_kill_stats(self, killer_id: str, killer_name: str, victim_id: str, victim_name: str, is_kill: bool = True):
        """Met à jour les statistiques de kills dans la base de données"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            if is_kill:
                # Mise à jour du tueur
                c.execute('''
                    INSERT INTO classement (player_id, player_name, kills, last_kill)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        kills = kills + 1,
                        last_kill = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (killer_id, killer_name))
                
                # Mise à jour de la victime
                c.execute('''
                    INSERT INTO classement (player_id, player_name, deaths, last_death)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        deaths = deaths + 1,
                        last_death = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (victim_id, victim_name))
            else:
                # Mise à jour de la victime uniquement
                c.execute('''
                    INSERT INTO classement (player_id, player_name, deaths, last_death)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        deaths = deaths + 1,
                        last_death = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (victim_id, victim_name))
            
            conn.commit()
            logger.info(f"Stats mises à jour pour {killer_name} et {victim_name}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_kill_stats(self):
        """Récupère les statistiques de kills triées par nombre de kills"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # On récupère les stats de la base de données Discord
            c.execute('''
                SELECT player_name, kills
                FROM classement
                ORDER BY kills DESC
                LIMIT 30
            ''')
            
            stats = c.fetchall()
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return []
        finally:
            conn.close()
