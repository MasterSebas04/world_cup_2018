import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def unicode_conversion(s):
    if s is None:
        return ""
    try:
        return s.encode("utf-8").decode("unicode_escape")
    except Exception:
        return s

event_path = "Soccer_Data/events/events_World_Cup.json"
with open(event_path, "r") as event_file:
    event_data = json.load(event_file)

json_path = "Soccer_Data/players.json"
with open(json_path, "r", encoding="utf-8") as f:
    player_data = json.load(f)

team_path = "Soccer_Data/teams.json"
with open(team_path, "r", encoding="utf-8") as f:
    team_data = json.load(f)

player_by_id = {p["wyId"]: p for p in player_data}
team_by_id = {t["wyId"]: t for t in team_data}

# Map player last names to team IDs
# Track both passers and receivers from the pass events
player_to_team = {}
for i, event in enumerate(event_data[:-1]):
    if event.get("eventName") != "Pass":
        continue
    if not any(tag.get("id") == 1801 for tag in event.get("tags", [])):
        continue

    # Track passer
    passer_id = event.get("playerId")
    team_id = event.get("teamId")
    
    if passer_id is not None and team_id is not None and passer_id in player_by_id:
        passer_name = unicode_conversion(player_by_id[passer_id].get("lastName"))
        if passer_name and passer_name not in player_to_team:
            player_to_team[passer_name] = team_id
    
    # Track receiver (from next event)
    next_event = event_data[i + 1]
    receiver_id = next_event.get("playerId")
    receiver_team_id = next_event.get("teamId")
    
    if receiver_id is not None and receiver_team_id is not None and receiver_id in player_by_id:
        receiver_name = unicode_conversion(player_by_id[receiver_id].get("lastName"))
        if receiver_name and receiver_name not in player_to_team:
            player_to_team[receiver_name] = receiver_team_id

result_tally = {}
for i, event in enumerate(event_data[:-1]):
    if event.get("eventName") != "Pass":
        continue
    if not any(tag.get("id") == 1801 for tag in event.get("tags", [])):
        continue

    next_event = event_data[i + 1]
    passer = event.get("playerId")
    receiver = next_event.get("playerId")

    if passer is None or receiver is None:
        continue
    if passer not in player_by_id or receiver not in player_by_id:
        continue

    key = tuple(sorted([
        unicode_conversion(player_by_id[passer].get("lastName")),
        unicode_conversion(player_by_id[receiver].get("lastName"))
    ]))

    result_tally[key] = result_tally.get(key, 0) + 1

G = nx.Graph()
MIN_WEIGHT = 1  # try 4, 6, 8, 10
for (p1, p2), w in result_tally.items():
    if p1 and p2 and p1 != p2 and w >= MIN_WEIGHT:
        G.add_edge(p1, p2, weight=w)

# Get unique teams from nodes in the graph
nodes_in_graph = list(G.nodes())
teams_in_graph = set()
for node in nodes_in_graph:
    if node in player_to_team:
        teams_in_graph.add(player_to_team[node])

# Create color mapping for each team
unique_teams = sorted(list(teams_in_graph))
colors_list = plt.cm.tab20(np.linspace(0, 1, len(unique_teams)))
team_color_map = {team_id: colors_list[i] for i, team_id in enumerate(unique_teams)}

# Map each node to its color

node_colors = []
for node in nodes_in_graph:
    team_id = player_to_team.get(node)
    if team_id and team_id in team_color_map:
        node_colors.append(team_color_map[team_id])
        # Add team info as node attributes for Gephi
        team_name = team_by_id.get(team_id, {}).get("name", f"Team {team_id}")
        G.nodes[node]["team_id"] = team_id
        G.nodes[node]["team_name"] = team_name


# Export to GEXF format for Gephi
nx.write_gexf(G, "soccer_network.gexf")
print("\nGraph exported to soccer_network.gexf - open in Gephi!")
    


plt.figure(figsize=(14, 14))

pos = nx.spring_layout(G, weight="weight", seed=42, k=1)

weights = [G[u][v]["weight"] for u, v in G.edges()]
max_w = max(weights) if weights else 1
base_widths = [0.1 + 1.5 * (w / max_w) for w in weights]

# Highlight edges for a specific player (change this to highlight different players)
highlight_player = "Pavard"  # Change this to highlight different players

# Create edge colors and widths: green and thick for highlighted player's edges
# We build parallel lists where each index corresponds to the same edge
# The order MUST match G.edges() so that edge_colors[0] and widths[0] style the first edge, etc.
edge_colors = []
widths = []
for i, (u, v) in enumerate(G.edges()):
    if highlight_player.lower() in str(u).lower() or highlight_player.lower() in str(v).lower():
        edge_colors.append('green')
        widths.append(base_widths[i] * 3.0)  # Make highlighted edges 3x thicker
    else:
        edge_colors.append('gray')
        widths.append(base_widths[i])


# Draw all nodes once
nx.draw_networkx_nodes(G, pos, node_size=50, node_color=node_colors)
# Draw all edges once - the function uses the lists to style each edge by index position
nx.draw_networkx_edges(G, pos, width=widths, alpha=0.4, edge_color=edge_colors)
nx.draw_networkx_labels(G, pos, font_size=4, font_color='black', font_weight='normal')

plt.axis("off")
plt.show()