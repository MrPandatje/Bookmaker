import aiohttp
import asyncio
from pydantic import BaseModel
from typing import List


class MarketOdd(BaseModel):
    label: str
    odds: float


class Event(BaseModel):
    bookmaker: str = "711"
    sport: str
    match_name: str
    market_type: str
    outcomes: List[MarketOdd]


class Scraper711:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "accept": "application/json",
            "origin": "https://www.711sports.be",
            "referer": "https://www.711sports.be/"
        }
        self.params = {
            "lang": "nl_BE",
            "market": "BE",
            "client_id": "200",
            "channel_id": "1",
            "useCombined": "true",
            "useCombinedLive": "true"
        }

    async def scrape_sport(self, sport_path: str, sport_name: str) -> List[Event]:
        """
        Dynamische scraper.
        sport_path voor Tennis = 'tennis/all/all'
        sport_path voor E-Soccer = 'football/esports_football/all/all'
        """
        extracted_events = []
        base_url = f"https://eu.offering-api.kambicdn.com/offering/v2018/sevelevbe/listView/{sport_path}.json"

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=self.headers, params=self.params) as response:
                if response.status != 200:
                    print(f"⚠️ API Error {response.status} bij 711.be voor {sport_name}")
                    return []

                data = await response.json()
                events_list = data.get("events", [])

                for item in events_list:
                    try:
                        match_name = item.get("event", {}).get("name", "Unknown Match")
                        bet_offers = item.get("betOffers", [])

                        for offer in bet_offers:
                            outcomes_data = offer.get("outcomes", [])

                            # Filter op 2-way (Over/Under, Even/Odd)
                            if len(outcomes_data) == 2:
                                market_name = offer.get("criterion", {}).get("label", "Unknown Market")
                                outcomes = []

                                if "line" in outcomes_data[0]:
                                    line_value = outcomes_data[0]["line"] / 1000.0
                                    market_name = f"{market_name} ({abs(line_value)})"

                                for odd in outcomes_data:
                                    decimal_odds = odd.get("odds", 0) / 1000.0
                                    label = odd.get("label", "Unknown")
                                    if decimal_odds > 1.0:
                                        outcomes.append(MarketOdd(label=label, odds=decimal_odds))

                                if len(outcomes) == 2:
                                    extracted_events.append(Event(
                                        sport=sport_name,
                                        match_name=match_name,
                                        market_type=market_name,
                                        outcomes=outcomes
                                    ))
                    except Exception:
                        continue

        return extracted_events


# --- Test Logica ---
if __name__ == "__main__":
    scraper = Scraper711()


    async def run_test():
        print("🚀 Start E-Soccer scraper voor 711.be (Kambi API)...\n")

        # We gebruiken hier het exacte pad dat we uit jouw cURL hebben afgeleid!
        esoccer_events = await scraper.scrape_sport("football/esports_football/all/all", "E-Soccer")

        print(f"✅ Totaal {len(esoccer_events)} 2-way E-Soccer markten gevonden op 711.be!\n")

        if esoccer_events:
            print("--- Preview willekeurige markt op 711 ---")
            print(esoccer_events[0].model_dump_json(indent=2))


    asyncio.run(run_test())