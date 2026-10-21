import asyncio
from scrapers.scraper_napoleon import NapoleonScraper
from scrapers.scraper_711 import Scraper711
from engine.matcher import EventMatcher
from engine.calculator import ArbitrageEngine


async def run_arbitrage_engine():
    print("--------------------------------------------------")
    print("INITIALIZING ARBITRAGE & OPTIMIZATION ENGINE")
    print("--------------------------------------------------\n")

    print("[1/3] Fetching data streams via internal JSON APIs...")
    nap_scraper = NapoleonScraper()
    s711_scraper = Scraper711()

    nap_events, s711_events = await asyncio.gather(
        nap_scraper.scrape_tennis(),
        s711_scraper.scrape_tennis()
    )
    print(f"      Data ingested: {len(nap_events)} (Napoleon) | {len(s711_events)} (711)\n")

    print("[2/3] Running Fuzzy String Matcher...")
    matcher = EventMatcher()
    pairs = matcher.find_arbitrage_pairs(s711_events, nap_events)
    print(f"      Identical markets paired: {len(pairs)}\n")

    print("[3/3] Calculating Dutching constraints & EV (50% 711-Boost)...\n")
    calculator = ArbitrageEngine(fixed_stake_711=50.0, boost_multiplier=1.50)

    profitable_opportunities = []
    for p in pairs:
        res_A = calculator.evaluate_opportunity(p['bet_711_A_odds'], p['hedge_nap_A_odds'])
        if res_A and res_A.net_profit > 0:
            profitable_opportunities.append((p, "A", res_A))

        res_B = calculator.evaluate_opportunity(p['bet_711_B_odds'], p['hedge_nap_B_odds'])
        if res_B and res_B.net_profit > 0:
            profitable_opportunities.append((p, "B", res_B))

    # Sorteer op absolute netto winst (hoogste bovenaan)
    profitable_opportunities.sort(key=lambda x: x[2].net_profit, reverse=True)

    print("--------------------------------------------------")
    print(f"SYSTEM REPORT: {len(profitable_opportunities)} POSITIVE EV OPPORTUNITIES FOUND")
    print("--------------------------------------------------\n")

    if not profitable_opportunities:
        print("No profitable arbitrage opportunities found at this moment.")
        return

    print("TOP 5 MOST PROFITABLE OPPORTUNITIES:")
    print("==================================================\n")

    for i, item in enumerate(profitable_opportunities[:5]):
        p, direction, calc = item
        if direction == "A":
            bet_711_label = p['bet_711_A_label']
            hedge_nap_label = p['hedge_nap_A_label']
        else:
            bet_711_label = p['bet_711_B_label']
            hedge_nap_label = p['hedge_nap_B_label']

        print(f"#{i + 1} | Match:  {p['match_name']}")
        print(f"     Market: {p['market_711']} (711) vs {p['market_nap']} (Napoleon)")
        print(
            f"     711:    Bet on '{bet_711_label}' @ Boosted {calc.odds_711_boosted} (Stake: EUR {calc.stake_711:.2f})")
        print(f"     Nap:    Bet on '{hedge_nap_label}' @ {calc.odds_napoleon} (Stake: EUR {calc.stake_napoleon:.2f})")
        print(f"     PROFIT: EUR {calc.net_profit:.2f} (ROI: {calc.roi_percentage}%)")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_arbitrage_engine())