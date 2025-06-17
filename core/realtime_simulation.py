"""
Real-time blockchain data simulation for demonstration purposes.
Generates realistic-looking fraudulent money movement patterns.
"""

import random
import time
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Tuple
import json
import threading
import logging

logger = logging.getLogger(__name__)


class BlockchainSimulator:
    """
    Simulates real-time blockchain data for multiple chains.
    Creates patterns that look like actual fraudulent activity.
    """
    
    def __init__(self):
        self.chains = {
            'ethereum': {
                'name': 'Ethereum',
                'color': '#627EEA',
                'base_balance': 2500000,  # $2.5M
                'volatility': 0.15,
                'trend': 0.02,  # 2% upward trend per day
            },
            'arbitrum': {
                'name': 'Arbitrum',
                'color': '#28A0F0', 
                'base_balance': 850000,  # $850K
                'volatility': 0.20,
                'trend': -0.01,  # -1% downward trend (money flowing out)
            },
            'optimism': {
                'name': 'Optimism',
                'color': '#FF0420',
                'base_balance': 450000,  # $450K
                'volatility': 0.25,
                'trend': 0.05,  # 5% upward trend (receiving funds)
            },
            'polygon': {
                'name': 'Polygon',
                'color': '#8247E5',
                'base_balance': 1200000,  # $1.2M
                'volatility': 0.18,
                'trend': -0.03,  # -3% downward trend (bridge to other chains)
            }
        }
        
        # Simulation state
        self.current_time = datetime.now()
        self.simulation_speed = 1  # Real-time (1 second = 1 second)
        self.running = False
        self.thread = None
        
        # Data history for charts
        self.balance_history = {chain: [] for chain in self.chains}
        self.volume_history = {chain: [] for chain in self.chains}
        self.transaction_events = []
        
        # Fraud pattern simulation
        self.fraud_patterns = {
            'mixing_cycles': [],  # Times when mixing occurs
            'large_transfers': [],  # Suspicious large transfers
            'bridge_events': [],  # Cross-chain bridge activity
        }
        
    def start_simulation(self):
        """Start the real-time simulation in a background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        logger.info("Blockchain simulation started")
        
    def stop_simulation(self):
        """Stop the real-time simulation."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Blockchain simulation stopped")
        
    def _simulation_loop(self):
        """Main simulation loop that generates data every second."""
        while self.running:
            try:
                self._generate_tick_data()
                time.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                
    def _generate_tick_data(self):
        """Generate one tick of simulation data."""
        self.current_time += timedelta(seconds=self.simulation_speed)
        
        # Generate balance updates for each chain
        for chain_id, chain_config in self.chains.items():
            balance = self._calculate_chain_balance(chain_id, chain_config)
            volume = self._calculate_chain_volume(chain_id, chain_config)
            
            # Store data point
            data_point = {
                'timestamp': self.current_time.isoformat(),
                'balance': balance,
                'volume': volume,
                'chain': chain_id
            }
            
            self.balance_history[chain_id].append(data_point)
            self.volume_history[chain_id].append(data_point)
            
            # Keep only last 200 data points per chain (for longer timeframes)
            if len(self.balance_history[chain_id]) > 200:
                self.balance_history[chain_id].pop(0)
            if len(self.volume_history[chain_id]) > 200:
                self.volume_history[chain_id].pop(0)
                
        # Generate fraud events occasionally
        if random.random() < 0.1:  # 10% chance per tick
            self._generate_fraud_event()
            
    def _calculate_chain_balance(self, chain_id: str, config: Dict) -> float:
        """Calculate current balance for a chain with realistic patterns."""
        base = config['base_balance']
        volatility = config['volatility']
        trend = config['trend']
        
        # Use seconds for more dynamic changes
        seconds_elapsed = self.current_time.second + (self.current_time.microsecond / 1000000)
        
        # Create a wave pattern for more visible changes
        wave = math.sin(seconds_elapsed * 0.1) * 0.05  # 5% wave amplitude
        
        # Time-based trend (smaller scale for seconds)
        trend_factor = 1 + (trend * seconds_elapsed / 3600)
        
        # Random volatility with higher frequency
        random_factor = 1 + random.gauss(0, volatility * 0.02)
        
        # Fraud pattern influences
        fraud_factor = self._get_fraud_influence(chain_id)
        
        balance = base * trend_factor * random_factor * fraud_factor * (1 + wave)
        return max(balance, 0)  # Never negative
        
    def _calculate_chain_volume(self, chain_id: str, config: Dict) -> float:
        """Calculate transaction volume for a chain."""
        base_volume = config['base_balance'] * 0.1  # 10% of balance as daily volume
        
        # Higher volume during fraud events
        fraud_multiplier = 1.0
        if self._is_fraud_active(chain_id):
            fraud_multiplier = random.uniform(2.0, 5.0)
            
        # Random variation
        random_factor = random.uniform(0.5, 2.0)
        
        volume = base_volume * fraud_multiplier * random_factor / 24  # Per hour
        return volume
        
    def _get_fraud_influence(self, chain_id: str) -> float:
        """Get fraud pattern influence on balance."""
        # Ethereum often receives mixed funds (higher balance during mixing)
        if chain_id == 'ethereum' and self._is_mixing_active():
            return random.uniform(1.1, 1.3)
            
        # Arbitrum and Polygon lose funds during bridging
        if chain_id in ['arbitrum', 'polygon'] and self._is_bridge_active():
            return random.uniform(0.8, 0.95)
            
        # Optimism receives bridged funds
        if chain_id == 'optimism' and self._is_bridge_active():
            return random.uniform(1.05, 1.2)
            
        return 1.0
        
    def _is_fraud_active(self, chain_id: str) -> bool:
        """Check if fraud activity is currently active for a chain."""
        return random.random() < 0.15  # 15% chance
        
    def _is_mixing_active(self) -> bool:
        """Check if mixing activity is currently active."""
        return random.random() < 0.08  # 8% chance
        
    def _is_bridge_active(self) -> bool:
        """Check if bridge activity is currently active."""
        return random.random() < 0.12  # 12% chance
        
    def _generate_fraud_event(self):
        """Generate a fraud event for the transaction log."""
        event_types = [
            'large_transfer',
            'mixing_service',
            'bridge_transaction',
            'tumbler_activity',
            'multiple_small_transfers'
        ]
        
        event_type = random.choice(event_types)
        chain = random.choice(list(self.chains.keys()))
        
        event = {
            'timestamp': self.current_time.isoformat(),
            'type': event_type,
            'chain': chain,
            'amount': random.uniform(10000, 500000),
            'suspicious_score': random.uniform(0.7, 1.0),
            'description': self._get_event_description(event_type)
        }
        
        self.transaction_events.append(event)
        
        # Keep only last 50 events
        if len(self.transaction_events) > 50:
            self.transaction_events.pop(0)
            
    def _get_event_description(self, event_type: str) -> str:
        """Get description for fraud event type."""
        descriptions = {
            'large_transfer': 'Large transfer detected between flagged addresses',
            'mixing_service': 'Interaction with known mixing service',
            'bridge_transaction': 'Cross-chain bridge transaction',
            'tumbler_activity': 'Possible tumbler/privacy coin interaction',
            'multiple_small_transfers': 'Multiple small transfers (possible structuring)'
        }
        return descriptions.get(event_type, 'Suspicious activity detected')
        
    def get_current_data(self, timeframe: str = '1M') -> Dict[str, Any]:
        """Get current simulation data for charts."""
        # Determine how many data points to return based on timeframe
        points_map = {
            '1M': 30,    # Last 30 seconds (1 minute)
            '5M': 60,    # Last 60 seconds (5 minutes)
            '30M': 90    # Last 90 seconds (30 minutes)
        }
        
        num_points = points_map.get(timeframe, 30)
        
        # Generate labels for the timeframe
        if timeframe == '1M':
            labels = [f"{i}s" for i in range(num_points, 0, -1)]
        elif timeframe == '5M':
            labels = [f"{i}s" for i in range(num_points*5, 0, -5)][:num_points]
        else:  # 30M
            labels = [f"{i}m" for i in range(30, 0, -1)][:num_points]
            
        # Get recent data for each chain
        multi_chain_data = {}
        for chain_id in self.chains:
            balance_data = self.balance_history[chain_id][-num_points:] if self.balance_history[chain_id] else []
            volume_data = self.volume_history[chain_id][-num_points:] if self.volume_history[chain_id] else []
            
            # Pad with zeros if not enough data
            while len(balance_data) < num_points:
                balance_data.insert(0, {'balance': self.chains[chain_id]['base_balance'], 'volume': 0})
            while len(volume_data) < num_points:
                volume_data.insert(0, {'balance': self.chains[chain_id]['base_balance'], 'volume': 0})
                
            multi_chain_data[chain_id] = {
                'balances': [d['balance'] for d in balance_data[-num_points:]],
                'volume': [d['volume'] for d in volume_data[-num_points:]]
            }
            
        # Calculate summary stats
        total_balance = sum(
            multi_chain_data[chain]['balances'][-1] if multi_chain_data[chain]['balances'] else 0
            for chain in multi_chain_data
        )
        
        previous_balance = sum(
            multi_chain_data[chain]['balances'][-2] if len(multi_chain_data[chain]['balances']) > 1 else multi_chain_data[chain]['balances'][-1] if multi_chain_data[chain]['balances'] else 0
            for chain in multi_chain_data
        )
        
        change_percent = ((total_balance - previous_balance) / previous_balance * 100) if previous_balance > 0 else 0
        
        return {
            'success': True,
            'timeframe': timeframe,
            'labels': labels,
            'multi_chain_data': multi_chain_data,
            'summary': {
                'total_balance': total_balance,
                'change_percent': f"{change_percent:+.2f}",
                'chains_tracked': len(self.chains),
                'fraud_events': len([e for e in self.transaction_events if 
                                   datetime.fromisoformat(e['timestamp']) > self.current_time - timedelta(hours=24)])
            },
            'recent_events': self.transaction_events[-5:],  # Last 5 fraud events
            'simulation_time': self.current_time.strftime("%H:%M:%S")
        }


# Global simulator instance
_simulator = None

def get_simulator() -> BlockchainSimulator:
    """Get the global simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = BlockchainSimulator()
        _simulator.start_simulation()
    return _simulator

def stop_global_simulator():
    """Stop the global simulator."""
    global _simulator
    if _simulator:
        _simulator.stop_simulation()
        _simulator = None