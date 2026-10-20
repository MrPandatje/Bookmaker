import aiohttp
import asyncio
from pydantic import BaseModel
from typing import List


# --- Data Modellen ---
# We gebruiken exact dezelfde modellen als bij Napoleon,
# zodat de Calculator dadelijk niet doorheeft dat de data van 2 verschillende API's komt!
class MarketOdd(BaseModel):
    label: str
    odds: float


class Event(BaseModel):
    bookmaker: str = "711"
    sport: str
    match_name: str
    market_type: str
    outcomes: List[MarketOdd]


# --- Async API Scraper (711 / Kambi) ---
class Scraper711:
    def __init__(self):
        # Standaard Kambi pad voor ALLE tenniswedstrijden
        self.base_url = "https://eu.offering-api.kambicdn.com/offering/v2018/sevelevbe/listView/tennis/all/all.json"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "accept": "application/json",
            "origin": "https://www.711sports.be",
            "referer": "https://www.711sports.be/"
        }

        # De verplichte Kambi parameters uit jouw cURL
        self.params = {
            "lang": "nl_BE",
            "market": "BE",
            "client_id": "200",
            "channel_id": "1",
            "useCombined": "true",
            "useCombinedLive": "true"
        }

    async def scrape_tennis(self) -> List[Event]:
        """Haalt Tennis data op van 711 en formatteert de Kambi JSON."""
        extracted_events = []

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, headers=self.headers, params=self.params) as response:
                if response.status != 200:
                    print(f"⚠️ API Error {response.status} bij 711.be")
                    return []

                data = await response.json()
                events_list = data.get("events", [])

                for item in events_list:
                    try:
                        # Haal Match naam op ("Speler A - Speler B")
                        event_info = item.get("event", {})
                        match_name = event_info.get("name", "Unknown Match")

                        # Kambi groepeert alle markten keurig in 'betOffers'
                        bet_offers = item.get("betOffers", [])

                        for offer in bet_offers:
                            outcomes_data = offer.get("outcomes", [])

                            # Wiskundige filter: We willen enkel 2-way odds (Arbitrage)
                            if len(outcomes_data) == 2:
                                market_name = offer.get("criterion", {}).get("label", "Unknown Market")

                                outcomes = []
                                # Check of dit een Handicap of Over/Under lijn is (bijv 36500 -> 36.5)
                                # Kambi zet de 'line' parameter altijd in de eerste uitkomst
                                if "line" in outcomes_data[0]:
                                    line_value = outcomes_data[0]["line"] / 1000.0
                                    # Voeg de lijnwaarde toe aan de marktnaam (bijv. "Game Handicap (36.5)")
                                    # We gebruiken + of - om te bepalen of het exact zo geprint moet worden
                                    market_name = f"{market_name} ({abs(line_value)})"

                                for odd in outcomes_data:
                                    # Kambi odds zijn x1000 (1470 = 1.47)
                                    decimal_odds = odd.get("odds", 0) / 1000.0
                                    label = odd.get("label", "Unknown")

                                    # Voorkom gesloten weddenschappen met odds = 0
                                    if decimal_odds > 1.0:
                                        outcomes.append(MarketOdd(label=label, odds=decimal_odds))

                                # Voeg alleen toe als beide uitkomsten geldige odds hadden
                                if len(outcomes) == 2:
                                    extracted_events.append(Event(
                                        sport="Tennis",
                                        match_name=match_name,
                                        market_type=market_name,
                                        outcomes=outcomes
                                    ))
                    except Exception as e:
                        # Stille fail per match zodat de rest blijft draaien
                        continue

        return extracted_events


# --- Test Logica ---
if __name__ == "__main__":
    scraper = Scraper711()


    async def run_test():
        print("🚀 Start clean Tennis scraper voor 711.be (Kambi API)...\n")
        tennis_events = await scraper.scrape_tennis()
        print(f"✅ Totaal {len(tennis_events)} 2-way Tennis markten gevonden op 711.be!\n")

        if tennis_events:
            print("--- Preview willekeurige markt op 711 ---")
            print(tennis_events[0].model_dump_json(indent=2))


    asyncio.run(run_test())