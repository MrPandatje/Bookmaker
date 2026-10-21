import re
from thefuzz import fuzz


class EventMatcher:
    def __init__(self, match_threshold=75, label_threshold=75):
        self.match_threshold = match_threshold
        self.label_threshold = label_threshold

    def fuzzy_match(self, s1, s2) -> int:
        return fuzz.token_set_ratio(str(s1).lower(), str(s2).lower())

    def get_line(self, event) -> float:
        """
        Scan de markttitel én de labels op kommagetallen (bijv. 22.5 of 4.5).
        Negeert plus- en mintekens, pakt puur de absolute lijnwaarde.
        """
        for text in [event.market_type, event.outcomes[0].label, event.outcomes[1].label]:
            match = re.search(r'\d+\.\d+', text)
            if match:
                return float(match.group())
        return None

    def translate_label(self, label: str, match_name: str) -> str:
        label_lower = label.lower()

        # Strip alles weg tot de essentie: Over of Under
        if "meer" in label_lower or "over" in label_lower or "+" in label_lower: return "Over"
        if "minder" in label_lower or "under" in label_lower or "onder" in label_lower or "-" in label_lower: return "Under"

        # Speler 1 of 2
        clean_name = match_name.replace("·", "-").replace(" - ", "-")
        parts = clean_name.split("-")
        if label == "1" and len(parts) >= 1: return parts[0].strip()
        if label == "2" and len(parts) >= 2: return parts[1].strip()

        return label

    def find_arbitrage_pairs(self, events_711, events_napoleon) -> list:
        pairs = []
        seen_hashes = set()

        for e7 in events_711:
            for en in events_napoleon:
                # 1. Naam check
                if self.fuzzy_match(e7.match_name, en.match_name) < self.match_threshold:
                    continue

                # 2. De 360-Graden Lijn Check
                line_711 = self.get_line(e7)
                line_nap = self.get_line(en)

                # Als één van beide een getal heeft (bijv. 4.5), MOET de ander dat ook hebben.
                # Dit garandeert dat we Over/Under 21.5 nooit met 22.5 matchen, of met een Winnaar markt.
                if line_711 != line_nap:
                    continue

                    # 3. Label Vertaling
                nap_label_0 = self.translate_label(en.outcomes[0].label, en.match_name)
                nap_label_1 = self.translate_label(en.outcomes[1].label, en.match_name)
                s711_label_0 = self.translate_label(e7.outcomes[0].label, e7.match_name)
                s711_label_1 = self.translate_label(e7.outcomes[1].label, e7.match_name)

                # 4. Kruiselingse Vergelijking
                score_straight_1 = self.fuzzy_match(s711_label_0, nap_label_0)
                score_straight_2 = self.fuzzy_match(s711_label_1, nap_label_1)
                avg_straight = (score_straight_1 + score_straight_2) / 2

                score_cross_1 = self.fuzzy_match(s711_label_0, nap_label_1)
                score_cross_2 = self.fuzzy_match(s711_label_1, nap_label_0)
                avg_cross = (score_cross_1 + score_cross_2) / 2

                pair_data = None
                if avg_straight >= self.label_threshold and avg_straight > avg_cross:
                    pair_data = {
                        "match_name": e7.match_name,
                        "market_711": e7.market_type,
                        "market_nap": en.market_type,
                        "bet_711_A_label": e7.outcomes[0].label,
                        "bet_711_A_odds": e7.outcomes[0].odds,
                        "hedge_nap_A_label": en.outcomes[1].label,
                        "hedge_nap_A_odds": en.outcomes[1].odds,
                        "bet_711_B_label": e7.outcomes[1].label,
                        "bet_711_B_odds": e7.outcomes[1].odds,
                        "hedge_nap_B_label": en.outcomes[0].label,
                        "hedge_nap_B_odds": en.outcomes[0].odds,
                    }
                elif avg_cross >= self.label_threshold:
                    pair_data = {
                        "match_name": e7.match_name,
                        "market_711": e7.market_type,
                        "market_nap": en.market_type,
                        "bet_711_A_label": e7.outcomes[0].label,
                        "bet_711_A_odds": e7.outcomes[0].odds,
                        "hedge_nap_A_label": en.outcomes[0].label,
                        "hedge_nap_A_odds": en.outcomes[0].odds,
                        "bet_711_B_label": e7.outcomes[1].label,
                        "bet_711_B_odds": e7.outcomes[1].odds,
                        "hedge_nap_B_label": en.outcomes[1].label,
                        "hedge_nap_B_odds": en.outcomes[1].odds,
                    }

                if pair_data:
                    # Deduplicatie via een unieke vingerafdruk (inclusief de lijn!)
                    hash_str = f"{pair_data['match_name']}_{line_711}_{pair_data['market_711']}"
                    if hash_str not in seen_hashes:
                        seen_hashes.add(hash_str)
                        pairs.append(pair_data)

        return pairs