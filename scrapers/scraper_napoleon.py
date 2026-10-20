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


# --- Async API Scraper (Met jouw exacte 2026 E-Soccer override) ---
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

    async def fetch_api(self, session: aiohttp.ClientSession, params: dict, sport_name: str) -> list:
        async with session.get(self.base_url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("events", [])
            else:
                print(f"⚠️ API Error {response.status} voor {sport_name}")
                return []

    async def scrape_sport_bulk(self, sport_id: int, sport_name: str, custom_params: dict = None) -> List[Event]:
        extracted_events = []

        async with aiohttp.ClientSession() as session:
            # Gebruik de custom params (jouw 2026 cURL) of bereken dynamisch voor Tennis
            if custom_params:
                params_prematch = custom_params
                live_events = []  # We doen even exact jouw cURL (prematch)
            else:
                now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
                start_date = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                end_date = (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

                params_prematch = {"startDate": start_date, "endDate": end_date, "index": "active-prematch",
                                   "sports": str(sport_id)}

            prematch_events = await self.fetch_api(session, params_prematch, sport_name)
            all_events = prematch_events

            for item in all_events:
                try:
                    match_name = item.get("fixture", {}).get("event_name", "Unknown Match")
                    markets = item.get("markets", [])

                    for market in markets:
                        market_name_base = market.get("name", "Unknown Market")
                        odds_data = market.get("odds", [])

                        # UUID Groepering voor correcte 2-way Over/Under detectie
                        lines = {}
                        for odd in odds_data:
                            meta = odd.get("metadata", {})
                            line_key = meta.get("market_line_uuid", "default")
                            if line_key not in lines:
                                lines[line_key] = []
                            lines[line_key].append(odd)

                        for line_key, grouped_odds in lines.items():
                            if len(grouped_odds) == 2:
                                outcomes = []
                                specific_market_name = market_name_base

                                for odd in grouped_odds:
                                    price = odd.get("price", 0.0)
                                    meta = odd.get("metadata", {})
                                    label = meta.get("name", "Unknown")

                                    if "special_bet_value" in meta and specific_market_name == market_name_base:
                                        specific_market_name = f"{market_name_base} ({meta['special_bet_value']})"

                                    outcomes.append(MarketOdd(label=label, odds=price))

                                extracted_events.append(Event(
                                    sport=sport_name,
                                    match_name=match_name,
                                    market_type=specific_market_name,
                                    outcomes=outcomes
                                ))
                except Exception:
                    continue

        return extracted_events


# --- Orkestratie en Test ---
if __name__ == "__main__":
    scraper = NapoleonScraper()


    async def run_all():
        print("🚀 Start scraping...\n")

        # 1. E-SOCCER MET JOUW EXACTE 2026 OVERRIDE
        esoccer_params = {
            "startDate": "2026-10-20T16:00:00.000Z",
            "endDate": "2026-10-21T08:00:00.000Z",
            "index": "active-prematch",
            "sports": "75"
        }
        print("Scraping E-Soccer (Sport ID: 75, met 2026 Override)...")
        esoccer_events = await scraper.scrape_sport_bulk(sport_id=75, sport_name="E-Soccer",
                                                         custom_params=esoccer_params)
        print(f"✅ Totaal {len(esoccer_events)} 2-way E-Soccer markten gevonden!\n")

        # 2. TENNIS (Dynamische datums)
        print("Scraping Tennis (Sport ID: 2, Dynamisch)...")
        tennis_events = await scraper.scrape_sport_bulk(sport_id=2, sport_name="Tennis")
        print(f"✅ Totaal {len(tennis_events)} 2-way Tennis markten gevonden!\n")

        if esoccer_events:
            print("--- Preview E-Soccer markt ---")
            print(esoccer_events[0].model_dump_json(indent=2))


    asyncio.run(run_all())