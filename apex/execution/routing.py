"""
Smart Order Router
Routes orders to the best exchange based on price, fees, liquidity, and latency.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from .base import BaseExchange, Order, OrderSide, OrderType, Ticker


class RoutingPriority(Enum):
    PRICE = "price"           # Best execution price
    FEES = "fees"             # Lowest fees
    SPEED = "speed"           # Fastest execution
    RELIABILITY = "reliability"  # Most reliable exchange
    LIQUIDITY = "liquidity"   # Best liquidity


@dataclass
class ExchangeScore:
    """Score for an exchange on a specific metric"""
    exchange: str
    score: float
    metric_value: float
    details: str


@dataclass
class RoutingDecision:
    """Result of routing analysis"""
    symbol: str
    side: OrderSide
    amount: float
    selected_exchange: str
    reason: str
    all_scores: List[ExchangeScore]
    estimated_cost: float
    estimated_fee: float
    timestamp: float


class SmartOrderRouter:
    """
    Intelligent order routing across multiple exchanges.
    
    Features:
    - Price comparison across exchanges
    - Fee optimization
    - Latency monitoring
    - Liquidity analysis
    - Failover support
    """
    
    def __init__(self):
        self.exchanges: Dict[str, BaseExchange] = {}
        self.latency_history: Dict[str, List[float]] = {}
        self.reliability_scores: Dict[str, float] = {}
        self.default_priority = RoutingPriority.PRICE
        
    def add_exchange(self, exchange: BaseExchange) -> bool:
        """Add an exchange to the router"""
        try:
            if exchange.connect():
                self.exchanges[exchange.name] = exchange
                self.reliability_scores[exchange.name] = 1.0
                logging.info(f"Added exchange: {exchange.name}")
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to add exchange {exchange.name}: {e}")
            return False
    
    def remove_exchange(self, name: str) -> bool:
        """Remove an exchange from the router"""
        if name in self.exchanges:
            self.exchanges[name].disconnect()
            del self.exchanges[name]
            return True
        return False
    
    def get_best_exchange(self, symbol: str, side: OrderSide,
                          amount: float,
                          priority: RoutingPriority = None) -> RoutingDecision:
        """
        Determine the best exchange for an order.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: Buy or sell
            amount: Order size
            priority: Optimization priority
            
        Returns:
            RoutingDecision with selected exchange and analysis
        """
        priority = priority or self.default_priority
        
        # Collect data from all exchanges
        exchange_data = self._collect_exchange_data(symbol)
        
        if not exchange_data:
            raise ValueError("No exchanges available for routing")
        
        # Score each exchange
        scores = []
        
        for name, data in exchange_data.items():
            try:
                score = self._score_exchange(
                    name, data, side, amount, priority
                )
                scores.append(score)
            except Exception as e:
                logging.warning(f"Failed to score {name}: {e}")
        
        if not scores:
            raise ValueError("Could not score any exchanges")
        
        # Sort by score (higher is better)
        scores.sort(key=lambda x: x.score, reverse=True)
        
        # Select best exchange
        best = scores[0]
        
        # Calculate estimated costs
        ticker = exchange_data[best.exchange]['ticker']
        price = ticker.ask if side == OrderSide.BUY else ticker.bid
        base_cost = amount * price
        
        exchange = self.exchanges[best.exchange]
        fees = exchange.get_fees()
        fee_rate = fees.taker  # Conservative estimate
        estimated_fee = base_cost * fee_rate
        estimated_cost = base_cost + estimated_fee
        
        return RoutingDecision(
            symbol=symbol,
            side=side,
            amount=amount,
            selected_exchange=best.exchange,
            reason=best.details,
            all_scores=scores,
            estimated_cost=estimated_cost,
            estimated_fee=estimated_fee,
            timestamp=time.time()
        )
    
    def _collect_exchange_data(self, symbol: str) -> Dict[str, dict]:
        """Collect ticker and fee data from all exchanges"""
        data = {}
        
        for name, exchange in self.exchanges.items():
            try:
                start = time.time()
                ticker = exchange.get_ticker(symbol)
                latency = time.time() - start
                
                # Update latency history
                if name not in self.latency_history:
                    self.latency_history[name] = []
                self.latency_history[name].append(latency)
                # Keep last 100 measurements
                self.latency_history[name] = self.latency_history[name][-100:]
                
                fees = exchange.get_fees()
                spread = exchange.get_spread(symbol)
                
                data[name] = {
                    'ticker': ticker,
                    'fees': fees,
                    'spread': spread,
                    'latency': latency,
                    'reliability': self.reliability_scores.get(name, 1.0)
                }
                
            except Exception as e:
                logging.warning(f"Failed to get data from {name}: {e}")
                # Reduce reliability score on failure
                self.reliability_scores[name] = max(
                    0.1, self.reliability_scores.get(name, 1.0) * 0.9
                )
        
        return data
    
    def _score_exchange(self, name: str, data: dict, side: OrderSide,
                        amount: float, priority: RoutingPriority) -> ExchangeScore:
        """Score an exchange based on priority"""
        
        ticker = data['ticker']
        fees = data['fees']
        
        if priority == RoutingPriority.PRICE:
            # Lower price for buying, higher for selling
            if side == OrderSide.BUY:
                score = 1.0 / ticker.ask  # Lower ask = higher score
                metric = ticker.ask
                details = f"Best ask price: ${ticker.ask:,.2f}"
            else:
                score = ticker.bid  # Higher bid = higher score
                metric = ticker.bid
                details = f"Best bid price: ${ticker.bid:,.2f}"
                
        elif priority == RoutingPriority.FEES:
            # Lower fees = higher score
            score = 1.0 / (1 + fees.taker * 1000)
            metric = fees.taker
            details = f"Lowest fee: {fees.taker*100:.3f}%"
            
        elif priority == RoutingPriority.SPEED:
            # Lower latency = higher score
            avg_latency = sum(self.latency_history.get(name, [0.1])) / \
                         max(1, len(self.latency_history.get(name, [0.1])))
            score = 1.0 / (1 + avg_latency * 10)
            metric = avg_latency
            details = f"Lowest latency: {avg_latency*1000:.1f}ms"
            
        elif priority == RoutingPriority.LIQUIDITY:
            # Higher volume = higher score
            score = min(1.0, ticker.volume / 1000000)  # Normalize to 1M
            metric = ticker.volume
            details = f"Best liquidity: ${ticker.volume:,.0f} volume"
            
        else:  # RELIABILITY
            score = data['reliability']
            metric = data['reliability']
            details = f"Reliability: {data['reliability']*100:.1f}%"
        
        # Apply reliability penalty
        score *= data['reliability']
        
        return ExchangeScore(
            exchange=name,
            score=score,
            metric_value=metric,
            details=details
        )
    
    def route_order(self, order: Order,
                    priority: RoutingPriority = None) -> Tuple[Order, RoutingDecision]:
        """
        Route an order to the best exchange.
        
        Returns:
            Tuple of (executed_order, routing_decision)
        """
        # Get routing decision
        decision = self.get_best_exchange(
            order.symbol,
            order.side,
            order.amount,
            priority
        )
        
        # Execute on selected exchange
        exchange = self.exchanges[decision.selected_exchange]
        order.exchange = decision.selected_exchange
        
        try:
            executed = exchange.place_order(order)
            
            # Update reliability on success
            self.reliability_scores[decision.selected_exchange] = min(
                1.0, self.reliability_scores.get(decision.selected_exchange, 1.0) * 1.05
            )
            
            return executed, decision
            
        except Exception as e:
            logging.error(f"Order failed on {decision.selected_exchange}: {e}")
            
            # Try failover to next best exchange
            for score in decision.all_scores[1:]:
                try:
                    backup_exchange = self.exchanges[score.exchange]
                    order.exchange = score.exchange
                    executed = backup_exchange.place_order(order)
                    
                    logging.info(f"Failover successful to {score.exchange}")
                    decision.selected_exchange = score.exchange
                    decision.reason += f" (failover from {decision.selected_exchange})"
                    
                    return executed, decision
                    
                except Exception as e2:
                    logging.error(f"Failover to {score.exchange} failed: {e2}")
            
            raise Exception("Order failed on all exchanges")
    
    def get_arbitrage_opportunities(self, symbol: str,
                                     min_profit_percent: float = 0.1) -> List[Dict]:
        """
        Find arbitrage opportunities across exchanges.
        
        Returns list of opportunities with buy_exchange, sell_exchange, profit %
        """
        data = self._collect_exchange_data(symbol)
        opportunities = []
        
        exchanges = list(data.keys())
        
        for i, buy_ex in enumerate(exchanges):
            for sell_ex in exchanges[i+1:]:
                buy_price = data[buy_ex]['ticker'].ask
                sell_price = data[sell_ex]['ticker'].bid
                
                # Account for fees
                buy_fee = data[buy_ex]['fees'].taker
                sell_fee = data[sell_ex]['fees'].taker
                
                gross_profit = (sell_price - buy_price) / buy_price * 100
                net_profit = gross_profit - (buy_fee + sell_fee) * 100
                
                if net_profit > min_profit_percent:
                    opportunities.append({
                        'buy_exchange': buy_ex,
                        'sell_exchange': sell_ex,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'gross_profit_pct': gross_profit,
                        'net_profit_pct': net_profit,
                        'symbol': symbol
                    })
        
        return sorted(opportunities, key=lambda x: x['net_profit_pct'], reverse=True)
    
    def get_exchange_status(self) -> Dict[str, dict]:
        """Get status of all exchanges"""
        status = {}
        
        for name, exchange in self.exchanges.items():
            try:
                is_connected = exchange.is_connected()
                avg_latency = 0
                if name in self.latency_history and self.latency_history[name]:
                    avg_latency = sum(self.latency_history[name]) / len(self.latency_history[name])
                
                status[name] = {
                    'connected': is_connected,
                    'reliability': self.reliability_scores.get(name, 1.0),
                    'avg_latency_ms': avg_latency * 1000,
                    'symbols_count': len(exchange.get_symbols())
                }
            except Exception as e:
                status[name] = {
                    'connected': False,
                    'error': str(e)
                }
        
        return status
