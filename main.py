"""
AI Anti-Sweep Trading System
Main Entry Point
"""

import logging
import time
from datetime import datetime, timezone
import sys
from pathlib import Path
import MetaTrader5 as mt5
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
import colorama
from colorama import Fore, Back, Style

# Local imports
from price_action_analyzer import PriceActionAnalyzer
from data_handler import DataHandler
from config import SYSTEM_CONFIG
from multi_timeframe_analyzer import MultitimeframeAnalyzer
from volume_analyzer import VolumeAnalyzer
from statistical_analyzer import StatisticalAnalyzer
from velocity_analyzer import VelocityAnalyzer
from microstructure_analyzer import MicrostructureAnalyzer
from market_context_analyzer import MarketContextAnalyzer
from smart_money_analyzer import SmartMoneyAnalyzer
from liquidity_analyzer import LiquidityAnalyzer
from signal_aggregator import SignalAggregator
from trade_executor import TradeExecutor

# Initialize colorama
colorama.init()

class TradingSystem:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        self.initialize_components()
        
    def setup_logging(self):
        """Setup enhanced logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        current_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"trading_{current_time}.log"
        
        # Setup rich console handler
        console = Console()
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                RichHandler(console=console, rich_tracebacks=True),
                logging.FileHandler(log_file)
            ]
        )

    def display_startup_banner(self):
        """Display enhanced startup banner with branding"""
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        banner_text = f"""[bold cyan]
╔══════════════════════════════════════════════════════════════════╗
║                  AI ANTI-SWEEP TRADING SYSTEM                    ║
║                                                                 ║
║  [bright_magenta]▀█▀ ─▀─ █─▄▀ ▀█▀ █▀▀▀█ █─▄▀      [bright_yellow]═ [/][white]KazTan[/][bright_yellow] ═[/]           ║
║  [bright_magenta]─█─ ▀█▀ █▀▄─ ─█─ █───█ █▀▄─                               [/]║
║  [bright_magenta]─▀─ ▀▀▀ ▀──▀ ─▀─ ▀▀▀▀▀ ▀──▀                               [/]║
║                                                                 ║
║  [cyan]System Information:[/]                                           ║
║  └─[white]Date & Time (UTC):[/] [green]{current_time}[/]                     ║
║  └─[white]User Account:[/] [green]{SYSTEM_CONFIG.get('user', 'Kaztanaifreedom')}[/]           ║
║  └─[white]Version:[/] [green]2.0[/]                                         ║
║  └─[white]System Status:[/] [bold green]ACTIVE[/]                                ║
║                                                                 ║
║  [cyan]Trading Details:[/]                                              ║
║  └─[white]Symbol:[/] [green]{SYSTEM_CONFIG['trading']['symbol']}[/]                           ║
╚══════════════════════════════════════════════════════════════════╝[/]"""
        
        # Display banner with loading effect
        with self.console.status("[bold green]Initializing system...", spinner="dots"):
            time.sleep(1)
        
        self.console.print(Panel(banner_text, expand=False))

    def initialize_components(self):
        """Initialize all system components"""
        try:
            with self.console.status("[bold green]Initializing system components..."):
                self.data_handler = DataHandler(SYSTEM_CONFIG)
                self.signal_aggregator = SignalAggregator(SYSTEM_CONFIG)
                self.trade_executor = TradeExecutor(SYSTEM_CONFIG)
                
                self.analyzers = {
                    'multi_timeframe': MultitimeframeAnalyzer(SYSTEM_CONFIG),
                    'volume': VolumeAnalyzer(SYSTEM_CONFIG),
                    'statistical': StatisticalAnalyzer(SYSTEM_CONFIG),
                    'velocity': VelocityAnalyzer(SYSTEM_CONFIG),
                    'microstructure': MicrostructureAnalyzer(SYSTEM_CONFIG),
                    'market_context': MarketContextAnalyzer(SYSTEM_CONFIG),
                    'smart_money': SmartMoneyAnalyzer(SYSTEM_CONFIG),
                    'liquidity': LiquidityAnalyzer(SYSTEM_CONFIG)
                }
                
                self.console.print("[bold green]✓ All components initialized successfully[/]")
                
        except Exception as e:
            self.console.print(f"[bold red]✗ Initialization error: {e}[/]")
            sys.exit(1)

    def check_trading_conditions(self) -> bool:
        """Check if trading conditions are met"""
        try:
            # Get account info
            account_info = self.data_handler.get_account_info()
            if not account_info:
                return False
                
            # Check if we've hit daily loss limit
            daily_loss_limit = SYSTEM_CONFIG['risk_management']['max_daily_loss']
            if account_info['profit'] < -(account_info['balance'] * daily_loss_limit / 100):
                self.logger.warning("Daily loss limit reached")
                return False
            
            # Check if we've hit max daily trades
            today_trades = len(mt5.positions_get())
            if today_trades >= SYSTEM_CONFIG['risk_management']['max_daily_trades']:
                self.logger.warning("Maximum daily trades reached")
                return False
            
            # Check spread
            symbol_info = self.data_handler.get_symbol_info()
            if symbol_info['spread'] > SYSTEM_CONFIG['trading']['max_spread']:
                self.logger.warning(f"Spread too high: {symbol_info['spread']}")
                return False
            
            return True
            
        except Exception as e:
            self.console.print(f"[bold red]✗ Trading conditions check error: {e}[/]")
            return False

    def display_signal_panel(self, signal):
        """Display signal analysis panel with branding"""
        signal_color = {
            "BULLISH": "[bold green]",
            "BEARISH": "[bold red]",
            "NEUTRAL": "[bold yellow]"
        }.get(signal.signal_type, "[white]")
        
        branding = """[bright_magenta]
    ╔══════════════════════════════════════════════════════╗
    ║             Follow My Tiktok : @KazTanai             ║
    ╚══════════════════════════════════════════════════════╝[/]"""
        
        analysis_text = f"""
{branding}

[white]Signal Analysis Results:[/]
├─[white]Type:[/] {signal_color}{signal.signal_type}[/]
├─[white]Score:[/] [bold]{signal.total_score:.1f}/200[/]
└─[white]Valid:[/] [bold {'green' if signal.is_valid else 'red'}]{signal.is_valid}[/]
    """
        
        self.console.print(Panel(
            analysis_text,
            title="[bold cyan]Signal Analysis[/]",
            border_style="blue",
            expand=False
        ))

    def run(self):
        """Main trading loop with enhanced visuals"""
        self.display_startup_banner()
        
        if not self.data_handler.initialize_mt5():
            self.console.print("[bold red]✗ Failed to initialize MT5. Exiting.[/]")
            return
        
        self.console.print(f"[bold green]✓ Connected to MT5. Trading {SYSTEM_CONFIG['trading']['symbol']}[/]")
        
        try:
            while True:
                current_time = datetime.now(timezone.utc)
                self.console.rule(f"[cyan]Analysis Cycle - {current_time.strftime('%Y-%m-%d %H:%M:%S')}[/]")
                
                with self.console.status("[yellow]Checking trading conditions...[/]"):
                    if not self.check_trading_conditions():
                        self.console.print("[yellow]⚠ Trading conditions not met. Waiting 60s...[/]")
                        time.sleep(60)
                        continue
                
                with self.console.status("[cyan]Fetching market data...[/]"):
                    m1_data = self.data_handler.get_ohlcv_data('M1', 2000)
                    tick_data = self.data_handler.get_tick_data(1000)
                    
                    if m1_data.empty or tick_data.empty:
                        self.console.print("[bold red]✗ Failed to get market data. Retrying in 10s...[/]")
                        time.sleep(10)
                        continue
                
                with self.console.status("[cyan]Analyzing market signals...[/]"):
                    signal = self.signal_aggregator.get_aggregated_signal(self.data_handler)
                
                self.display_signal_panel(signal)
                
                if signal.is_valid:
                    with self.console.status("[green]Executing trade...[/]"):
                        result = self.trade_executor.execute_trade(signal)
                    
                    if result['success']:
                        self.console.print(Panel(
                            f"[green]✓ Trade executed successfully[/]\n" +
                            f"Entry: {result['entry']}\n" +
                            f"SL: {result['sl']}\n" +
                            f"TPs: {result['tp_levels']}\n" +
                            f"Volume: {result['volume']}",
                            title="Trade Execution",
                            border_style="green"
                        ))
                    else:
                        self.console.print(f"[bold red]✗ Trade execution failed: {result['message']}[/]")
                
                self.console.print("[cyan]Waiting for next analysis cycle (Wait 4sec)...[/]")
                time.sleep(3)
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠ Received shutdown signal. Closing gracefully...[/]")
            self.data_handler.shutdown()
        except Exception as e:
            self.console.print(f"[bold red]✗ Critical error in main loop: {str(e)}[/]")
            self.data_handler.shutdown()

if __name__ == "__main__":
    system = TradingSystem()
    system.run()