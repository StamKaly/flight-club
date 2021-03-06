from . import commands, players
from os.path import getsize, join, isfile
from os import remove
import json
import time


def teamno_to_team_colour(team_number):
    colours = [2, 'spec',
               3, 'red',
               4, 'blue',
               5, 'green',
               6, 'yellow',
               7, 'orange',
               8, 'purple',
               9, 'azure',
               10, 'pink',
               11, 'brown']
    for number in colours:
        if team_number == number:
            return colours[colours.index(number) + 1]


class AltitudeMod:
    def __init__(self, port, altitude_path, modded=False, lobby=None):
        self.log_file = join(altitude_path, 'servers', 'log.txt')
        self.old_log_file = join(altitude_path, 'servers', 'log_old.txt')
        self.archive_log_file = join(altitude_path, 'servers', 'log_archive.txt')
        self.players = players.Players(self, modded, lobby)
        self.commands = commands.Commands(self.players, port, join(altitude_path, 'servers', 'command.txt'))
        self.players.get_commands_object(self.commands)
        self.current_line = 0

        self.admins = ["5640761e-f165-4f40-b3d6-3e3167dd767d",  # duck
                       "f4d0b170-2877-4a92-90eb-eb950a57c636",  # stam
                       "c9e24c41-292d-4d40-b76c-230d8f30ef32",  # stam2
                       "faa8061c-5cd6-43bb-b389-561be0792b33",  # kafka
                       "55dd4345-53e2-4a5d-b6e1-7ca357c7337d",  # label
                       "7c29079d-5ead-4136-8b1d-467513350b79",  # demv
                       "b61aa791-7cc3-44bf-bba0-1c7faa9009a9",  # toma
                       "31456ecc-b5f2-4615-88b4-c4aeadcbf0a7",  # golden
                       "bf60335d-784f-4f31-98f8-3e0bb591b8c2",  # moxy
                       "8612de03-f66c-4281-9d7b-8b751837a3c6",  # jonus
                       "2f2101b2-bfda-4f95-8f6d-a590992d8108",  # max
                       "92f40cad-d09f-48b4-b165-5d3c3d97f26c",  # brutal
                       "02a33655-b2eb-42c2-bc88-fff24240f0d8",  # phyx
                       "0aa6b54c-52b4-4fa7-b2b4-0dc0c8350dd0",  # paiza
                       "d2ade87e-09a6-4ff9-af7b-9ae9f58fd570",  # elusive
                       "5ec76fe2-7074-4926-8873-a0e2bf2d9ba5",  # dmcm
                       "ba9e19db-2cec-4c01-b984-14ca9313f9ff",  # rawr
                       "0d754ee7-0a53-4bbf-bb9f-1c7e88ca0ee9",  # tolis
                       "25c28e39-8c93-4adb-91c0-783cb9d75959",  # nick
                       "a9d97c25-09a5-432f-b221-7e3162296424"  # lewish
                       ]

        self.teams = [[], []]
        self.mode = "free"
        self.map_team_colours = ["red", "blue"]
        self.onelh = False

    def parse(self, decoded):
        try:
            event = decoded['type']
            if event == "chat":
                self.on_chat(self.players.player_from_player_id(decoded['player']),
                             *[decoded[argument] for argument in ['message', 'server', 'team']])
            elif event == "mapChange":
                self.players._on_map_change(decoded['map'])
                self.on_server_map_change(decoded['map'], decoded['mode'],
                                          *[teamno_to_team_colour(decoded['{}Team'.format(team)])
                                            for team in ['right', 'left']])
            elif event == "logPlanePositions":
                position_by_player = []
                for player in decoded['positionByPlayer']:
                    position_by_player.append([self.players.player_from_player_id(player),
                                               tuple(decoded['positionByPlayer'][player].split(','))])
                self.on_log_plane_positions(position_by_player)
            elif event == "goal":
                scorer = self.players.player_from_player_id(decoded['player'])
                assister = None if decoded['assister'] < 0 else \
                    self.players.player_from_player_id(decoded['assister'])
                secondary_assister = None if decoded['secondaryAssister'] < 0 else \
                    self.players.player_from_player_id(decoded['secondaryAssister'])
                self.on_goal(scorer, assister, secondary_assister, decoded['xp'])
            elif event == "structureDestroy":
                self.on_structure_destroy(self.players.player_from_player_id(decoded['player']), decoded['target'],
                                          decoded['xp'])
            elif event == "kill":
                kill_type = "crash" if decoded['source'] == "plane" and decoded['player'] == -1 else "turret_kill" \
                    if decoded['source'] == "turret" else "plane_kill"
                killer = self.players.player_from_player_id(decoded['player']) if kill_type == "plane_kill" else None
                self.on_kill(kill_type, killer, self.players.player_from_player_id(decoded['victim']),
                             decoded['multi'], decoded['streak'])
            elif event == "roundEnd":
                # TODO: parse everything given
                # {"port":27279,"participantStatsByName":{"Crashes":[1,2,0],"Kills":[3,1,0],"Longest Life":[216,158,0],
                # "Ball Possession Time":[0,0,0],"Goals Scored":[0,0,0],"Damage Received":[700,1120,0],
                # "Assists":[0,0,0],"Experience":[75,25,0],"Damage Dealt":[340,510,0],"Goals Assisted":[0,0,0],
                # "Damage Dealt to Enemy Buildings":[0,0,0],"Deaths":[2,5,0],"Multikill":[0,0,0],"Kill Streak":[2,1,0]},
                # "winnerByAward":{"Most Helpful":0,"Best Kill Streak":0,"Longest Life":0,"Most Deadly":0,
                # "Best Multikill":0},"time":441083559,"type":"roundEnd","participants":[0,1,2]}
                self.on_round_end()
            elif event == "consoleCommandExecute":
                if decoded['source'] != "00000000-0000-0000-0000-000000000000":
                    self.on_command(self.players.player_from_vapor_id(decoded['source']),
                                    *[decoded[argument] for argument in ['command', 'arguments', 'group']])
            elif event == "clientAdd":
                self.players.add(*[decoded[argument] for argument in ['nickname', 'vaporId', 'player']],
                                 decoded['ip'].split(":")[0])
                self.on_client_add(self.players.player_from_player_id(decoded['player']))
            elif event == "logServerStatus":
                self.players.get_all_players(*[decoded[argument] for argument in ['nicknames', 'vaporIds',
                                                                                  'playerIds']],
                                             [ip.split(':')[0] for ip in decoded['ips']])
            elif event == "clientRemove":
                self.players.remove(decoded['nickname'])
                self.on_client_remove(decoded['nickname'], decoded['vaporId'], decoded['ip'].split(':')[0],
                                      decoded['reason'])
            elif event == "clientNicknameChange":
                self.players.nickname_change(decoded['oldNickname'], decoded['newNickname'])
                self.on_nickname_change(decoded['oldNickname'],
                                        self.players.player_from_nickname(decoded['newNickname']))
            elif event == "playerInfoEv":
                if not decoded['leaving']:
                    self.players._on_player_info_ev(decoded['player'])
            elif event == "spawn":
                self.on_spawn(self.players.player_from_player_id(decoded['player']),
                              *[decoded[argument] for argument in ['plane', 'perkRed', 'perkGreen',
                                                                   'perkBlue', 'skin']],
                              teamno_to_team_colour(decoded['team']))
        except KeyError:
            print('Could not handle line "{}"'.format(decoded))

    def archive_log(self):
        with open(self.log_file) as log:
            with open(self.archive_log_file, "a") as archive:
                archive.write(log.read())
        with open(self.log_file, "w"):
            pass

    def _run_on_every_loop(self):
        pass

    def run(self):
        if getsize(self.log_file) != 0:
            self.archive_log()
        self.commands.log_server_status()
        while True:
            with open(self.log_file) as log:
                for line in log.readlines()[self.current_line:]:
                    if 'port' in line:
                        try:
                            self.parse(json.loads(line))
                        except json.decoder.JSONDecodeError:
                            print("JSON error -- could not parse line {}".format(line))
                        finally:
                            self.current_line += 1
                            if isfile(self.old_log_file):
                                self.current_line = 0
                                with open(self.old_log_file) as old_log_file:
                                    with open(self.archive_log_file, "a") as archive:
                                        archive.writelines(old_log_file.readlines())
                                remove(self.old_log_file)
            self._run_on_every_loop()
            time.sleep(0.01)

    def on_chat(self, player, message, server_message, team_message):
        pass

    def on_server_map_change(self, map_name, mode, right_team, left_team):
        pass

    def on_player_map_change(self, player, map_name):
        pass

    def on_log_plane_positions(self, position_by_player):
        pass

    def on_goal(self, scorer, assister, secondary_assister, xp):
        pass

    def on_structure_destroy(self, player, target, xp):
        pass

    def on_kill(self, kill_type, killer, victim, multikill, streak):
        pass

    def on_round_end(self):
        pass

    def on_command(self, player, command_name, arguments, group):
        pass

    def on_client_add(self, player):
        pass

    def on_client_join(self, player):
        pass

    def on_client_remove(self, nickname, vapor_id, ip, reason):
        pass

    def on_nickname_change(self, old_nickname, player):
        pass

    def on_spawn(self, player, plane, red_perk, green_perk, blue_perk, skin, team):
        pass
