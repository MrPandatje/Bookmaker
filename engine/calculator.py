from pydantic import BaseModel
from typing import Optional


class ArbitrageResult(BaseModel):
    odds_711_base: float
    odds_711_boosted: float
    odds_napoleon: float
    stake_711: float
    stake_napoleon: float
    total_investment: float
    guaranteed_payout: float
    net_profit: float
    roi_percentage: float


class ArbitrageEngine:
    def __init__(self, fixed_stake_711: float = 50.0, boost_multiplier: float = 1.50):
        self.fixed_stake_711 = fixed_stake_711
        self.boost_multiplier = boost_multiplier

    def calculate_boosted_odds(self, base_odds: float) -> float:
        """
        Berekent de effectieve odds inclusief de 711 Profit Boost.
        Formule: 1 + (Base - 1) * 1.50
        """
        if base_odds <= 1.0:
            return base_odds
        return 1 + (base_odds - 1) * self.boost_multiplier

    def evaluate_opportunity(self, odds_711: float, odds_napoleon: float) -> Optional[ArbitrageResult]:
        """
        Berekent de optimale inzet voor Napoleon om winst te egaliseren,
        en retourneert resultaten als er sprake is van positieve EV.
        """
        # Voorkom zero-division errors als odds verkeerd doorkomen
        if odds_napoleon <= 0 or odds_711 <= 0:
            return None

        boosted_odds_711 = self.calculate_boosted_odds(odds_711)

        # Payout 711 = Stake_711 * Odds_711 = Stake_Nap * Odds_Nap
        payout_711 = self.fixed_stake_711 * boosted_odds_711
        stake_napoleon = round(payout_711 / odds_napoleon, 2)

        total_investment = self.fixed_stake_711 + stake_napoleon
        net_profit = round(payout_711 - total_investment, 2)

        # We printen ALLES, ook kleine verliezen (zodat je weet dat de engine werkt)
        # In een pure gok-omgeving zet je dit op "> 0"
        if net_profit > -20.0:
            roi = round((net_profit / total_investment) * 100, 2)
            return ArbitrageResult(
                odds_711_base=odds_711,
                odds_711_boosted=round(boosted_odds_711, 2),
                odds_napoleon=odds_napoleon,
                stake_711=self.fixed_stake_711,
                stake_napoleon=stake_napoleon,
                total_investment=round(total_investment, 2),
                guaranteed_payout=round(payout_711, 2),
                net_profit=net_profit,
                roi_percentage=roi
            )
        return None