import asyncio
from scrapers.scraper_napoleon import NapoleonScraper
from scrapers.scraper_711 import Scraper711
from scrapers.scraper_bwin import BwinScraper
from engine.matcher import EventMatcher
from engine.calculator import ArbitrageEngine


async def run_arbitrage_engine():
    print("==================================================")
    print("🚀 HIGH-THROUGHPUT ARBITRAGE & OPTIMIZATION ENGINE")
    print("==================================================\n")

    print("[1/3] Fetching data streams concurrently via internal APIs...")
    nap_scraper = NapoleonScraper()
    s711_scraper = Scraper711()
    bwin_scraper = BwinScraper()

    # We vuren alle 4 de requests asynchroon TEGELIJK af voor maximale snelheid
    task_s711_tennis = s711_scraper.scrape_sport("tennis/all/all", "Tennis")
    task_nap_tennis = nap_scraper.scrape_tennis()

    task_s711_esoccer = s711_scraper.scrape_sport("football/esports_football/all/all", "E-Soccer")
    task_bwin_esoccer = bwin_scraper.scrape_esoccer()

    # Wacht tot alles binnen is
    s711_tennis, nap_tennis, s711_esoccer, bwin_esoccer = await asyncio.gather(
        task_s711_tennis, task_nap_tennis, task_s711_esoccer, task_bwin_esoccer
    )

    print(f"      [Tennis]   Ingested: 711 ({len(s711_tennis)} markets) | Napoleon ({len(nap_tennis)} markets)")
    print(f"      [E-Soccer] Ingested: 711 ({len(s711_esoccer)} markets) | Bwin ({len(bwin_esoccer)} markets)\n")

    print("[2/3] Running Fuzzy String Matcher & Line Extractor...")
    matcher = EventMatcher()

    # We matchen ze per sport
    tennis_pairs = matcher.find_arbitrage_pairs(s711_tennis, nap_tennis)
    esoccer_pairs = matcher.find_arbitrage_pairs(s711_esoccer, bwin_esoccer)

    print(f"      [Tennis]   Identical markets paired: {len(tennis_pairs)}")
    print(f"      [E-Soccer] Identical markets paired: {len(esoccer_pairs)}\n")

    print("[3/3] Calculating Dutching constraints & EV (50% 711-Boost)...\n")
    calculator = ArbitrageEngine(fixed_stake_711=50.0, boost_multiplier=1.50)

    # --- HELPER FUNCTIE VOOR BEREKENING ---
    def evaluate_pairs(pairs, hedge_bookmaker_name):
        profitable = []
        for p in pairs:
            # Richting A
            res_A = calculator.evaluate_opportunity(p['bet_711_A_odds'], p['hedge_nap_A_odds'])
            if res_A and res_A.net_profit > 0:
                p['hedge_bookmaker'] = hedge_bookmaker_name
                profitable.append((p, "A", res_A))

            # Richting B
            res_B = calculator.evaluate_opportunity(p['bet_711_B_odds'], p['hedge_nap_B_odds'])
            if res_B and res_B.net_profit > 0:
                p['hedge_bookmaker'] = hedge_bookmaker_name
                profitable.append((p, "B", res_B))

        # Sorteer hoogste winst bovenaan
        profitable.sort(key=lambda x: x[2].net_profit, reverse=True)
        return profitable

    tennis_opportunities = evaluate_pairs(tennis_pairs, "Napoleon")
    esoccer_opportunities = evaluate_pairs(esoccer_pairs, "Bwin")

    # --- OUTPUT GENERATIE ---
    print("==================================================")
    print(f"SYSTEM REPORT: {len(tennis_opportunities) + len(esoccer_opportunities)} POSITIVE EV OPPORTUNITIES FOUND")
    print("==================================================\n")

    def print_top_5(opportunities, title):
        print(f"🏆 {title} (Top 5):")
        print("-" * 50)
        if not opportunities:
            print("Geen winstgevende arbitrage gevonden voor deze categorie momenteel.\n")
            return

        for i, (p, direction, calc) in enumerate(opportunities[:5]):
            if direction == "A":
                bet_711_label = p['bet_711_A_label']
                hedge_label = p['hedge_nap_A_label']
            else:
                bet_711_label = p['bet_711_B_label']
                hedge_label = p['hedge_nap_B_label']

            hedge_bookie = p['hedge_bookmaker']

            print(f"#{i + 1} | Match:  {p['match_name']}")
            print(f"     Market: {p['market_711']} (711) vs {p['market_nap']} ({hedge_bookie})")
            print(
                f"     711:    Bet on '{bet_711_label}' @ Boosted {calc.odds_711_boosted} (Stake: EUR {calc.stake_711:.2f})")
            print(
                f"     Hedge:  Bet on '{hedge_label}' @ {calc.odds_napoleon} (Stake: EUR {calc.stake_napoleon:.2f}) on {hedge_bookie}")
            print(f"     PROFIT: EUR {calc.net_profit:.2f} (ROI: {calc.roi_percentage}%)")
            print("-" * 50)
        print("")

    # Print de twee dashboards!
    print_top_5(tennis_opportunities, "TENNIS (711 vs Napoleon)")
    print_top_5(esoccer_opportunities, "E-SOCCER (711 vs Bwin)")


if __name__ == "__main__":
    asyncio.run(run_arbitrage_engine())