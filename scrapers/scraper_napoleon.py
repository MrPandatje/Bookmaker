import aiohttp
import asyncio
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta, timezone


# --- Data Modellen ---
class MarketOdd(BaseModel):
    label: str
    odds: float


class Event(BaseModel):
    bookmaker: str = "Napoleon"
    sport: str
    match_name: str
    market_type: str
    outcomes: List[MarketOdd]


# --- Async API Scraper (Strictly Tennis) ---
class NapoleonScraper:
    def __init__(self):
        self.base_url = "https://production-superbet-offer-ng-be.freetls.fastly.net/v3/nl-BE/events"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "accept": "application/json",
            "origin": "https://napoleonsports.be",
            "referer": "https://napoleonsports.be/",
            "x-client-id": "ohwfUEGdhUdjcYieNdffbw=="
        }

    def _get_time_params(self, days_ahead: int = 14) -> dict:
        """Genereert dynamische tijdstempels voor Tennis (tot 2 weken vooruit)."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        future = now + timedelta(days=days_ahead)

        return {
            "startDate": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "endDate": future.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "index": "active-prematch",
            "sports": "2"  # 2 is het vaste Sport ID voor Tennis
        }

    async def fetch_api(self, session: aiohttp.ClientSession, params: dict) -> list:
        async with session.get(self.base_url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("events", [])
            else:
                print(f"⚠️ API Error {response.status} bij ophalen Tennis data.")
                return []

    async def scrape_tennis(self) -> List[Event]:
        """Haalt alle Tennis wedstrijden op en extraheert strict 2-way markten."""
        extracted_events = []
        params = self._get_time_params()

        async with aiohttp.ClientSession() as session:
            events = await self.fetch_api(session, params)

            for item in events:
                try:
                    match_name = item.get("fixture", {}).get("event_name", "Unknown Match")
                    markets = item.get("markets", [])

                    for market in markets:
                        market_name_base = market.get("name", "Unknown Market")
                        odds_data = market.get("odds", [])

                        # Groepeer odds op hun line_uuid (cruciaal voor handicap lijnen in Tennis)
                        lines = {}
                        for odd in odds_data:
                            line_key = odd.get("metadata", {}).get("market_line_uuid", "default")
                            if line_key not in lines:
                                lines[line_key] = []
                            lines[line_key].append(odd)

                        # Alleen 2-way markten goedkeuren
                        for line_key, grouped_odds in lines.items():
                            if len(grouped_odds) == 2:
                                outcomes = []
                                specific_market_name = market_name_base

                                for odd in grouped_odds:
                                    price = odd.get("price", 0.0)
                                    meta = odd.get("metadata", {})
                                    label = meta.get("name", "Unknown")

                                    # Voeg handicap-waarde toe aan de marktnaam als deze bestaat
                                    if "special_bet_value" in meta and specific_market_name == market_name_base:
                                        specific_market_name = f"{market_name_base} ({meta['special_bet_value']})"

                                    outcomes.append(MarketOdd(label=label, odds=price))

                                extracted_events.append(Event(
                                    sport="Tennis",
                                    match_name=match_name,
                                    market_type=specific_market_name,
                                    outcomes=outcomes
                                ))
                except Exception:
                    continue

        return extracted_events


# --- Test Logica ---
if __name__ == "__main__":
    scraper = NapoleonScraper()


    async def run_test():
        print("🚀 Start clean Tennis scraper voor Napoleon Games...\n")
        tennis_events = await scraper.scrape_tennis()
        print(f"✅ Totaal {len(tennis_events)} 2-way Tennis markten gevonden!\n")

        if tennis_events:
            print("--- Preview eerste resultaat ---")
            print(tennis_events[0].model_dump_json(indent=2))


    asyncio.run(run_test())