from thefuzz import fuzz


class EventMatcher:
    def __init__(self, match_threshold=75, label_threshold=70):
        self.match_threshold = match_threshold
        self.label_threshold = label_threshold

    def fuzzy_match(self, s1, s2) -> int:
        return fuzz.token_sort_ratio(str(s1).lower(), str(s2).lower())

    def translate_label(self, label: str, match_name: str) -> str:
        clean_name = match_name.replace("·", "-").replace(" - ", "-")
        parts = clean_name.split("-")

        if label == "1" and len(parts) >= 1:
            return parts[0].strip()
        elif label == "2" and len(parts) >= 2:
            return parts[1].strip()

        if "meer" in label.lower() or "over" in label.lower() or "+" in label:
            return "Over"
        if "minder" in label.lower() or "under" in label.lower() or "-" in label:
            return "Under"

        return label

    def find_arbitrage_pairs(self, events_711, events_napoleon) -> list:
        pairs = []

        for e7 in events_711:
            for en in events_napoleon:
                # Veiligheidscheck: Zorg dat de markt-categorieën logisch matchen
                cat_711 = e7.market_type.lower()
                cat_nap = en.market_type.lower()

                # Voorkom kruisingen tussen Handicap, Over/Under en Winnaar
                if ("handicap" in cat_711) != ("handicap" in cat_nap):
                    continue
                if ("over" in cat_711 or "onder" in cat_711 or "minder" in cat_711) != (
                        "over" in cat_nap or "onder" in cat_nap or "minder" in cat_nap):
                    continue

                # 1. Komen de wedstrijdenamen overeen?
                if self.fuzzy_match(e7.match_name, en.match_name) >= self.match_threshold:

                    # 2. Vertaal de labels
                    nap_label_0 = self.translate_label(en.outcomes[0].label, en.match_name)
                    nap_label_1 = self.translate_label(en.outcomes[1].label, en.match_name)
                    s711_label_0 = self.translate_label(e7.outcomes[0].label, e7.match_name)
                    s711_label_1 = self.translate_label(e7.outcomes[1].label, e7.match_name)

                    # 3. Bereken overlap
                    score_straight_1 = self.fuzzy_match(s711_label_0, nap_label_0)
                    score_straight_2 = self.fuzzy_match(s711_label_1, nap_label_1)
                    avg_straight = (score_straight_1 + score_straight_2) / 2

                    score_cross_1 = self.fuzzy_match(s711_label_0, nap_label_1)
                    score_cross_2 = self.fuzzy_match(s711_label_1, nap_label_0)
                    avg_cross = (score_cross_1 + score_cross_2) / 2

                    # 4. Voeg samen
                    if avg_straight >= self.label_threshold and avg_straight > avg_cross:
                        pairs.append({
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
                        })
                    elif avg_cross >= self.label_threshold:
                        pairs.append({
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
                        })
        return pairs