from altitude import AltitudeMod


class FlightClub(AltitudeMod):
    def on_server_map_change(self, map_name, mode, right_team, left_team):
        self.map_team_colours = [right_team, left_team]
        if map_name.startwith("1lh") and not self.onelh:
            self.onelh = True
            self.commands.disable_weapon("secondary")
            self.commands.health_modifier(1)
        elif not map_name.startwith("1lh") and self.onelh:
            self.onelh = False
            self.commands.disable_weapon("nothing")
            self.commands.health_modifier(100)

    def find_player(self, partial_nickname):
        matched_players = []
        for player in self.players.players:
            if partial_nickname.lower() in player.nickname.lower():
                matched_players.append(player)
        if not matched_players:
            return None
        if len(matched_players) > 1:
            return False
        else:
            return matched_players[0]

    def find_position(self, position):
        if position == "spec":
            return -1
        elif position == "left" or position.lower() == self.map_team_colours[0]:
            return 0
        elif position == "right" or position.lower() == self.map_team_colours[1]:
            return 1
        else:
            return None

    def move(self, player, partial_nickname, position):
        player_found = self.find_player(partial_nickname)
        if player_found is None:
            self.commands.whisper(player.nickname, "There is no player that matches this partial nickname.")
        elif player_found is False:
            self.commands.whisper(player.nickname, "More than one players match this partial nickname.")
            self.commands.whisper(player.nickname, "Be more specific!")
        else:
            position = self.find_position(position)
            if not position:
                self.commands.whisper(player.nickname, 'Team can be "left", "right" or "spec"!')
            else:
                if position == -1:
                    found = False
                    for team in self.teams:
                        for team_player in team:
                            if team_player is player_found:
                                team.remove(team_player)
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        self.commands.whisper(player.nickname,
                                              "{} isn't assigned to any team.".format(player_found.nickname))

                else:
                    self.teams[position].append(player_found)

                if self.mode == "tourny":
                    self.commands.modify_tournament(player_found.nickname, position)

    def swap(self, player, partial_nickname1, partial_nickname2):
        players = [[partial_nickname1], [partial_nickname2]]
        for i in range(2):
            player_found = self.find_player(players[i][0])
            if player_found is None:
                self.commands.whisper(player.nickname, "There is no player that matches this partial nickname.")
                return
            elif player_found is False:
                self.commands.whisper(player.nickname, "More than one players match this partial nickname.")
                self.commands.whisper(player.nickname, "Be more specific!")
                return
            else:
                players[i][0] = player_found
        for player_found in range(2):
            found = False
            for team in range(2):
                for team_player in self.teams[team]:
                    if team_player is player_found:
                        players[player_found].append(team)
                        found = True
                        break
                if found:
                    break
            if not found:
                players[player_found] = -1
        if players[0][1] == -1:
            if players[1][1] == -1:
                pass
            else:
                team = self.teams[players[1][1]]
                team[team.index(players[1][0])] = players[0][0]
                if self.mode == "tourny":
                    self.commands.modify_tournament(players[0][0].nickname, players[1][1])
                    self.commands.modify_tournament(players[1][0].nickname, -1)
        elif players[1][1] == -1:
            team = self.teams[players[0][1]]
            team[team.index(players[0][0])] = players[1][0]
            if self.mode == "tourny":
                self.commands.modify_tournament(players[1][0].nickname, players[0][1])
                self.commands.modify_tournament(players[0][0].nickname, -1)
        else:
            team1 = self.teams[players[0][1]]
            team2 = self.teams[players[1][1]]
            team2[team2.index(players[1][0])] = players[0][0]
            team1[team1.index(players[0][0])] = players[1][0]
            if self.mode == "tourny":
                self.commands.modify_tournament(players[0][0].nickname, players[1][1])
                self.commands.modify_tournament(players[1][0].nickname, players[0][1])

    def on_client_add(self, player):
        self.commands.message("Please welcome {} to flight club,".format(player.nickname))
        self.commands.message("the place where good alitutude happens!")

    def on_chat(self, player, message, server_message, team_message):
        if message.startswith(".move"):
            parts = message.split()[1:]
            if len(parts) == 2:
                self.move(player, *parts)
            else:
                self.commands.whisper(player.nickname, "Wrong structure of function.")
                self.commands.whisper(player.nickname, 'Please use it like this: ".move <nickname> <team>"')
        elif message.startswith(".swap"):
            parts = message.split()[1:]
            if len(parts) == 2:
                self.swap(player, *parts)
            else:
                self.commands.whisper(player.nickname, "Wrong structure of function.")
                self.commands.whisper(player.nickname, 'Please use it like this: ".swap <nickname 1> <nickname 2>"')
