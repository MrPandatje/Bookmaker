import aiohttp
import asyncio
from pydantic import BaseModel
from typing import List


class MarketOdd(BaseModel):
    label: str
    odds: float


class Event(BaseModel):
    bookmaker: str = "Bwin"
    sport: str = "E-Soccer"
    match_name: str
    market_type: str
    outcomes: List[MarketOdd]


class BwinScraper:
    def __init__(self):
        self.base_url = "https://www.bwin.be/cds-api/bettingoffer/fixtures"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "origin": "https://www.bwin.be",
            "referer": "https://www.bwin.be/"
        }

        # De exacte Bwin/Entain architectuur parameters uit jouw cURL
        self.params = {
            "x-bwin-accessid": "NTE3MjUyZDUtNGU5Ni00MTkwLWJkMGQtMDhmOGViNGNiNmRk",
            "lang": "en",
            "country": "BE",
            "userCountry": "BE",
            "fixtureTypes": "Standard",
            "state": "Latest",
            "offerMapping": "Filtered",
            "offerCategories": "Gridable",
            "fixtureCategories": "Gridable,NonGridable,Other",
            "sportIds": "108",  # 108 is E-Soccer op Bwin!
            "isPriceBoost": "false",
            "skip": "0",
            "take": "100",  # Bulk-load 100 matches tegelijk
            "sortBy": "Tags"
        }

    async def fetch_api(self, session: aiohttp.ClientSession) -> dict:
        async with session.get(self.base_url, headers=self.headers, params=self.params) as response:
            if response.status == 200:
                print("   -> [200 OK] Bwin (Entain) API succesvol bereikt.")
                return await response.json()
            else:
                print(f"   -> [ERROR {response.status}] Fout bij het ophalen van Bwin data.")
                return {}

    async def scrape_esoccer(self) -> List[Event]:
        extracted_events = []
        rejected_3way = 0

        async with aiohttp.ClientSession() as session:
            data = await self.fetch_api(session)
            fixtures = data.get("fixtures", [])

            for fixture in fixtures:
                try:
                    match_name = fixture.get("name", {}).get("value", "Unknown Match")
                    markets = fixture.get("optionMarkets", [])

                    for market in markets:
                        market_name_base = market.get("name", {}).get("value", "Unknown Market")
                        options = market.get("options", [])

                        # Wiskundig filter: we willen ALLES met exact 2 uitkomsten (Over/Under, Handicap)
                        if len(options) == 2:
                            outcomes = []

                            for opt in options:
                                label = opt.get("name", {}).get("value", "Unknown")
                                odds = opt.get("price", {}).get("odds", 0.0)

                                # Voorkom gesloten of foutieve weddenschappen
                                if odds > 1.0:
                                    outcomes.append(MarketOdd(label=label, odds=odds))

                            if len(outcomes) == 2:
                                extracted_events.append(Event(
                                    match_name=match_name,
                                    market_type=market_name_base,
                                    outcomes=outcomes
                                ))
                        elif len(options) == 3:
                            rejected_3way += 1

                except Exception:
                    continue

        print(f"   -> 🛡️ Veiligheidsfilter: {rejected_3way} 3-way markten (1X2) genegeerd op Bwin.")
        return extracted_events


# --- Test Logica ---
if __name__ == "__main__":
    scraper = BwinScraper()


    async def run_test():
        print("🚀 Start E-Soccer scraper voor BWIN (Entain API)...\n")
        bwin_events = await scraper.scrape_esoccer()
        print(f"\n✅ Totaal {len(bwin_events)} veilige 2-way E-Soccer markten gefilterd!\n")

        if bwin_events:
            print("--- Preview willekeurige markt op Bwin ---")
            print(bwin_events[0].model_dump_json(indent=2))


    asyncio.run(run_test())