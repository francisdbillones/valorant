import os
import json
import re
import unicodedata
from collections import defaultdict, Counter

def normalize_text(text):
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Normalize unicode (accents, umlauts) to ASCII equivalents
    text = "".join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    # Remove dots and other special chars (keep letters, numbers, spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

class VetoResolver:
    def __init__(self, all_matches, overrides_path=None):
        if overrides_path is None:
            # Default path: same directory as veto_resolver.py
            base_dir = os.path.dirname(os.path.abspath(__file__))
            overrides_path = os.path.join(base_dir, "veto_overrides.json")
            
        self.overrides = {}
        if os.path.exists(overrides_path):
            try:
                with open(overrides_path, "r", encoding="utf-8") as f:
                    self.overrides = json.load(f)
                print(f"Loaded {len(self.overrides)} manual veto overrides from {overrides_path}")
            except Exception as e:
                print(f"Warning: Failed to load veto overrides from {overrides_path}: {e}")
                
        self.global_tag_lookup = self._build_global_lookup(all_matches)
        
    def parse_veto_string(self, veto_str):
        if not veto_str:
            return []
        # Split by semicolon and strip
        segments = [s.strip() for s in veto_str.split(";")]
        actions = []
        for segment in segments:
            if not segment:
                continue
            segment_lower = segment.lower()
            if " remains" in segment_lower:
                # {map} remains
                idx = segment_lower.rfind(" remains")
                map_name = segment[:idx].strip()
                actions.append({
                    "tag": None,
                    "action": "remains",
                    "map_name": map_name
                })
            elif " ban " in segment_lower:
                idx = segment_lower.find(" ban ")
                tag = segment[:idx].strip()
                map_name = segment[idx + len(" ban "):].strip()
                actions.append({
                    "tag": tag,
                    "action": "ban",
                    "map_name": map_name
                })
            elif " pick " in segment_lower:
                idx = segment_lower.find(" pick ")
                tag = segment[:idx].strip()
                map_name = segment[idx + len(" pick "):].strip()
                actions.append({
                    "tag": tag,
                    "action": "pick",
                    "map_name": map_name
                })
        return actions

    def _is_subsequence(self, sub, s):
        if not sub or not s:
            return False
        sub_norm = normalize_text(sub)
        s_norm = normalize_text(s)
        if not sub_norm or not s_norm:
            return False
        it = iter(s_norm)
        return all(c in it for c in sub_norm)

    def _build_global_lookup(self, matches):
        votes = defaultdict(Counter)
        for m in matches:
            veto_str = m.get("map_vetos")
            if not veto_str:
                continue
            
            teams = m.get("teams", [])
            if len(teams) < 2:
                continue
                
            team1_id = str(teams[0].get("id"))
            team1_name = teams[0].get("name")
            team2_id = str(teams[1].get("id"))
            team2_name = teams[1].get("name")
            
            actions = self.parse_veto_string(veto_str)
            tags = set(a["tag"] for a in actions if a["tag"] is not None)
            
            for tag in tags:
                # Skip voting for tags that are manually overridden
                if tag in self.overrides:
                    continue
                    
                in_t1 = self._is_subsequence(tag, team1_name) if team1_name else False
                in_t2 = self._is_subsequence(tag, team2_name) if team2_name else False
                if in_t1 and not in_t2:
                    votes[tag][team1_id] += 1
                elif in_t2 and not in_t1:
                    votes[tag][team2_id] += 1
                    
        # Initialize lookup with manual overrides
        global_lookup = {tag: str(tid) for tag, tid in self.overrides.items()}
        
        # Accept tags with >= 90% majority
        for tag, team_votes in votes.items():
            total_votes = sum(team_votes.values())
            if total_votes > 0:
                top_team, top_count = team_votes.most_common(1)[0]
                if top_count / total_votes >= 0.9:
                    global_lookup[tag] = str(top_team)
        return global_lookup

    def resolve_match(self, match):
        veto_str = match.get("map_vetos")
        teams = match.get("teams", [])
        
        picks = {}      # map_name_lower -> team_id
        deciders = {}   # map_name_lower -> bool
        resolved_mapping = {}  # tag -> team_id
        
        if not veto_str or len(teams) < 2:
            return picks, deciders, resolved_mapping
            
        team1_id = str(teams[0].get("id"))
        team1_name = teams[0].get("name")
        team2_id = str(teams[1].get("id"))
        team2_name = teams[1].get("name")
        
        actions = self.parse_veto_string(veto_str)
        tags = list(set(a["tag"] for a in actions if a["tag"] is not None))
        
        # Look up resolved tags globally or locally
        resolved_tags = {}
        for tag in tags:
            resolved_id = self.global_tag_lookup.get(tag)
            if resolved_id in (team1_id, team2_id):
                resolved_tags[tag] = resolved_id
            else:
                # Fallback to local match-level subsequence check
                in_t1 = self._is_subsequence(tag, team1_name) if team1_name else False
                in_t2 = self._is_subsequence(tag, team2_name) if team2_name else False
                if in_t1 and not in_t2:
                    resolved_tags[tag] = team1_id
                elif in_t2 and not in_t1:
                    resolved_tags[tag] = team2_id
                
        # Resolve by elimination
        if len(tags) == 2:
            t0, t1 = tags[0], tags[1]
            r0 = resolved_tags.get(t0)
            r1 = resolved_tags.get(t1)
            
            if r0 and r1:
                if r0 != r1:
                    resolved_mapping[t0] = r0
                    resolved_mapping[t1] = r1
            elif r0 and not r1:
                resolved_mapping[t0] = r0
                resolved_mapping[t1] = team2_id if r0 == team1_id else team1_id
            elif not r0 and r1:
                resolved_mapping[t1] = r1
                resolved_mapping[t0] = team2_id if r1 == team1_id else team1_id
        elif len(tags) == 1:
            tag = tags[0]
            r = resolved_tags.get(tag)
            if r:
                resolved_mapping[tag] = r
                
        # Generate the map-level pick and decider dictionaries
        for action in actions:
            m_name_lower = action["map_name"].lower()
            tag = action["tag"]
            act_type = action["action"]
            
            if act_type == "pick":
                team_id = resolved_mapping.get(tag)
                if team_id:
                    picks[m_name_lower] = team_id
            elif act_type == "remains":
                deciders[m_name_lower] = True
                
        return picks, deciders, resolved_mapping
