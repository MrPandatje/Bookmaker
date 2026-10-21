import aiohttp
import asyncio
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta, timezone


class MarketOdd(BaseModel):
    label: str
    odds: float


class Event(BaseModel):
    bookmaker: str = "Napoleon"
    sport: str = "Tennis"
    match_name: str
    market_type: str
    outcomes: List[MarketOdd]


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

    def _get_time_params(self, index_type: str) -> dict:
        """Kijkt standaard 14 dagen vooruit voor Tennis."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        future = now + timedelta(days=14)

        return {
            "startDate": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "endDate": future.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "index": index_type,
            "sports": "2"  # Hardcoded Tennis ID
        }

    async def fetch_api(self, session: aiohttp.ClientSession, params: dict, index_name: str) -> list:
        async with session.get(self.base_url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                events = data.get("events", [])
                print(f"   -> [200 OK] {index_name} API leverde {len(events)} RUWE matchen op.")
                return events
            else:
                print(f"   -> [ERROR {response.status}] op {index_name}.")
                return []

    async def scrape_tennis(self) -> List[Event]:
        extracted_events = []
        rejected_3way = 0

        async with aiohttp.ClientSession() as session:
            params_prematch = self._get_time_params("active-prematch")
            params_live = self._get_time_params("active-live")

            prematch_events = await self.fetch_api(session, params_prematch, "Prematch")
            live_events = await self.fetch_api(session, params_live, "Live")

            all_events = prematch_events + live_events

            for item in all_events:
                try:
                    match_name = item.get("fixture", {}).get("event_name", "Unknown Match")
                    markets = item.get("markets", [])

                    for market in markets:
                        market_name_base = market.get("name", "Unknown Market")
                        odds_data = market.get("odds", [])

                        lines = {}
                        for odd in odds_data:
                            meta = odd.get("metadata", {})
                            line_key = meta.get("special_bet_value") or meta.get("market_line_uuid") or "default"

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
                                    match_name=match_name,
                                    market_type=specific_market_name,
                                    outcomes=outcomes
                                ))
                            elif len(grouped_odds) == 3:
                                rejected_3way += 1
                except Exception:
                    continue

        print(f"   -> 🛡️ Veiligheidsfilter: {rejected_3way} markten met 3 uitkomsten genegeerd.")
        return extracted_events


# --- Test Logica ---
if __name__ == "__main__":
    scraper = NapoleonScraper()


    async def run_test():
        print("🚀 Start clean Tennis scraper voor Napoleon Games...\n")
        tennis_events = await scraper.scrape_tennis()
        print(f"\n✅ Totaal {len(tennis_events)} veilige 2-way Tennis markten gefilterd!\n")


    asyncio.run(run_test())