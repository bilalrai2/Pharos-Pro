from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from eth_abi.abi import encode
from web3 import Web3
from colorama import *
from datetime import datetime
import asyncio, random, secrets, time, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class PharosTestnet:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://testnet.pharosnetwork.xyz",
            "Referer": "https://testnet.pharosnetwork.xyz/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://api.pharosnetwork.xyz"
        self.RPC_URL = "https://testnet.dplabs-internal.com"
        self.PHRS_CONTRACT_ADDRESS = "0xf6a07fe10e28a70d1b0f36c7eb7745d2bae2a312"
        self.WPHRS_CONTRACT_ADDRESS = "0x76aaada469d23216be5f7c596fa25f282ff9b364"
        self.USDC_CONTRACT_ADDRESS = "0xad902cf99c2de2f1ba5ec4d642fd7e49cae9ee37"
        self.SWAP_CONTRACT_ROUTER = "0x1a4de519154ae51200b0ad7c90f7fac75547888a"
        self.ERC20_CONTRACT_ABI = [
            {
                "constant": True,
                "inputs": [
                    { "name": "owner", "type": "address" }
                ],
                "name": "balanceOf",
                "outputs": [
                    { "name": "", "type": "uint256" }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [
                    { "name": "", "type": "uint8" }
                ],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    { "name": "spender", "type": "address" },
                    { "name": "value", "type": "uint256" }
                ],
                "name": "approve",
                "outputs": [
                    { "name": "", "type": "bool" }
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    { "name": "owner", "type": "address" },
                    { "name": "spender", "type": "address" }
                ],
                "name": "allowance",
                "outputs": [
                    { "name": "", "type": "uint256" }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    { "name": "wad", "type": "uint256" }
                ],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.MULTICALL_CONTRACT_ABI = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "collectionAndSelfcalls", "type": "uint256"},
                    {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
                ],
                "name": "multicall",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        ]
        self.ref_code = "PNFXEcz1CWezuu3g" # U can change it with yours.
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Pharos Testnet{Fore.BLUE + Style.BRIGHT} Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT} Telegram Channel {Fore.YELLOW + Style.BRIGHT} > https://t.me/AllAirdropScript
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            return ValueError("Generate EVM Address Failed")
        
    def generate_random_receiver(self):
        try:
            private_key_bytes = secrets.token_bytes(32)
            private_key_hex = to_hex(private_key_bytes)
            account = Account.from_key(private_key_hex)
            receiver = account.address
            
            return receiver
        except Exception as e:
            return None
        
    def generate_url_login(self, account: str, address: str):
        try:
            encoded_message = encode_defunct(text="pharos")
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            url_login = f"{self.BASE_API}/user/login?address={address}&signature={signature}&invite_code={self.ref_code}"
            return url_login
        except Exception as e:
            return ValueError("Generate Signature Failed")
        
    def get_token_balance(self, address: str, contract_address: str):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        try:
            if contract_address == "PHRS":
                balance = web3.eth.get_balance(address)
                decimals = 18
            else:
                token_contract = web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
                decimals = token_contract.functions.decimals().call()
                balance = token_contract.functions.balanceOf(address).call()

            token_balance = balance / (10 ** decimals)

            return token_balance
        except Exception as e:
            return None
    
    def get_multicall_data(self, address: str, from_contract_address: str, to_contract_address: str, swap_amount: str):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        try:
            data = encode(
                ['address', 'address', 'uint256', 'address', 'uint256', 'uint256', 'uint256'],
                [
                    web3.to_checksum_address(from_contract_address),
                    web3.to_checksum_address(to_contract_address),
                    500,
                    web3.to_checksum_address(address),
                    web3.to_wei(swap_amount, "ether"),
                    0,
                    0
                ]
            )
            return [b'\x04\xe4\x5a\xaf' + data]
        except Exception as e:
            self.log(str(e))
            return []
        
    async def perform_transfer(self, account: str, address: str, receiver: str, amount: float):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        try:
            txn = {
                "to": receiver,
                "value": web3.to_wei(amount, "ether"),
                "nonce": web3.eth.get_transaction_count(address),
                "gas": 21000,
                "gasPrice": web3.eth.gas_price,
                "chainId": web3.eth.chain_id
            }

            signed_tx = web3.eth.account.sign_transaction(txn, account)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            return None, None
        
    async def perform_wrapped(self, account: str, address: str, amount: float):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        contract_address = web3.to_checksum_address(self.WPHRS_CONTRACT_ADDRESS)
        contract = web3.eth.contract(address=contract_address, abi=self.ERC20_CONTRACT_ABI)
        try:
            amount_to_wei = web3.to_wei(amount, "ether")
            txn = contract.functions.deposit().build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": 50000,
                "gasPrice": web3.eth.gas_price,
                "nonce": web3.eth.get_transaction_count(address)
            })

            signed_tx = web3.eth.account.sign_transaction(txn, account)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            return None, None
        
    async def perform_unwrapped(self, account: str, address: str, amount: float):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        contract_address = web3.to_checksum_address(self.WPHRS_CONTRACT_ADDRESS)
        contract = web3.eth.contract(address=contract_address, abi=self.ERC20_CONTRACT_ABI)
        try:
            amount_to_wei = web3.to_wei(amount, "ether")
            txn = contract.functions.withdraw(amount_to_wei).build_transaction({
                "from": address,
                "gas": 50000,
                "gasPrice": web3.eth.gas_price,
                "nonce": web3.eth.get_transaction_count(address)
            })

            signed_tx = web3.eth.account.sign_transaction(txn, account)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            return None, None
        
    async def approving_swap(self, account: str, address: str, contract_address: str):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        swap_router = web3.to_checksum_address(self.SWAP_CONTRACT_ROUTER)
        token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
        try:
            approve_tx = token_contract.functions.approve(swap_router, 2**256 - 1).build_transaction({
                "from": address,
                "gas": 50000,
                "gasPrice": web3.eth.gas_price,
                "nonce": web3.eth.get_transaction_count(address)
            })

            signed_tx = web3.eth.account.sign_transaction(approve_tx, account)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber
        
            return True
        except Exception as e:
            return self.log(str(e))
        
    async def perform_swap(self, account: str, address: str, multicall_data: list):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        contract = web3.eth.contract(address=Web3.to_checksum_address(self.SWAP_CONTRACT_ROUTER), abi=self.MULTICALL_CONTRACT_ABI)
        try:
            tx_data = contract.functions.multicall(int(time.time()), multicall_data)
            estimated_gas = tx_data.estimate_gas({"from": address})

            tx = contract.functions.multicall(int(time.time()), multicall_data).build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "gasPrice": web3.eth.gas_price,
                "nonce": web3.eth.get_transaction_count(address)
            })
            signed_tx = web3.eth.account.sign_transaction(tx, account)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            return None, None
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account 
    
    async def print_timer(self, delay=random.randint(15, 20)):
        for remaining in range(delay, 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        tx_count = 0
        tx_amount = 0
        wrap_amount = 0
        swap_count = 0
        wrap_option = None
        rotate = False

        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Check-In, Claim Faucet, and Send to Friends{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Wrapped PHRS to WPHRS - Unwrapped WPHRS to PHRS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Swap WPHRS to USDC - USDC to WPHRS{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3/4] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4]:
                    option_type = (
                        "Check-In, Claim Faucet, and Send to Friends" if option == 1 else 
                        "Wrapped PHRS to WPHRS" if option == 2 else 
                        "Swap WPHRS to USDC - USDC to WPHRS" if option == 3 else
                        "Run All Features"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, or 4.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, or 4).{Style.RESET_ALL}")

        if option == 1:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    tx_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if tx_amount > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive amount.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

        elif option == 2:
            while True:
                try:
                    print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}1. Wrapped PHRS to WPHRS{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}2. Unwrapped WPHRS to PHRS{Style.RESET_ALL}")
                    wrap_option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                    if wrap_option in [1, 2]:
                        wrap_type = (
                            "Wrapped PHRS to WPHRS" if wrap_option == 1 else 
                            "Unwrapped WPHRS to PHRS"
                        )
                        print(f"{Fore.GREEN + Style.BRIGHT}{wrap_type} Selected.{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

            while True:
                try:
                    wrap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Amount [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if wrap_amount > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive amount.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

        elif option == 3:
            while True:
                try:
                    swap_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Swap? -> {Style.RESET_ALL}").strip())
                    if swap_count > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        elif option == 4:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    tx_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if tx_amount > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive amount.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}1. Wrapped PHRS to WPHRS{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}2. Unwrapped WPHRS to PHRS{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}3. Skipped{Style.RESET_ALL}")
                    wrap_option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                    if wrap_option in [1, 2, 3]:
                        wrap_type = (
                            "Wrapped PHRS to WPHRS" if wrap_option == 1 else 
                            "Unwrapped WPHRS to PHRS" if wrap_option == 2 else
                            "Skipped"
                        )
                        print(f"{Fore.GREEN + Style.BRIGHT}{wrap_type} Selected.{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, or 3.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, or 3).{Style.RESET_ALL}")

            if wrap_option in [1, 2]:
                while True:
                    try:
                        wrap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Amount [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                        if wrap_amount > 0:
                            break
                        else:
                            print(f"{Fore.RED + Style.BRIGHT}Please enter positive amount.{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    swap_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Swap? -> {Style.RESET_ALL}").strip())
                    if swap_count > 0:
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
        
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Monosans Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, tx_count, tx_amount, wrap_option, wrap_amount, swap_count, choose, rotate
    
    async def check_connection(self, proxy=None):
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://testnet.pharosnetwork.xyz", headers={}) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            return None
    
    async def user_login(self, url_login: str, proxy=None, retries=5):
        headers = {
            **self.headers,
            "Authorization": "Bearer null",
            "Content-Length": "0"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url_login, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]["jwt"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def user_profile(self, address: str, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/user/profile?address={address}"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def sign_in(self, address: str, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/sign/in?address={address}"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": "0"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def faucet_status(self, address: str, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/faucet/status?address={address}"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def claim_faucet(self, address: str, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/faucet/daily?address={address}"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": "0"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def send_to_friends(self, address: str, token: str, tx_hash: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/task/verify?address={address}&task_id=103&tx_hash={tx_hash}"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": "0"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        message = "Checking Connection, Wait..."
        if use_proxy:
            message = "Checking Proxy Connection, Wait..."

        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}{message}{Style.RESET_ALL}",
            end="\r",
            flush=True
        )

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if rotate_proxy:
            is_valid = None
            while is_valid is None:
                is_valid = await self.check_connection(proxy)
                if not is_valid:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Not 200 OK, {Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT}Rotating Proxy...{Style.RESET_ALL}"
                    )
                    proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                    await asyncio.sleep(5)
                    continue

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} 200 OK {Style.RESET_ALL}                  "
                )

                return True

        is_valid = await self.check_connection(proxy)
        if not is_valid:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Not 200 OK {Style.RESET_ALL}          "
            )
            return False
        
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} 200 OK {Style.RESET_ALL}                  "
        )

        return True
        
    async def process_user_login(self, address: str, url_login: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        token = await self.user_login(url_login, proxy)
        if not token:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
            )
            return
        
        return token
    
    async def process_perform_transfer(self, account: str, address: str, token: str, receiver: str, tx_amount: float, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        tx_hash, block_number = await self.perform_transfer(account, address, receiver, tx_amount)
        if tx_hash and block_number:
            send = await self.send_to_friends(address, token, tx_hash, proxy)
            if send and send.get("msg") == "task verified successfully":
                explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Transfer Verified Successfully {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
                )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Verify Transfer Failed {Style.RESET_ALL}"
                )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_wrapped(self, account: str, address: str, wrap_amount: float):
        tx_hash, block_number = await self.perform_wrapped(account, address, wrap_amount)
        if tx_hash and block_number:
            explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Wrapped {wrap_amount} PHRS to WPHRS Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_unwrapped(self, account: str, address: str, wrap_amount: float):
        tx_hash, block_number = await self.perform_unwrapped(account, address, wrap_amount)
        if tx_hash and block_number:
            explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Unwrapped {wrap_amount} WPHRS to PHRS Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_perform_swap(self, account: str, address: str, from_contract_address: str, to_contract_address: str, from_token: str, to_token: str, swap_amount: float):
        approve = await self.approving_swap(account, address, from_contract_address)
        if approve:
            multicall_data = self.get_multicall_data(address, from_contract_address, to_contract_address, swap_amount)
            if multicall_data:
                tx_hash, block_number = await self.perform_swap(account, address, multicall_data)
                if tx_hash and block_number:
                    explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} Swap {swap_amount} {from_token} to {to_token} Success {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                    )
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
                    )
                else:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
                    )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} GET Multicall Data Failed {Style.RESET_ALL}"
                )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Approving Swap Failed {Style.RESET_ALL}"
            )

    async def process_option_1(self, account: str, address: str, url_login: str, tx_count: int, tx_amount: float, use_proxy: bool):
        token = await self.process_user_login(address, url_login, use_proxy)
        if token:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

            points = "N/A"
            profile = await self.user_profile(address, token, proxy)
            if profile and profile.get("msg") == "ok":
                points = profile.get("data", {}).get("user_info", {}).get("TotalPoints", 0)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Balance   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {points} PTS {Style.RESET_ALL}"
            )

            sign_in = await self.sign_in(address, token, proxy)
            if sign_in and sign_in.get("msg") == "ok":
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Claimed Successfully {Style.RESET_ALL}"
                )
            elif sign_in and sign_in.get("msg") == "already signed in today":
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                )

            faucet_status = await self.faucet_status(address, token, proxy)
            if faucet_status and faucet_status.get("msg") == "ok":
                is_able = faucet_status.get("data", {}).get("is_able_to_faucet", False)

                if is_able:
                    claim = await self.claim_faucet(address, token, proxy)
                    if claim and claim.get("msg") == "ok":
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} 0.2 PHRS {Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT}Claimed Successfully{Style.RESET_ALL}"
                        )
                    else:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                            f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                        )
                else:
                    faucet_available_ts = faucet_status.get("data", {}).get("avaliable_timestamp", None)
                    faucet_available_wib = datetime.fromtimestamp(faucet_available_ts).astimezone(wib).strftime('%x %X %Z')
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT} Available at: {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{faucet_available_wib}{Style.RESET_ALL}"
                    )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Faucet    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} GET Eligibility Status Failed {Style.RESET_ALL}"
                )

            self.log(f"{Fore.CYAN+Style.BRIGHT}Transfer  :{Style.RESET_ALL}")
            await asyncio.sleep(5)

            for i in range(tx_count):
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT}Tx - {i+1}{Style.RESET_ALL}"
                )
                receiver = self.generate_random_receiver()
                balance = self.get_token_balance(address, "PHRS")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {balance} PHRS {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_amount} PHRS {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Receiver:{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {receiver} {Style.RESET_ALL}"
                )

                if balance <= tx_amount:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Insufficient PHRS balance {Style.RESET_ALL}"
                    )
                    break

                await self.process_perform_transfer(account, address, token, receiver, tx_amount, use_proxy)
                await asyncio.sleep(2)

    async def process_option_2(self, account: str, address: str, wrap_option: int, wrap_amount: float):
        if wrap_option == 1:
            self.log(f"{Fore.CYAN+Style.BRIGHT}Wrapped   :{Style.RESET_ALL}")
            balance = self.get_token_balance(address, "PHRS")
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} PHRS {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {wrap_amount} PHRS {Style.RESET_ALL}"
            )

            if balance <= wrap_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient PHRS balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_wrapped(account, address, wrap_amount)
        
        elif wrap_option == 2:
            self.log(f"{Fore.CYAN+Style.BRIGHT}Unwrapped :{Style.RESET_ALL}")
            balance = self.get_token_balance(address, self.WPHRS_CONTRACT_ADDRESS)
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} WPHRS {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {wrap_amount} WPHRS {Style.RESET_ALL}"
            )

            if balance < wrap_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient WPHRS balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_unwrapped(account, address, wrap_amount)

    async def process_option_3(self, account: str, address: str, swap_count: int):
        for i in range(swap_count):
            self.log(
                f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT}Swap{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {i+1} / {swap_count} {Style.RESET_ALL}                           "
            )
            for swap_option in ["WPHRStoUSDC", "USDCtoWPHRS"]:
                from_contract_address = self.WPHRS_CONTRACT_ADDRESS if swap_option == "WPHRStoUSDC" else self.USDC_CONTRACT_ADDRESS
                to_contract_address = self.USDC_CONTRACT_ADDRESS if swap_option == "WPHRStoUSDC" else self.WPHRS_CONTRACT_ADDRESS
                from_token = "WPHRS" if swap_option == "WPHRStoUSDC" else "USDC"
                to_token = "USDC" if swap_option == "WPHRStoUSDC" else "WPHRS"
                swap_amount = 0.005 if swap_option == "WPHRStoUSDC" else 1.5

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Type    :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {from_token} - {to_token} {Style.RESET_ALL}                "
                )

                balance = self.get_token_balance(address, from_contract_address)
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {balance} {from_token} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {swap_amount} {from_token} {Style.RESET_ALL}"
                )

                if balance <= swap_amount:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Insufficient {from_token} balance {Style.RESET_ALL}"
                    )
                    break

                await self.process_perform_swap(account, address, from_contract_address, to_contract_address, from_token, to_token, swap_amount)
                await self.print_timer()

            await asyncio.sleep(2)

    async def process_accounts(self, account: str, address: str, url_login: str, option: int, tx_count: int, tx_amount: float, wrap_option: int, wrap_amount: float, swap_count: int, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:

            if option == 1:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Check-In, Claim Faucet, and Send to Friends {Style.RESET_ALL}"
                )

                await self.process_option_1(account, address, url_login, tx_count, tx_amount, use_proxy)

            elif option == 2:
                wrap_type = "Wrapped PHRS to WPHRS" if wrap_option == 1 else "Unwrapped WPHRS to PHRS"
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} {wrap_type} {Style.RESET_ALL}"
                )
                
                await self.process_option_2(account, address, wrap_option, wrap_amount)

            elif option == 3:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Swap WPHRS to USDC - USDC to WPHRS {Style.RESET_ALL}"
                )

                await self.process_option_3(account, address, swap_count)

            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Option    :{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} Run All Features {Style.RESET_ALL}"
                )

                await self.process_option_1(account, address, url_login, tx_count, tx_amount, use_proxy)
                await asyncio.sleep(3)

                await self.process_option_2(account, address, wrap_option, wrap_amount)
                await asyncio.sleep(3)

                await self.process_option_3(account, address, swap_count)
                await asyncio.sleep(3)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            option, tx_count, tx_amount, wrap_option, wrap_amount, swap_count, use_proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice in [1, 2]:
                    use_proxy = True

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        if address:
                            url_login = self.generate_url_login(account, address)

                            if url_login:
                                self.log(
                                    f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                                    f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                                )
                                await self.process_accounts(account, address, url_login, option, tx_count, tx_amount, wrap_option, wrap_amount, swap_count, use_proxy, rotate_proxy)
                                await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = PharosTestnet()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Pharos Testnet - BOT{Style.RESET_ALL}                                       "                              
        )