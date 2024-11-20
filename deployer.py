import json
import os
import re
import sys
import webbrowser
from tkinter import *
from tkinter import Button, BOTH
from tkinter import Toplevel, Frame
from tkinter import messagebox, simpledialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import requests
import solcx
from eth_account import Account
from solcx import exceptions
from web3 import Web3


class CustomDialog(simpledialog.Dialog):

    def __init__(self, parent, title, prompt, initialvalue=None):
        self.result = None
        self.entry = None
        self.parent = None
        self.prompt = prompt
        self.initialvalue = initialvalue
        super().__init__(parent, title)

    def body(self, master):
        Label(master, text=self.prompt).pack(padx=5, pady=5)
        self.entry = Entry(master)
        self.entry.pack(padx=5, pady=5)
        if self.initialvalue:
            self.entry.insert(0, self.initialvalue)
            self.entry.select_range(0, END)

        self.parent.bind_text_shortcuts(self.entry)

        return self.entry

    def apply(self):
        self.result = self.entry.get()


def encode_address_as_uint256(address_hex):
    target_address_int = int(address_hex, 16)

    encoded_solidity = f"""
    {target_address_int}"""
    return encoded_solidity


class ContractInterfaceApp:
    def __init__(self, root):
        self.check_syntax_if_modified = None
        self.user_refused_version_change = False

        self.saved_contracts_listbox = None
        self.key_visible = False
        self.syntax_check_scheduled = False
        self.account_balance_label = None
        self.root = root
        self.root.title("Ethereum/BSC Contract Interface v2.0611")
        self.contract = None
        self.abi = None
        self.bytecode = None
        self.deployed_contract = None
        self.account = None
        self.w3 = None
        self.selected_network = None
        self.selected_button = None
        self.version_mismatch_notified = False
        self.last_checked_version = None

        self.top_frame = Frame(self.root, bg='#1e1e1e', height=40)
        self.top_frame.pack(side=TOP, fill=X, padx=10, pady=10)
        self.documentation_button = Button(
            self.top_frame,
            text="Documentation",
            command=self.open_documentation_window,
            bg='white', fg='black', font=('Arial', 8, 'bold'), width=13,
            cursor="hand2"
        )
        self.documentation_button.grid(row=0, column=0, padx=5)

        self.documentation_button.bind("<Enter>", lambda event: self.documentation_button.config(
            bg='lightgrey'))
        self.documentation_button.bind("<Leave>", lambda event: self.documentation_button.config(
            bg='white'))

        self.uniswap_button = Button(
            self.top_frame,
            text="Uniswap",
            command=self.open_uniswap,
            bg='pink', fg='black', font=('Arial', 10, 'bold'), width=13,
            cursor="hand2"
        )
        self.uniswap_button.grid(row=0, column=1, padx=5, pady=(0, 0))

        self.uniswap_button.bind("<Enter>",
                                 lambda event: self.uniswap_button.config(bg='lightcoral'))
        self.uniswap_button.bind("<Leave>",
                                 lambda event: self.uniswap_button.config(bg='pink'))

        self.pancakeswap_button = Button(
            self.top_frame,
            text="PancakeSwap",
            command=self.open_pancakeswap,
            bg='lightgreen', fg='black', font=('Arial', 10, 'bold'), width=13,
            cursor="hand2"
        )
        self.pancakeswap_button.grid(row=0, column=2, padx=5, pady=(0, 0))

        self.pancakeswap_button.bind("<Enter>", lambda event: self.pancakeswap_button.config(
            bg='lightyellow'))
        self.pancakeswap_button.bind("<Leave>", lambda event: self.pancakeswap_button.config(
            bg='lightgreen'))

        self.etherscan_button = Button(
            self.top_frame,
            text="Etherscan",
            command=self.open_etherscan,
            bg='lightblue', fg='black', font=('Arial', 10, 'bold'), width=13,
            cursor="hand2"
        )
        self.etherscan_button.grid(row=0, column=3, padx=5, pady=(0, 0))

        self.etherscan_button.bind("<Enter>",
                                   lambda event: self.etherscan_button.config(bg='deepskyblue'))
        self.etherscan_button.bind("<Leave>", lambda event: self.etherscan_button.config(
            bg='lightblue'))

        self.bscscan_button = Button(
            self.top_frame,
            text="Bscscan",
            command=self.open_bscscan,
            bg='lightyellow', fg='black', font=('Arial', 10, 'bold'), width=13,
            cursor="hand2"
        )
        self.bscscan_button.grid(row=0, column=4, padx=5, pady=(0, 0))

        self.bscscan_button.bind("<Enter>", lambda event: self.bscscan_button.config(bg='gold'))
        self.bscscan_button.bind("<Leave>", lambda event: self.bscscan_button.config(
            bg='lightyellow'))

        self.dex_tools_button = Button(
            self.top_frame,
            text="DEX Tools",
            command=self.open_dextools,
            bg='#3b5998',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12,
            relief=RAISED,
            bd=2,
            cursor="hand2"
        )
        self.dex_tools_button.grid(row=0, column=5, padx=5)

        self.dex_tools_button.bind("<Enter>",
                                   lambda event: self.dex_tools_button.config(bg='#3b78d1'))
        self.dex_tools_button.bind("<Leave>", lambda event: self.dex_tools_button.config(
            bg='#3b5998'))

        self.dex_tools_button.bind("<Enter>",
                                   lambda event: self.dex_tools_button.config(bg='darkblue'))
        self.dex_tools_button.bind("<Leave>", lambda event: self.dex_tools_button.config(
            bg='#3b5998'))

        self.uint256_frame = Frame(self.top_frame, bg='#1e1e1e')
        self.uint256_frame.grid(row=0, column=6, padx=(20, 0), sticky="e")
        self.custom_address_label = Label(
            self.uint256_frame,
            text="Enter address:",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.custom_address_label.pack(side=LEFT, padx=(0, 5))

        self.custom_address_entry = Entry(self.uint256_frame, font=('Arial', 10), width=20)
        self.custom_address_entry.pack(side=LEFT, padx=(0, 5))
        self.custom_address_entry.bind("<Button-3>", lambda event: self.show_text_menu(event))

        self.encode_address_btn = Button(
            self.uint256_frame,
            text="Encode as uint256",
            command=self.encode_address,
            bg='purple', fg='white', font=('Arial', 10, 'bold')
        )
        self.encode_address_btn.pack(side=LEFT)

        self.main_frame = Frame(self.root, bg='#1e1e1e')
        self.main_frame.pack(fill=BOTH, expand=True)

        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.interfaces_path = "interfaces"
        self.imports_path = "imports"
        self.setup_contract_environment()

        self.root.configure(bg='#1e1e1e')

        self.left_frame = Frame(self.main_frame, bg='#1e1e1e')
        self.left_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.right_frame = Frame(self.main_frame, bg='#1e1e1e')
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        self.center_frame = Frame(self.main_frame, bg='#1e1e1e')
        self.center_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.contract_code_frame = LabelFrame(
            self.center_frame,
            text="Enter Contract Code:",
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        self.contract_code_frame.pack(pady=10, fill=BOTH, expand=True)

        self.line_numbers = Text(
            self.contract_code_frame,
            width=4,
            padx=5,
            takefocus=0,
            border=0,
            background='#1e1e1e',
            foreground='grey',
            state='disabled',
            font=('Arial', 10),
            spacing3=3
        )

        self.line_numbers.pack(side=LEFT, fill=Y)

        self.contract_code = ScrolledText(
            self.contract_code_frame,
            height=30,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            bg='#2e2e2e',
            fg='white',
            insertbackground='white',
            font=('Arial', 10),
            spacing3=3

        )
        self.contract_code.bind("<<Modified>>", self.on_contract_code_modified)

        self.contract_code.bind("<KeyRelease>", self.update_line_numbers)
        self.contract_code.bind("<MouseWheel>", self.sync_scroll)

        self.update_line_numbers()

        self.contract_code.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.saved_contracts = []

        self.setup_interface_elements()

        self.setup_interface()

        self.private_key.bind('<<Paste>>', self.on_private_key_paste)
        self.private_key.bind('<KeyRelease>', self.update_address_display)

        self.current_contract_name = None
        self.current_loaded_contract_address = None

        self.check_internet_connection()

        self.the_menu = None
        self.make_text_menu()

    def open_dextools(self):
        webbrowser.open("https://www.dextools.io/")

    def open_etherscan(self):
        webbrowser.open("https://etherscan.io/")

    def open_bscscan(self):
        webbrowser.open("https://bscscan.com/")

    def open_uniswap(self):
        webbrowser.open("https://uniswap.org")

    def open_pancakeswap(self):
        webbrowser.open("https://pancakeswap.finance")

    def on_seed_phrase_paste(self, event=None):

        self.root.after(50, self)

    def select_network(self, network_name):

        private_key = self.private_key.get().strip()
        if not private_key:
            self.update_log("Private key is empty. Please enter your private key.", level='error')
            messagebox.showerror("Error", "Private key is required to connect to the network.")

            return False

        self.selected_network = network_name
        self.update_log(f"Attempting to connect to {network_name}...", level='info')

        try:
            self.connect_to_network()
            if self.w3.is_connected():
                self.update_log(f"Successfully connected to {network_name}.", level='info')
                return True
            else:
                self.update_log(f"Failed to connect to {network_name}.", level='error')
                return False
        except Exception as e:
            self.update_log(f"Error connecting to {network_name}: {e}", level='error')
            messagebox.showerror("Connection Error",
                                 f"Failed to connect to {network_name}. Check network URL and keys.")
            return False

    def select_network_and_update(self, network_name):
        connection_success = self.select_network(network_name)

        self.bnb_testnet_btn.config(bg='red', text="BNB Test Network")
        self.bnb_mainnet_btn.config(bg='red', text="BNB Main Network")
        self.eth_mainnet_btn.config(bg='red', text="ETH Main Network")
        self.sepolia_testnet_btn.config(bg='red', text="Sepolia Test Network")

        if connection_success:
            if network_name == "BNB Test Network":
                self.bnb_testnet_btn.config(bg='green', text="BNB Test Connected")
            elif network_name == "BNB Main Network":
                self.bnb_mainnet_btn.config(bg='green', text="BNB Main Connected")
            elif network_name == "ETH Main Network":
                self.eth_mainnet_btn.config(bg='green', text="ETH Main Connected")
            elif network_name == "Sepolia Test Network":
                self.sepolia_testnet_btn.config(bg='green', text="Sepolia Connected")
        else:

            self.update_log(f"Failed to connect to {network_name}. Check your network settings and try again.",
                            level='error')

    def get_constructor_args_dialog(self, abi):
        constructor = next((item for item in abi if item.get('type') == 'constructor'), None)
        args = []
        if constructor and constructor.get('inputs'):
            dialog = Toplevel(self.root)
            dialog.title("Enter Constructor Parameters")
            dialog.configure(bg='#1e1e1e')
            dialog.grab_set()

            input_frame = Frame(dialog, bg='#1e1e1e')
            input_frame.pack(padx=10, pady=10)

            entries = []
            for param in constructor['inputs']:
                param_label = Label(input_frame, text=f"{param['name']} ({param['type']}):", bg='#1e1e1e', fg='white')
                param_label.pack(anchor='w')
                entry = Entry(input_frame, width=40)
                entry.pack(pady=5)
                entries.append((param, entry))

            def on_ok():
                try:
                    for param, entry in entries:
                        user_input = entry.get()
                        parsed_input = self.parse_input(user_input, param['type'])
                        args.append(parsed_input)
                except Exception as e:
                    messagebox.showerror("Error", f"Error parsing input: {e}")
                finally:
                    dialog.destroy()

            button_frame = Frame(dialog, bg='#1e1e1e')
            button_frame.pack(pady=10)

            ok_button = Button(button_frame, text="OK", command=on_ok, bg='green', fg='white', font=('Arial', 10, 'bold'))
            ok_button.pack(side=LEFT, padx=5)

            cancel_button = Button(button_frame, text="Cancel", command=dialog.destroy, bg='red', fg='white', font=('Arial', 10, 'bold'))
            cancel_button.pack(side=LEFT, padx=5)

            self.root.wait_window(dialog)

        return args



    def convert_seed_to_private_key(self):
        seed_phrase = self.seed_phrase_entry.get().strip()
        if not seed_phrase:
            self.update_log("Seed phrase is empty. Please enter the seed phrase.", level='error')
            return

        try:
            Account.enable_unaudited_hdwallet_features()

            account = Account.from_mnemonic(seed_phrase)
            private_key = account.key.hex()

            warning_window = Toplevel(self.root)
            warning_window.title("Warning!")
            warning_window.configure(bg='#1e1e1e')

            window_width, window_height = 400, 200
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            warning_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            warning_label = Label(
                warning_window,
                text="⚠️ The private key will be displayed for 10 seconds after you press 'OK'.\nPlease save it securely.",
                font=("Arial", 14, "bold"),
                bg='#1e1e1e',
                fg='white',
                wraplength=350,
                justify="center"
            )
            warning_label.pack(pady=20)

            def on_ok():
                warning_window.destroy()

                self.log_output.config(state="normal")
                self.log_output.insert(END, f"Private Key from Seed Phrase: {private_key}\n", ('private_key',))
                self.log_output.tag_add('private_key', "end-2l", "end-1c")
                self.log_output.see(END)
                self.log_output.config(state="disabled")

                self.root.after(10000, self.clear_private_key_logs)
                self.root.after(10000, lambda: self.seed_phrase_entry.delete(0, END))

            ok_button = Button(warning_window, text="OK", command=on_ok, font=("Arial", 12), bg="green", fg="white")
            ok_button.pack(pady=20)

        except Exception as e:
            self.update_log(f"Error generating private key: {e}", level='error')
            messagebox.showerror("Error", f"Error generating private key from seed phrase: {e}")

    def clear_private_key_logs(self):
        self.log_output.config(state="normal")

        start = self.log_output.index("1.0")
        while True:
            pos = self.log_output.search("Private Key from Seed Phrase", start, END, nocase=True)
            if not pos:
                break
            end = f"{pos} lineend"
            self.log_output.delete(pos, end)
            start = pos

        self.seed_phrase_entry.delete(0, END)

        self.log_output.config(state="disabled")

    def toggle_seed_phrase_visibility(self):
        if self.seed_visible:
            self.seed_phrase_entry.config(show="*")
            self.seed_eye_button.config(text="👁")
            self.seed_visible = False
        else:
            self.seed_phrase_entry.config(show="")
            self.seed_eye_button.config(text="🔒")
            self.seed_visible = True

    def on_contract_code_modified(self, event):
        pragma_match = re.search(r'pragma solidity\s+\^?([^;]+);', self.contract_code.get("1.0", END))
        if pragma_match:
            specified_version = pragma_match.group(1).strip()

            if specified_version != self.version_var.get() and not self.user_refused_version_change:
                response = messagebox.askyesno(
                    "Version Mismatch",
                    f"The contract specifies Solidity version {specified_version}. Would you like to switch to this version?"
                )
                if response:
                    self.version_var.set(specified_version)
                    self.load_compiler(show_message=True)
                    self.update_log(f"Switched compiler version to {specified_version} as specified in the contract.",
                                    level='info')
                else:
                    self.user_refused_version_change = True
                    self.update_log("Compiler version remains unchanged.", level='info')

        if not self.syntax_check_scheduled:
            self.syntax_check_scheduled = True
            self.root.after(1000, self.check_syntax_if_modified)

    def check_syntax_errors(self):
        source_code = self.contract_code.get("1.0", END).strip()

        if not source_code:
            self.update_log("Error: Contract code is empty.", level='error')
            return

        solc_version = self.version_var.get()

        pragma_match = re.search(r'pragma solidity\s+\^?([^;]+);', source_code)
        if pragma_match:
            specified_version = pragma_match.group(1).strip()
            if specified_version != solc_version:
                if self.user_refused_version_change:
                    self.update_log(
                        f"Skipped syntax check: compiler version mismatch ({specified_version} specified, {solc_version} loaded).",
                        level='warning'
                    )
                    return
            else:
                self.user_refused_version_change = False

        try:
            solcx.install_solc(solc_version)
            solcx.set_solc_version(solc_version)

            solcx.compile_source(
                source_code,
                output_values=["abi", "bin"],
                import_remappings=[
                    "github.com/=" + os.path.join(self.imports_path, "github.com/"),
                    "./=" + self.imports_path
                ],
                allow_paths=self.imports_path
            )

            self.clear_error_logs()
            if "No errors detected" not in self.log_output.get("1.0", END):
                self.update_log("Syntax check passed successfully. No errors detected.", level='info')

        except exceptions.SolcError as e:
            error_message = str(e).replace("\\n", "\n")
            self.update_log(f"[Error] Syntax error:\n{error_message}", level='error')

        except Exception as e:
            self.update_log(f"[Error] Unknown error during syntax check: {e}", level='error')

    def clear_error_logs(self):
        self.log_output.config(state="normal")
        current_log = self.log_output.get("1.0", END)
        updated_log = "\n".join(
            line for line in current_log.splitlines() if not line.startswith("[Error]")
        )
        self.log_output.delete("1.0", END)
        self.log_output.insert("1.0", updated_log.strip())
        self.log_output.config(state="disabled")
        self.log_output.see(END)

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state=NORMAL)
        self.line_numbers.delete(1.0, END)
        line_count = self.contract_code.index('end-1c').split('.')[0]
        line_numbers_text = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state=DISABLED)

    def sync_scroll(self, event=None):
        self.line_numbers.yview_moveto(self.contract_code.yview()[0])

    def setup_interface_elements(self):
        self.network_frame = LabelFrame(self.left_frame, text="Network Selection", bg='#1e1e1e', fg='white',
                                        font=('Arial', 15))
        self.network_frame.pack(pady=5, fill=X)

        self.network_buttons_frame = Frame(self.network_frame, bg='#1e1e1e')
        self.network_buttons_frame.pack(pady=5)

        self.bnb_testnet_btn = Button(
            self.network_buttons_frame,
            text="BNB Test Network",
            command=lambda: self.select_network_and_update("BNB Test Network"),
            bg='red', fg='white', font=('Arial', 10, 'bold'), width=18,
            cursor="hand2"
        )
        self.bnb_testnet_btn.pack(side=LEFT, padx=5)

        self.bnb_mainnet_btn = Button(
            self.network_buttons_frame,
            text="BNB Main Network",
            command=lambda: self.select_network_and_update("BNB Main Network"),
            bg='red', fg='white', font=('Arial', 10, 'bold'), width=18,
            cursor="hand2"
        )
        self.bnb_mainnet_btn.pack(side=LEFT, padx=5)

        self.eth_mainnet_btn = Button(
            self.network_buttons_frame,
            text="ETH Main Network",
            command=lambda: self.select_network_and_update("ETH Main Network"),
            bg='red', fg='white', font=('Arial', 10, 'bold'), width=18,
            cursor="hand2"
        )
        self.eth_mainnet_btn.pack(side=LEFT, padx=5)

        self.sepolia_testnet_btn = Button(
            self.network_buttons_frame,
            text="Sepolia Test Network",
            command=lambda: self.select_network_and_update("Sepolia Test Network"),
            bg='red', fg='white', font=('Arial', 10, 'bold'), width=18,
            cursor="hand2"
        )
        self.sepolia_testnet_btn.pack(side=LEFT, padx=5)

    def open_documentation_window(self):
        pdf_path = os.path.abspath(
            "Ethereum_BSC_Contract_Interface_Documentation.pdf")

        if os.path.exists(pdf_path):
            try:
                webbrowser.open(f"file://{pdf_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open the documentation file: {e}")
        else:
            messagebox.showerror("Error", "Documentation file not found.")

    def make_text_menu(self):
        if not self.the_menu:
            self.the_menu = Menu(self.root, tearoff=0, bg='#2e2e2e', fg='white')
            self.the_menu.add_command(label="Cut", command=lambda: self.execute_menu_command("<<Cut>>"))
            self.the_menu.add_command(label="Copy", command=lambda: self.execute_menu_command("<<Copy>>"))
            self.the_menu.add_command(label="Paste", command=lambda: self.execute_menu_command("<<Paste>>"))
            self.the_menu.add_separator()
            self.the_menu.add_command(label="Select All", command=lambda: self.select_all(self.root.focus_get()))
            self.root.bind("<Escape>", lambda e: self.the_menu.unpost())

    def execute_menu_command(self, command):
        widget = self.root.focus_get()
        print(f"Executing menu command: {command} on {widget}")
        widget.event_generate(command)
        self.the_menu.unpost()

    def copy_log_entry(self, event):
        try:

            line_index = self.log_output.index("@%s,%s linestart" % (event.x, event.y))
            line_text = self.log_output.get(line_index, f"{line_index} lineend")

            indented_text = "    " + line_text

            self.root.clipboard_clear()
            self.root.clipboard_append(indented_text)

            messagebox.showinfo("Copied", "Function copied to clipboard.")
        except Exception as e:
            self.update_log(f"Error copying: {e}", level='error')

    def load_saved_contracts(self):
        try:
            self.load_contracts_btn.pack_forget()

            if os.path.exists('contracts.json'):
                with open('contracts.json', 'r', encoding='utf-8') as file:
                    self.saved_contracts = json.load(file)

                self.update_log(f"Loaded {len(self.saved_contracts)} saved contracts.", level='info')

                self.update_saved_contracts_list()
            else:
                self.update_log("Saved contracts file not found.", level='warning')
                self.saved_contracts = []
        except json.JSONDecodeError:
            self.update_log("Error decoding JSON file with saved contracts.", level='error')
            self.saved_contracts = []
        except FileNotFoundError as e:
            self.update_log(f"File not found: {e}", level='error')
            self.saved_contracts = []
        except Exception as e:
            self.update_log(f"An unexpected error occurred while loading contracts: {e}", level='error')
            self.saved_contracts = []

    def delete_selected_contract(self):
        selection = self.saved_contracts_listbox.curselection()
        if selection:
            index = selection[0]
            contract = self.saved_contracts[index]
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Do you really want to delete the contract {contract['name']}?"
            )
            if confirm:
                del self.saved_contracts[index]
                with open('contracts.json', 'w', encoding='utf-8') as f:
                    json.dump(self.saved_contracts, f, indent=2)
                self.load_saved_contracts()
                self.update_log(f"Contract {contract['name']} deleted.", level='info')
        else:
            messagebox.showerror("Error", "No contract selected for deletion.")

    def update_saved_contracts_list(self):
        for widget in self.saved_contracts_frame.winfo_children():
            if widget != self.load_contracts_btn:
                widget.destroy()

        for index, contract in enumerate(self.saved_contracts):
            display_text = f'contract "{contract["name"]}": {contract["address"]}'

            button = Button(
                self.saved_contracts_frame,
                text=display_text,
                bg='darkgreen' if contract.get('address') == self.current_loaded_contract_address else 'white',
                fg='white' if contract.get('address') == self.current_loaded_contract_address else 'black',
                font=('Arial', 8),
                relief=RAISED
            )

            button.config(command=lambda c=contract, b=button: self.select_contract(c, b))
            button.pack(pady=1, padx=5, fill=X)

            button.original_bg = button.cget("bg")
            button.original_fg = button.cget("fg")

            button.bind("<Enter>", lambda e, btn=button: btn.config(bg='darkgrey', cursor="hand2"))
            button.bind("<Leave>", lambda e, btn=button: btn.config(
                bg=btn.original_bg if self.selected_button is None or btn != self.selected_button else 'darkgreen',
                fg='white' if btn == self.selected_button else 'black'
            ))

            button.bind("<Button-3>", lambda e, idx=index: self.show_delete_menu(e, idx))

            if contract.get('address') == self.current_loaded_contract_address:
                self.selected_button = button
                button.config(bg='darkgreen', fg='white')

    def select_contract(self, contract, button):
        if self.selected_button:
            self.selected_button.config(bg=self.selected_button.original_bg, fg=self.selected_button.original_fg)

        self.current_loaded_contract_address = contract['address']

        self.selected_button = button
        self.selected_button.config(bg='darkgreen', fg='white')

        self.load_contract(contract)

    def show_delete_menu(self, event, index):
        self.contract_menu = Menu(self.root, tearoff=0)
        self.contract_menu.add_command(label="Delete", command=lambda: self.confirm_delete_contract(index))
        self.contract_menu.post(event.x_root, event.y_root)

    def confirm_delete_contract(self, index):
        contract = self.saved_contracts[index]
        confirm = messagebox.askyesno("Confirmation",
                                      f"Are you sure you want to delete the contract {contract['name']}?")
        if confirm:
            del self.saved_contracts[index]
            with open('contracts.json', 'w', encoding='utf-8') as f:
                json.dump(self.saved_contracts, f, indent=2)
            self.load_saved_contracts()
            self.update_log(f"Contract {contract['name']} deleted.", level='info')

    def reset_interface(self):
        self.contract_code.delete("1.0", END)

        self.custom_address_entry.delete(0, END)

        self.address_label.config(text="Address: " + self.address_value.cget("text"))

        if hasattr(self, 'contract_balance_frame'):
            for widget in self.contract_balance_frame.winfo_children():
                widget.grid_remove()

        self.abi_output.config(state="normal")
        self.abi_output.delete(1.0, END)
        self.abi_output.config(state="disabled")

        self.bytecode_output.config(state="normal")
        self.bytecode_output.delete(1.0, END)
        self.bytecode_output.config(state="disabled")

        self.log_output.config(state="normal")
        self.log_output.delete("1.0", END)
        self.log_output.config(state="disabled")

        for widget in self.saved_contracts_frame.winfo_children():
            widget.destroy()

        self.load_contracts_btn = Button(
            self.saved_contracts_frame,
            text="Load Contracts",
            command=self.load_saved_contracts,
            bg='grey', fg='white',
            font=('Arial', 12, 'bold'),
            cursor="hand2"
        )
        self.load_contracts_btn.pack(pady=5, fill=X)

        self.selected_button = None
        self.deploy_selected_btn.config(state=DISABLED)

        for widget in self.functions_frame.winfo_children():
            widget.destroy()

        self.deployed_contract = None
        self.current_loaded_contract_address = None
        self.account_balance_output.config(text="0 ETH")

        self.private_key.delete(0, END)

        self.update_log("Interface reset for new deploy. Network connection and private key retained.", level='info')

    def show_loading_window(self):
        self.loading_window = Toplevel(self.root)
        self.loading_window.title("Deploy")
        self.loading_window.configure(bg='#1e1e1e')

        window_width = 200
        window_height = 100
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.loading_label = Label(
            self.loading_window,
            text="Pending...",
            font=("Arial Black", 12, "bold"),
            bg='#1e1e1e',
            fg='white'
        )
        self.loading_label.pack(pady=20)

    def encode_address(self):
        address = self.custom_address_entry.get().strip()

        if not Web3.is_checksum_address(address):
            self.update_log("Invalid address. Please enter a valid address.", level='error')
            messagebox.showerror("Error", "Invalid address. Please enter a valid address.")
            return

        encoded_result = encode_address_as_uint256(address)

        self.update_log(f"Encoded address as uint256:\n{encoded_result}", level='info')
        messagebox.showinfo("Result", f"Encoded address as uint256:\n{encoded_result}")

    def hide_loading_window(self):
        self.animating = False
        if hasattr(self, 'loading_window'):
            self.loading_window.destroy()

    def update_bytecode_display(self, address):
        try:

            self.bytecode_output.config(state="normal")
            self.bytecode_output.delete(1.0, END)
            self.bytecode_output.insert(END, f"Contract deployed at address: {address}\n")
            self.bytecode_output.insert(END, f"Bytecode: {self.bytecode}")
            self.bytecode_output.config(state="disabled")
            self.update_log(f"Contract bytecode updated for address: {address}", level='info')
        except Exception as e:
            self.update_log(f"Error updating bytecode: {e}", level='error')
            messagebox.showerror("Error", f"Error updating bytecode: {e}")

    def setup_contract_environment(self):
        for path in [self.interfaces_path, self.imports_path]:
            if not os.path.exists(path):
                os.makedirs(path)
                self.update_log(f"Created folder: {path}", level='info')

            try:
                test_file = os.path.join(path, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except PermissionError:
                self.update_log(f"Error: No write permissions for folder {path}.", level='error')
                messagebox.showerror("Error", f"No write permissions for folder {path}.")

    def update_log(self, message, level='info'):
        if not hasattr(self, 'log_output'):
            print(f"[{level.upper()}] {message}")
            return

        self.log_output.config(state="normal")

        if "Private Key" in message:
            parts = message.split("Private Key from Seed Phrase: ")
            prefix = "Private Key from Seed Phrase: "
            private_key = parts[1] if len(parts) > 1 else ""

            self.log_output.insert(END, prefix, 'private_key')
            self.log_output.insert(END, private_key + "\n", 'private_key')
        else:
            self.log_output.insert(END, message + "\n", level)

        self.log_output.see(END)
        self.log_output.config(state="disabled")

    def setup_interface(self):
        label_bg_color = '#1e1e1e'

        self.top_frame = Frame(self.root, bg='#1e1e1e')
        self.top_frame.pack(side=TOP, fill=X, padx=10, pady=10)

        self.connection_indicator = Canvas(self.top_frame, width=20, height=20, bg='#1e1e1e', highlightthickness=0)
        self.connection_indicator.pack(side=RIGHT, padx=5)

        self.connection_circle = self.connection_indicator.create_oval(5, 5, 15, 15, fill="red")

        self.reset_button = Button(self.top_frame, text="Reset", command=self.reset_interface, bg='red', fg='white',
                                   font=('Arial', 10, 'bold'))
        self.reset_button.pack(side=RIGHT, padx=10)

        self.infura_label = Label(
            self.network_frame,
            text="Enter Infura key (only for Ethereum):",
            bg='#1e1e1e', fg='white', font=('Arial', 10)
        )
        self.infura_key = Entry(self.network_frame, font=('Arial', 10), width=35)
        self.infura_label.pack_forget()
        self.infura_key.pack_forget()

        self.private_key_label = Label(
            self.left_frame,
            text="Enter private key:",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.private_key_label.pack(pady=5)

        self.private_key_frame = Frame(self.left_frame, bg='#1e1e1e')
        self.private_key_frame.pack(pady=5)

        self.private_key = Entry(self.private_key_frame, show="*", width=35, font=('Arial', 10))
        self.private_key.pack(side=LEFT)

        self.eye_button = Button(
            self.private_key_frame,
            text="👁",
            command=self.toggle_private_key_visibility,
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 15),
            relief=FLAT
        )
        self.eye_button.pack(side=LEFT)

        self.address_container = Frame(self.left_frame, bg='#1e1e1e')
        self.address_container.pack(pady=5)

        self.address_label = Label(
            self.address_container,
            text="Address:",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.address_label.pack(side=LEFT, pady=5)

        self.address_value = Label(self.address_container, text="", bg='#1e1e1e', fg='#ADD8E6',
                                   font=('Arial', 10, 'bold'))
        self.address_value.pack(side=LEFT, padx=(5, 0))

        self.share_button = Button(
            self.address_container,
            text="🔗",
            font=("Arial", 12),
            command=lambda: self.open_block_explorer(self.address_label.cget("text").replace("Address: ", "").strip()),
            bg='#1e1e1e',
            fg='white',
            relief=FLAT,
            cursor="hand2"
        )

        self.share_button.pack(side=LEFT, padx=(5, 0))
        self.share_button.pack_forget()

        self.account_balance_label = Label(
            self.left_frame,
            text="Wallet balance:",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.account_balance_label.pack(pady=5)

        self.account_balance_output = Label(
            self.left_frame,
            text="0 ETH",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.account_balance_output.pack(pady=2)

        self.separator = Frame(self.left_frame, height=2, bd=1, relief=SUNKEN, bg='#2e2e2e')
        self.separator.pack(fill=X, padx=5, pady=10)

        self.seed_phrase_label = Label(
            self.left_frame,
            text="Enter seed phrase:",
            bg='#2e2e2e',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=5
        )
        self.seed_phrase_label.pack(pady=5)

        self.seed_phrase_frame = Frame(self.left_frame, bg='#1e1e1e')
        self.seed_phrase_frame.pack(pady=5)

        self.seed_phrase_entry = Entry(self.seed_phrase_frame, font=('Arial', 10), width=40, show="*")
        self.seed_phrase_entry.pack(side=LEFT, padx=5)
        self.seed_visible = False
        self.seed_phrase_entry.bind("<Control-v>", self.on_seed_phrase_paste)
        self.seed_phrase_entry.bind("<Command-v>", self.on_seed_phrase_paste)
        self.seed_phrase_entry.bind("<<Paste>>", self.on_seed_phrase_paste)

        self.seed_phrase_entry.bind("<Button-3>", self.show_text_menu)

        self.seed_eye_button = Button(
            self.seed_phrase_frame,
            text="👁",
            command=self.toggle_seed_phrase_visibility,
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 15),
            relief=FLAT
        )
        self.seed_eye_button.pack(side=LEFT)

        self.seed_to_private_key_btn = Button(
            self.left_frame,
            text="Seed Phrase to Private Key",
            command=self.convert_seed_to_private_key,
            bg='purple', fg='white', font=('Arial', 10, 'bold'), width=35
        )
        self.seed_to_private_key_btn.pack(pady=5)

        self.separator = Frame(self.left_frame, height=2, bd=1, relief=SUNKEN, bg='#2e2e2e')
        self.separator.pack(fill=X, padx=5, pady=10)

        self.version_label = Label(
            self.left_frame,
            text="Select compiler version:",
            bg='#1e1e1e', fg='white', font=('Arial', 14, 'bold')
        )
        self.version_label.pack(pady=5)

        self.compiler_versions = [f"0.8.{i}" for i in range(26, -1, -1)] + \
                                 [f"0.7.{i}" for i in range(6, -1, -1)] + \
                                 [f"0.6.{i}" for i in range(12, -1, -1)] + \
                                 [f"0.5.{i}" for i in range(17, -1, -1)] + \
                                 [f"0.4.{i}" for i in range(26, 10, -1)]
        self.version_var = StringVar(value="0.8.0")

        self.version_menu = ttk.Combobox(
            self.left_frame,
            textvariable=self.version_var,
            values=self.compiler_versions,
            font=('Arial', 12),
            state="readonly",
            cursor="hand2",
            justify="center"
        )
        self.version_menu.pack(pady=5)

        self.version_menu.bind("<Button-1>", lambda event: self.version_menu.event_generate('<Down>'))

        self.compile_btn = Button(
            self.left_frame,
            text="Compile",
            command=self.compile_contract,
            bg='blue', fg='white', font=('Arial', 12, 'bold'), width=30,
            cursor="hand2"
        )
        self.compile_btn.pack(pady=8)

        self.compile_btn.bind("<Enter>", lambda event: self.compile_btn.config(bg='darkblue'))
        self.compile_btn.bind("<Leave>", lambda event: self.compile_btn.config(bg='blue'))

        self.deploy_selected_btn = Button(
            self.left_frame,
            text="Deploy",
            command=self.deploy_selected_contract,
            state=DISABLED,
            bg='green',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=30
        )
        self.deploy_selected_btn.pack(pady=10)

        self.deploy_selected_btn.config(width=25)
        self.deploy_selected_btn.original_bg = 'green'
        self.deploy_selected_btn.bind("<Enter>", self.on_enter_button)
        self.deploy_selected_btn.bind("<Leave>", self.on_leave_button)

        self.contract_selection_frame = Frame(self.left_frame, bg='#1e1e1e')
        self.contract_selection_frame.pack(pady=5, fill=X)

        self.functions_frame_label = LabelFrame(
            self.left_frame,
            text="Contract Functions",
            bg='#1e1e1e',
            fg='white'
        )
        self.functions_frame_label.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.functions_canvas = Canvas(self.functions_frame_label, bg='#1e1e1e')
        self.functions_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.functions_scrollbar = Scrollbar(
            self.functions_frame_label,
            orient=VERTICAL,
            command=self.functions_canvas.yview
        )
        self.functions_scrollbar.pack(side=RIGHT, fill=Y)

        self.functions_canvas.configure(yscrollcommand=self.functions_scrollbar.set)
        self.functions_canvas.bind('<Configure>', lambda e: self.functions_canvas.configure(
            scrollregion=self.functions_canvas.bbox("all")))

        self.functions_frame = Frame(self.functions_canvas, bg='#1e1e1e')
        self.functions_canvas.create_window((0, 0), window=self.functions_frame, anchor="nw")

        self.functions_canvas.bind("<Enter>", self._bind_mousewheel)
        self.functions_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.log_label_frame = LabelFrame(self.right_frame, text="Logs", bg='#1e1e1e', fg='white', font=('Arial', 10),
                                          padx=10, pady=10)
        self.log_label_frame.pack(pady=10, fill=BOTH, expand=True)

        self.log_output = ScrolledText(
            self.log_label_frame,
            height=8,
            state="normal",
            bg='#2e2e2e',
            fg='white',
            insertbackground='white',
            wrap="word"
        )
        self.log_output.pack(fill=BOTH, expand=True, padx=5)

        self.log_output.tag_config('info', foreground='white')
        self.log_output.tag_config('error', foreground='red')
        self.log_output.tag_config('address', foreground='blue')
        self.log_output.tag_config('contract_address', foreground='#ADD8E6', font=('Arial', 10, 'bold'))

        self.bytecode_label_frame = LabelFrame(
            self.right_frame,
            text="Bytecode Bytecode",
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 10),
            padx=10,
            pady=10
        )
        self.bytecode_label_frame.pack(pady=10, fill=BOTH, expand=True)

        self.bytecode_output = ScrolledText(
            self.bytecode_label_frame,
            height=5,
            state="normal",
            bg='#2e2e2e',
            fg='white',
            insertbackground='white'
        )
        self.bytecode_output.pack(fill=BOTH, expand=True, padx=5)

        self.abi_label_frame = LabelFrame(
            self.right_frame,
            text="Contract ABI:",
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 10),
            padx=10,
            pady=10
        )
        self.abi_label_frame.pack(pady=10, fill=BOTH, expand=True)

        self.abi_output = ScrolledText(
            self.abi_label_frame,
            height=10,
            state="disabled",
            bg='#2e2e2e',
            fg='white',
            insertbackground='white'
        )
        self.abi_output.pack(fill=BOTH, expand=True, padx=5)

        self.saved_contracts_frame = Frame(
            self.right_frame,
            bg='#1e1e1e'
        )
        self.saved_contracts_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        if not hasattr(self, 'load_contracts_btn'):
            self.load_contracts_btn = Button(
                self.saved_contracts_frame,
                text="Load Contracts",
                command=self.load_saved_contracts,
                bg='grey', fg='white',
                font=('Arial', 12, 'bold'),
                cursor="hand2"
            )
            self.load_contracts_btn.pack(pady=5, fill=X)
            self.load_contracts_btn.original_bg = 'grey'
            self.load_contracts_btn.bind("<Enter>", self.on_enter_button)
            self.load_contracts_btn.bind("<Leave>", self.on_leave_button)

        self.contract_menu = Menu(self.root, tearoff=0, bg='#2e2e2e', fg='white')
        self.contract_menu.add_command(label="Delete", command=self.delete_selected_contract)

        self.bind_text_shortcuts(self.private_key)
        self.bind_text_shortcuts(self.contract_code)
        self.bind_text_shortcuts(self.log_output)
        self.bind_text_shortcuts(self.bytecode_output)
        self.bind_text_shortcuts(self.abi_output)

        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        self.root.geometry("")

    def on_private_key_paste(self, event=None):
        print("Pasting private key")
        self.root.after(50, self.check_private_key_format)

    def toggle_private_key_visibility(self):
        if self.key_visible:

            self.private_key.config(show="*")
            self.eye_button.config(text="👁")
            self.key_visible = False
        else:

            current_key = self.private_key.get()
            if current_key.startswith("0x"):
                self.private_key.delete(0, END)
                self.private_key.insert(0, current_key[2:])
            self.private_key.config(show="")
            self.eye_button.config(text="🔒")
            self.key_visible = True

    def set_wallet_address(self, address):
        if address:
            self.address_label.config(text=f"Address: {address}")
            self.share_button.pack(side=LEFT)
        else:
            self.address_label.config(text="")
            self.share_button.pack_forget()

    def check_private_key_format(self):
        private_key_text = self.private_key.get().strip()

        if private_key_text.startswith("0x"):
            private_key_text = private_key_text[2:]

        if not private_key_text or len(private_key_text) != 64:
            messagebox.showerror("Error", "Private key must be 64 characters long (without '0x' prefix).")
            return

        private_key_with_prefix = "0x" + private_key_text

        try:
            account_address = Web3().eth.account.from_key(private_key_with_prefix).address

            self.address_label.config(text=f"Address: {account_address}")
            self.set_wallet_address(account_address)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get address from private key: {e}")

    def check_private_key_prefix_and_update_address(self):
        private_key = self.private_key.get().strip()
        if len(private_key) == 64 and not private_key.startswith("0x"):
            private_key = "0x" + private_key
            self.private_key.delete(0, END)
            self.private_key.insert(0, private_key)
        self.update_address_display()

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def check_internet_connection(self):

        def check():
            try:
                requests.get('https://www.google.com', timeout=5)

                self.connection_indicator.itemconfig(self.connection_circle, fill="green")
            except requests.RequestException:

                self.connection_indicator.itemconfig(self.connection_circle, fill="red")

            self.root.after(10000, check)

        check()

    def update_address_display(self, event=None):
        print("Updating address display")
        private_key = self.private_key.get().strip()
        if len(private_key) == 64 and not private_key.startswith("0x"):
            private_key = "0x" + private_key
            self.private_key.delete(0, END)
            self.private_key.insert(0, private_key)

        if len(private_key) != 66 or not private_key.startswith("0x"):
            self.address_label.config(text="Invalid key format")
            self.update_log("Error: Private key has an invalid format.", level='error')
            return

        try:
            if not self.w3 or not self.w3.is_connected():

                account = Web3().eth.account.from_key(private_key)
            else:
                account = self.w3.eth.account.from_key(private_key)

            self.set_wallet_address(account.address)

            if self.w3 and self.w3.is_connected():
                self.update_account_balance()
        except Exception as e:
            self.address_label.config(text="Invalid private key")
            self.update_log(f"Error: Invalid private key — {e}", level='error')

    def show_text_menu(self, event):
        widget = event.widget
        if isinstance(widget, (Entry, Text, ScrolledText)):
            self.the_menu.tk_popup(event.x_root, event.y_root)

    def bind_text_shortcuts(self, widget):
        widget.bind("<Button-3>", self.show_text_menu)

    def select_all(self, widget):
        widget.event_generate("<<SelectAll>>")

    def load_compiler(self, show_message=False):
        version = self.version_var.get()
        try:
            solcx.install_solc(version)
            solcx.set_solc_version(version)
            self.update_log(f"Compiler version {version} successfully loaded.", level='info')

            if show_message:
                messagebox.showinfo("Success", f"Solidity compiler version {version} loaded.")

        except Exception as e:
            self.update_log(f"Error loading compiler: {e}", level='error')
            if show_message:
                messagebox.showerror("Error", f"Failed to load compiler: {str(e)}")

    def find_and_download_imports(self, source_code, current_dir=None):
        if current_dir is None:
            current_dir = self.imports_path

        imports = re.findall(r'import\s+(?:[^"]*"([^"]+)"|\'([^\']+)\');', source_code)
        imports = [imp[0] or imp[1] for imp in imports]

        self.update_log(f"Found imports: {imports}", level='info')

        for imp_path in imports:

            local_path = os.path.join(current_dir, imp_path.replace('/', os.sep))

            if os.path.exists(local_path):
                self.update_log(f"Import {imp_path} already downloaded.", level='info')
                continue

            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            if imp_path.startswith('http://') or imp_path.startswith('https://'):
                url = imp_path
            elif imp_path.startswith('github.com/'):

                url = self.convert_github_url(imp_path)
                if not url:
                    continue
            else:

                url = self.get_standard_url(imp_path)
                if not url:
                    self.update_log(f"Unknown import: {imp_path}", level='warning')
                    continue

            self.download_file(url, local_path)

            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    imported_code = f.read()
                self.find_and_download_imports(imported_code, os.path.dirname(local_path))
            except Exception as e:
                self.update_log(f"Error processing imports in file {local_path}: {e}", level='error')

    def convert_github_url(self, github_path):

        parts = github_path.split('/')
        try:
            user = parts[1]
            repo = parts[2]
            if parts[3] == 'blob':
                branch = parts[4]
                file_path = '/'.join(parts[5:])
                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
                return raw_url
            else:
                self.update_log(f"Unsupported GitHub URL format: {github_path}", level='error')
                return None
        except IndexError:
            self.update_log(f"Error parsing GitHub URL: {github_path}", level='error')
            return None

    def get_standard_url(self, imp_path):
        standard_imports = {

            "IERC20.sol": "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/master/contracts/token/ERC20/IERC20.sol",
            "IERC20Metadata.sol": "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/master/contracts/token/ERC20/extensions/IERC20Metadata.sol",
            "IPancakeRouter02.sol": "https://raw.githubusercontent.com/pancakeswap/pancake-swap-periphery/master/contracts/interfaces/IPancakeRouter02.sol",
            "IPancakeRouter01.sol": "https://raw.githubusercontent.com/pancakeswap/pancake-swap-periphery/master/contracts/interfaces/IPancakeRouter01.sol",

        }
        filename = os.path.basename(imp_path)
        return standard_imports.get(filename)

    def download_file(self, url, local_path):
        self.update_log(f"Downloading {url} to {local_path}", level='info')
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.update_log(f"File {local_path} successfully downloaded.", level='info')
        except requests.exceptions.RequestException as e:
            self.update_log(f"Error downloading {url}: {e}", level='error')

    def check_and_download_imports(self):
        source_code = self.contract_code.get("1.0", END).strip()
        if not source_code:
            self.update_log("Error: Contract source code is empty.", level='error')
            messagebox.showerror("Error", "Please enter the contract code first.")
            return

        try:
            self.find_and_download_imports(source_code)
            self.update_log("All necessary imports have been downloaded.", level='info')
            messagebox.showinfo("Success", "All necessary imports have been downloaded.")
        except Exception as e:
            self.update_log(f"Error checking and downloading imports: {e}", level='error')
            messagebox.showerror("Error", f"Error checking and downloading imports: {e}")

    def compile_contract(self):
        source_code = self.contract_code.get("1.0", END).strip()

        if not source_code:
            self.update_log("Error: Contract source code is empty.", level='error')
            messagebox.showerror("Compilation Error",
                                 "Contract source code is empty. Please enter the code and try again.")
            return

        self.check_and_download_imports()

        solc_version = self.version_var.get()
        self.update_log(f"Installing compiler version: {solc_version}", level='info')

        try:
            solcx.install_solc(solc_version)
            solcx.set_solc_version(solc_version)
            self.update_log(f"Solidity compiler version {solc_version} installed and configured.", level='info')
        except solcx.exceptions.SolcInstallationError as e:
            self.update_log(f"Error installing compiler: {e}", level='error')
            messagebox.showerror(
                "Error Installing Compiler",
                f"Failed to install Solidity compiler version {solc_version}: {e}"
            )
            return
        except Exception as e:
            self.update_log(f"Unknown error while installing compiler: {e}", level='error')
            messagebox.showerror(
                "Error",
                f"An unknown error occurred while installing the compiler: {e}"
            )
            return

        try:
            self.update_log("Running contract compilation...", level='info')

            compiled_sol = solcx.compile_source(
                source_code,
                output_values=["abi", "bin"],
                import_remappings=[
                    f"github.com/={self.imports_path}/github.com/",
                    f"./={self.imports_path}/"
                ],
                allow_paths=self.imports_path
            )

            self.update_log(f"Compilation completed, returned: {list(compiled_sol.keys())}", level='info')

            self.compiled_contracts = compiled_sol

            if not self.compiled_contracts:
                self.update_log("Compilation Error: No contracts to compile.", level='error')
                messagebox.showerror(
                    "Compilation Error",
                    "No contracts to compile in the compilation results."
                )
                return

            self.contracts_with_code = {
                name: info for name, info in self.compiled_contracts.items()
                if info.get('bin') and info.get('abi') and info.get('bin') != '0x'
            }

            if not self.contracts_with_code:
                self.update_log("Compilation Error: No contracts with ABI and bytecode.", level='error')
                messagebox.showerror(
                    "Compilation Error",
                    "No contracts with ABI and bytecode."
                )
                return

            first_contract_name = next(iter(self.contracts_with_code))
            first_contract_info = self.contracts_with_code[first_contract_name]
            self.abi = first_contract_info['abi']
            self.bytecode = first_contract_info['bin']

            self.abi_output.config(state="normal")
            self.abi_output.delete(1.0, END)
            self.abi_output.insert(END, json.dumps(self.abi, indent=2))
            self.abi_output.config(state="disabled")

            self.bytecode_output.config(state="normal")
            self.bytecode_output.delete(1.0, END)
            self.bytecode_output.insert(END, self.bytecode)
            self.bytecode_output.config(state="disabled")

            self.update_log("Contracts compiled successfully.", level='info')
            messagebox.showinfo("Success", "Contracts compiled successfully.")

            self.deploy_selected_btn.config(state=NORMAL)

            self.display_contracts()

            self.root.update_idletasks()
            self.root.geometry("")

        except solcx.exceptions.SolcError as e:
            error_msg = str(e).replace("\\n", "\n")
            self.update_log(f"Compilation Error:\n{error_msg}", level='error')
            messagebox.showerror("Compilation Error", f"Error during compilation:\n{error_msg}")
        except Exception as e:
            self.update_log(f"Unknown compilation error: {e}", level='error')
            messagebox.showerror("Compilation Error", f"Unknown error: {str(e)}")

    def display_contracts(self):

        for widget in self.contract_selection_frame.winfo_children():
            widget.destroy()

        self.contract_choice = StringVar(value="Select Contract")
        contract_names = [name.split(':')[1] for name in self.contracts_with_code.keys()]
        self.contract_dropdown = OptionMenu(
            self.contract_selection_frame,
            self.contract_choice,
            *contract_names
        )
        self.contract_dropdown.config(bg='#2e2e2e', fg='white')
        self.contract_dropdown["menu"].config(bg='#2e2e2e', fg='white')
        self.contract_dropdown.pack(pady=5, fill=X)

        self.contract_choice.trace_add('write', self.update_selected_contract_display)

        self.root.update_idletasks()
        self.root.geometry("")

    def update_selected_contract_display(self, *args):
        selected_contract_name = self.contract_choice.get()
        full_contract_name = None
        for name in self.contracts_with_code.keys():
            if name.endswith(f":{selected_contract_name}"):
                full_contract_name = name
                break

        if not full_contract_name:
            return

        contract_info = self.contracts_with_code[full_contract_name]
        self.abi = contract_info['abi']
        self.bytecode = contract_info['bin']

        self.abi_output.config(state="normal")
        self.abi_output.delete(1.0, END)
        self.abi_output.insert(END, json.dumps(self.abi, indent=2))
        self.abi_output.config(state="disabled")

        self.bytecode_output.config(state="normal")
        self.bytecode_output.delete(1.0, END)
        self.bytecode_output.insert(END, self.bytecode)
        self.bytecode_output.config(state="disabled")

    def deploy_selected_contract(self):
        selected_contract_name = self.contract_choice.get()
        if selected_contract_name == "Select Contract":
            messagebox.showerror("Error", "Please select a contract to deploy.")
            return

        full_contract_name = None
        for name in self.contracts_with_code.keys():
            if name.endswith(f":{selected_contract_name}"):
                full_contract_name = name
                break

        if not full_contract_name:
            messagebox.showerror("Error", f"Contract {selected_contract_name} not found.")
            return

        try:
            contract_info = self.contracts_with_code[full_contract_name]
            bytecode = contract_info["bin"]
            abi = contract_info["abi"]
            if not abi:
                raise ValueError(f"ABI for contract {selected_contract_name} not found.")
            self.contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            self.update_log(f"Selected contract for deployment: {selected_contract_name}", level='info')

            self.abi = abi

            # Get constructor arguments through a dialog
            constructor_args = self.get_constructor_args_dialog(abi)

            estimated_gas = self.contract.constructor(*constructor_args).estimate_gas({
                'from': self.account.address,
            })

            gas_price = self.w3.to_wei(3, 'gwei') if "bnb" in self.selected_network.lower() else self.w3.eth.gas_price

            total_cost = estimated_gas * gas_price
            ether_cost = self.w3.from_wei(total_cost, 'ether')

            proceed = messagebox.askyesno(
                "Deployment Confirmation",
                f"Approximately {ether_cost} ETH will be spent. Continue?"
            )
            if not proceed:
                self.update_log("Deployment canceled by user.", level='info')
                return

            self.show_loading_window()
            self.root.update()

            transaction = self.contract.constructor(*constructor_args).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': estimated_gas,
                'gasPrice': gas_price,
            })
            signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key.get())
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            self.update_log(f"Executing transaction {selected_contract_name}... Pending...", level='info')

            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            deployed_address = tx_receipt.contractAddress
            if not deployed_address:
                self.update_log("Error: Contract was not deployed.", level='error')
                self.show_error("Error", "Contract was not deployed.")
                self.hide_loading_window()
                return

            if not self.w3.is_address(deployed_address):
                self.update_log(f"Error: Received invalid contract address: {deployed_address}", level='error')
                self.show_error("Error", f"Received invalid contract address: {deployed_address}")
                self.hide_loading_window()
                return

            self.deployed_contract = self.w3.eth.contract(address=deployed_address, abi=self.abi)
            self.update_log(f"Contract deployed at address: {deployed_address}", level='address')
            self.show_info("Success", f"Contract deployed at address: {deployed_address}")

            self.show_transaction_result(tx_hash.hex())

            self.save_contract(
                name=selected_contract_name,
                address=deployed_address,
                abi=self.abi,
                bytecode=self.bytecode,
                contract_code=self.contract_code.get("1.0", END).strip(),
                network=self.selected_network,
                private_key=self.private_key.get(),
                deployer_address=self.account.address
            )

            self.hide_loading_window()

            self.display_contract_balance(deployed_address)
            self.update_contract_balance(deployed_address)

            self.update_bytecode_display(deployed_address)

            self.display_functions()

            self.root.geometry("")

        except Exception as e:
            self.hide_loading_window()
            self.update_log(f"Error during contract deployment: {e}", level='error')
            messagebox.showerror("Error", f"Error during contract deployment: {str(e)}")


    def get_constructor_args(self, abi):
        constructor = next((item for item in abi if item.get('type') == 'constructor'), None)
        args = []
        if constructor and constructor.get('inputs'):
            for param in constructor['inputs']:
                user_input = self.show_input_dialog(f"Enter value for {param['name']} ({param['type']}):")

                args.append(self.parse_input(user_input, param['type']))
        return args


    def parse_input(self, user_input, param_type):
        try:
            if param_type.startswith("uint") or param_type.startswith("int"):
                return int(user_input)
            elif param_type == "address":
                if self.w3.is_address(user_input):
                    return Web3.to_checksum_address(user_input)
                else:
                    raise ValueError("Invalid address format.")
            elif param_type == "bool":
                return user_input.lower() in ['true', '1', 'yes']
            elif param_type.startswith("bytes") or param_type.startswith("string"):
                return user_input
            elif param_type.endswith("[]"):  # Arrays
                # Example: split values by comma
                return [self.parse_input(item.strip(), param_type[:-2]) for item in user_input.split(',')]
            else:
                return user_input
        except Exception as e:
            self.update_log(f"Error parsing input: {e}", level='error')
            messagebox.showerror("Input Error", f"Error parsing input: {e}")
            return user_input



    def save_contract(self, name, address, abi, bytecode, contract_code, network, private_key, deployer_address):
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance = self.w3.from_wei(balance_wei, 'ether')

            contract_data = {
                'name': name,
                'address': address,
                'abi': abi,
                'bytecode': bytecode,
                'contract_code': contract_code,
                'network': network,
                'deployer_address': deployer_address,
                'private_key': private_key,
                'balance': str(balance)
            }

            if os.path.exists('contracts.json'):
                with open('contracts.json', 'r', encoding='utf-8') as f:
                    contracts = json.load(f)
            else:
                contracts = []

            contracts.append(contract_data)

            with open('contracts.json', 'w', encoding='utf-8') as f:
                json.dump(contracts, f, indent=2)

            self.update_saved_contracts_list()
            self.update_log(f"Contract {name} saved with a balance of {balance} ETH.", level='info')


        except Exception as e:
            self.update_log(f"Ошибка при сохранении контракта: {e}", level='error')

    def load_contract(self, contract):
        try:

            if 'private_key' in contract:
                self.private_key.delete(0, END)
                self.private_key.insert(0, contract['private_key'])
                private_key = self.private_key.get().strip()
                self.account = self.w3.eth.account.from_key(private_key) if self.w3 else None
                self.update_log("Private key loaded for the selected contract.", level='info')
            else:
                self.update_log("Private key not found for the selected contract.", level='warning')
                messagebox.showerror("Error", "No private key found for this contract.")
                return

            if not self.w3 or not self.w3.is_connected() or contract.get('network') != self.selected_network:
                self.select_network(contract.get('network', self.selected_network))

                if not self.w3 or not self.w3.is_connected():
                    messagebox.showerror("Error", "Network connection failed. Please check the network and try again.")
                    return

            self.update_address_display()

            self.deployed_contract = self.w3.eth.contract(address=contract['address'], abi=contract['abi'])
            self.abi = contract['abi']
            self.display_functions()

            if 'abi' in contract:
                self.abi_output.config(state="normal")
                self.abi_output.delete(1.0, END)
                self.abi_output.insert(END, json.dumps(contract['abi'], indent=2))
                self.abi_output.config(state="disabled")
                self.update_log("ABI loaded for the selected contract.", level='info')
            else:
                self.update_log("ABI not found for the selected contract.", level='warning')

            if 'bytecode' in contract:
                self.bytecode = contract['bytecode']
                self.bytecode_output.config(state="normal")
                self.bytecode_output.delete(1.0, END)
                self.bytecode_output.insert(END, self.bytecode)
                self.bytecode_output.config(state="disabled")
                self.update_log("Bytecode loaded for the selected contract.", level='info')
            else:
                self.update_log("Bytecode not found for the selected contract.", level='warning')

            if 'contract_code' in contract:
                self.contract_code.delete("1.0", END)
                self.contract_code.insert(END, contract['contract_code'])
                self.update_log("Contract code loaded for the selected contract.", level='info')

                pragma_match = re.search(r'pragma solidity\s+\^?([^;]+);', contract['contract_code'])
                if pragma_match:
                    version = pragma_match.group(1).strip()
                    if version in self.compiler_versions:
                        self.version_var.set(version)
                        self.load_compiler()
                    else:
                        self.update_log(f"Warning: Compiler version {version} is not supported or available.",
                                        level='warning')
                else:
                    self.update_log("Warning: Solidity version not specified in contract code.", level='warning')

                self.update_line_numbers()

            else:
                self.update_log("Contract code not found for the selected contract.", level='warning')

            balance = contract.get('balance', "0")
            self.display_contract_balance(contract['address'])
            self.balance_output.config(text=f"{balance} ETH")

            self.current_loaded_contract_address = contract['address']

            if self.account.address != contract.get('deployer_address'):
                proceed = messagebox.askyesno(
                    "Account Mismatch",
                    f"You are using a different account ({self.account.address}), not the one that deployed the contract ({contract.get('deployer_address')}).\n"
                    f"Do you want to continue?"
                )
                if not proceed:
                    return

            self.update_log(
                f"Loaded contract {contract['name']} at address {contract['address']} on the {contract['network']} network.\n"
                f"Balance: {balance} ETH. Deployer address: {contract.get('deployer_address')}",
                level='info'
            )

        except Exception as e:
            self.update_log(f"Error loading contract: {e}", level='error')
            messagebox.showerror("Error", f"Error loading contract: {e}")

    def on_saved_contract_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            contract = self.saved_contracts[index]

            self.load_contract(contract)

    def update_contract_balance(self, address):
        if not hasattr(self, 'balance_output'):
            self.balance_output = Label(
                self.contract_selection_frame,
                text="0 ETH",
                bg='#1e1e1e',
                fg='white',
                font=("Arial", 10, "bold")
            )
            self.balance_output.pack(pady=2)

        if not self.w3 or not self.w3.is_connected():
            self.update_log("No connection to the network for retrieving balance.", level='warning')
            self.balance_output.config(text="No connection")
            return

        def start_balance_monitoring():
            try:

                balance_wei = self.w3.eth.get_balance(address)
                balance = self.w3.from_wei(balance_wei, 'ether')

                currency = "ETH" if "ethereum" in self.selected_network.lower() else "BNB"
                balance_str = f"{balance} {currency}"

                if self.balance_output.cget("text") != balance_str:
                    self.balance_output.config(text=balance_str)

                    self.update_log(f"Balance of contract {address} updated: {balance_str}", level='info')

            except Exception as e:
                self.update_log(f"Error updating contract balance: {e}", level='error')
                self.balance_output.config(text="Error")

            self.root.after(10000, start_balance_monitoring)

        start_balance_monitoring()

    def connect_to_network(self):
        if not self.selected_network:
            messagebox.showerror("Error", "Select a network to connect.")
            return

        networks = {
            "BNB Test Network": "https://data-seed-prebsc-1-s1.binance.org:8545/",
            "BNB Main Network": "https://bsc-dataseed.binance.org/",
            "ETH Main Network": "https://eth.llamarpc.com",
            "Sepolia Test Network": "https://ethereum-sepolia-rpc.publicnode.com"
        }
        provider_url = networks.get(self.selected_network)

        if not provider_url:
            self.update_log(f"Unknown network: {self.selected_network}", level='error')
            messagebox.showerror("Error", f"Unknown network: {self.selected_network}")
            return

        self.w3 = Web3(Web3.HTTPProvider(provider_url))

        try:
            private_key = self.private_key.get().strip()
            if not private_key:
                self.update_log("Private key is empty. Please enter your private key.", level='warning')
                messagebox.showerror("Error", "Private key is required to connect.")
                return

            if len(private_key) not in [64, 66] or (len(private_key) == 66 and not private_key.startswith('0x')):
                raise ValueError("The private key must be exactly 64 characters or 66 characters with the '0x' prefix.")

            self.account = self.w3.eth.account.from_key(private_key)

            if not self.w3.is_connected():
                self.update_log("Failed to connect to the network. Please check the URL and your internet connection.",
                                level='error')
                raise ValueError("Failed to connect to the network.")

            messagebox.showinfo("Success", f"Connected to {self.selected_network}.")
            self.update_address_display()

        except ValueError as ve:
            self.update_log(f"Private key error: {ve}", level='error')
            messagebox.showerror("Error", f"Private key error: {ve}")

        except Exception as e:
            self.update_log(f"Connection error: {e}", level='error')
            messagebox.showerror("Error", f"Failed to connect to {self.selected_network}. Check network URL and keys.")

    def update_account_balance(self):
        if not self.w3 or not self.w3.is_connected():
            self.account_balance_output.config(text="No connection")
            return
        try:

            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance = self.w3.from_wei(balance_wei, 'ether')

            balance = round(balance, 4)

            if self.selected_network == "ETH Main Network" or self.selected_network == "Sepolia Test Network":
                currency = "ETH"
            elif "BNB" in self.selected_network:
                currency = "BNB"
            else:
                currency = "Unknown"

            balance_str = f"{balance} {currency}"

            self.account_balance_output.config(text=balance_str)
            self.update_log(f"Account balance: {balance_str}", level='info')
        except Exception as e:
            self.update_log(f"Error getting account balance: {e}", level='error')
            self.account_balance_output.config(text="Error")

    def display_functions(self, e=None, entries=None):
        if e is None:
            e = entries
        if e is None:
            e = None
        for widget in self.functions_frame.winfo_children():
            widget.destroy()

        if not self.deployed_contract:
            self.update_log("No deployed contract loaded to display functions.", level='warning')
            return

        contract_functions = [func for func in self.abi if func["type"] == "function"]
        unique_functions = []

        for func in contract_functions:
            if not any(f["name"] == func["name"] and f["inputs"] == func["inputs"] for f in unique_functions):
                unique_functions.append(func)

        for func in unique_functions:
            frame = Frame(self.functions_frame, bg='#1e1e1e')
            frame.pack(fill=X, padx=5, pady=5)

            entries = []

            button = Button(
                frame,
                text=func["name"],
                command=lambda f=func, e=None: self.call_function(f, e),
                bg='#2e2e2e',
                fg='white',
                font=('Arial', 8, 'bold'),
                width=15,
                height=2
            )
            button.pack(side=LEFT, padx=5)
            button.original_bg = '#2e2e2e'
            button.bind("<Enter>", self.on_enter_button)
            button.bind("<Leave>", self.on_leave_button)
            button.bind("<Button-3>", lambda event, f=func, e=None: self.on_function_button_right_click(event, f, e))

            if func["inputs"]:
                inputs_frame = Frame(frame, bg='#1e1e1e')
                inputs_frame.pack(side=LEFT, padx=5)
                for param in func["inputs"]:
                    param_frame = Frame(inputs_frame, bg='#1e1e1e')
                    param_frame.pack(side=LEFT, padx=5)

                    label = Label(param_frame, text=param['name'], bg='#1e1e1e', fg='white')
                    label.pack(side=TOP)
                    entry = Entry(param_frame, width=15, bg='white', fg='black',
                                  insertbackground='black')
                    entry.pack(side=TOP)
                    entries.append(entry)

                    entry.bind("<Button-3>", self.show_text_menu)

        self.functions_canvas.update_idletasks()
        self.functions_canvas.configure(scrollregion=self.functions_canvas.bbox("all"))

        self.root.update_idletasks()
        self.root.geometry("")

    def on_function_button_right_click(self, event, func, entries):
        self.update_log(f"Right-click on the function: {func['name']}", level='info')

        self.show_text_menu(event)

    def call_function(self, func, entries=None):
        inputs = []

        if entries is None:
            entries = []

        if func["inputs"]:
            for entry, param in zip(entries, func["inputs"]):
                user_input = entry.get()
                inputs.append(user_input)

            try:

                inputs = [self.parse_input(i, p["type"]) for i, p in zip(inputs, func["inputs"])]
            except ValueError:
                self.update_log("Invalid input data.", level='error')
                messagebox.showerror("Error", "Invalid input data.")
                return

        try:
            contract_function = self.deployed_contract.functions[func["name"]]
            if func["stateMutability"] in ["view", "pure"]:
                result = contract_function(*inputs).call()
                self.update_log(f"Result of calling {func['name']}: {result}", level='info')
                messagebox.showinfo("Result", f"Result: {result}")
            else:

                estimated_gas = contract_function(*inputs).estimate_gas({
                    'from': self.account.address,
                })

                gas_price = self.w3.eth.gas_price
                total_cost = estimated_gas * gas_price
                proceed = messagebox.askyesno(
                    "Confirm Transaction",
                    f"Function {func['name']} will require approximately {estimated_gas} gas.\n"
                    f"Cost: {self.w3.from_wei(total_cost, 'ether')} ETH.\nContinue?"
                )
                if not proceed:
                    return

                transaction = contract_function(*inputs).build_transaction({
                    'from': self.account.address,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'gas': estimated_gas,
                    'gasPrice': gas_price
                })

                self.update_log(f"Executing transaction {func['name']}... Pending...", level='info')

                signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key.get())
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if "BNB" in self.selected_network:
                    tx_url = f"https://bscscan.com/tx/{tx_hash.hex()}"
                else:
                    tx_url = f"https://etherscan.io/tx/{tx_hash.hex()}"

                self.update_log(f"Transaction {func['name']} completed. Hash: {tx_hash.hex()}", level='info')

                messagebox.showinfo("Success",
                                    f"Transaction completed.\nHash: {tx_hash.hex()}\nYou can view it here: {tx_url}")

                if self.deployed_contract and self.deployed_contract.address:
                    self.update_contract_balance(self.deployed_contract.address)

        except Exception as e:
            self.update_log(f"Error calling function {func['name']}: {e}", level='error')
            messagebox.showerror("Error", f"Error calling the function: {str(e)}")

    def show_transaction_result(self, tx_hash):

        result_window = Toplevel(self.root)
        result_window.title("Transaction Result")

        hash_label = Label(result_window, text=f"Transaction completed.\nHash: 0x{tx_hash}", font=('Arial', 10))
        hash_label.pack(pady=10)

        if self.selected_network == "BNB Test Network":
            tx_url = f"https://testnet.bscscan.com/tx/0x{tx_hash}"
        elif self.selected_network == "BNB Main Network":
            tx_url = f"https://bscscan.com/tx/0x{tx_hash}"
        elif self.selected_network == "ETH Main Network":
            tx_url = f"https://etherscan.io/tx/0x{tx_hash}"
        elif self.selected_network == "Sepolia Test Network":
            tx_url = f"https://sepolia.etherscan.io/tx/0x{tx_hash}"
        else:
            tx_url = ""

        link_label = Label(result_window, text="View Transaction", fg="blue", cursor="hand2")
        link_label.pack(pady=5)
        link_label.bind("<Button-1>", lambda e: webbrowser.open(tx_url))

        close_button = Button(result_window, text="Close", command=result_window.destroy)
        close_button.pack(pady=10)

    def get_explorer_url(self, tx_hash):
        if "eth main" in self.selected_network.lower():
            return f"https://etherscan.io/tx/{tx_hash}"
        elif "sepolia" in self.selected_network.lower():
            return f"https://sepolia.etherscan.io/tx/{tx_hash}"
        elif "bnb main" in self.selected_network.lower():
            return f"https://bscscan.com/tx/{tx_hash}"
        elif "bnb test" in self.selected_network.lower():
            return f"https://testnet.bscscan.com/tx/{tx_hash}"
        else:
            return "Unknown network"

    def show_input_dialog(self, prompt):
        dialog = CustomDialog(self.root, "Enter data", prompt)
        return dialog.result

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Contract address copied to clipboard.")

    def _on_mousewheel(self, event):
        delta = -1 * (event.delta // 120) if sys.platform == "win32" else int(event.delta)
        self.functions_canvas.yview_scroll(delta, "units")

    def display_contract_balance(self, address):
        if not hasattr(self, 'contract_balance_frame'):
            self.contract_balance_frame = Frame(self.left_frame, bg='#1e1e1e')
            self.contract_balance_frame.pack(pady=5, fill=X)

        balance_label = Label(self.contract_balance_frame, text="Contract Balance:", bg='#1e1e1e', fg='white')
        balance_label.grid(row=0, column=0, padx=5)

        self.balance_output = Label(self.contract_balance_frame, text="0 ETH", bg='#1e1e1e', fg='white')
        self.balance_output.grid(row=0, column=1, padx=5)

        self.address_output = Label(
            self.contract_balance_frame,
            text=f" {address}",
            bg='#1e1e1e',
            fg='#ADD8E6',
            font=('Arial', 10, 'bold'),
            cursor="hand2"
        )
        self.address_output.bind("<Button-1>", lambda e: self.open_block_explorer(address))
        self.address_output.grid(row=1, column=0, padx=5, columnspan=2, sticky='w')

        copy_icon = Button(self.contract_balance_frame, text="📋", command=lambda: self.copy_to_clipboard(address),
                           bg='#1e1e1e', fg='white', cursor="hand2")
        copy_icon.grid(row=1, column=2, padx=5, sticky='w')

    def open_block_explorer(self, address):
        if self.selected_network == "ETH Main Network":
            url = f"https://etherscan.io/address/{address}"
        elif self.selected_network == "BNB Main Network":
            url = f"https://bscscan.com/address/{address}"
        elif self.selected_network == "BNB Test Network":
            url = f"https://testnet.bscscan.com/address/{address}"
        else:

            messagebox.showerror("Ошибка", "Неизвестная сеть выбрана.")
            return

        webbrowser.open(url)

    def _bind_mousewheel(self, event):
        self.functions_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.functions_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.functions_canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.functions_canvas.unbind_all("<MouseWheel>")
        self.functions_canvas.unbind_all("<Button-4>")
        self.functions_canvas.unbind_all("<Button-5>")

    def on_enter_button(self, event):
        event.widget.config(background='darkgrey', relief=GROOVE, cursor="hand2")

    def on_leave_button(self, event):
        event.widget.config(background=event.widget.original_bg, relief=RAISED, cursor="")

    def clear_success_logs(self):
        pass


if __name__ == "__main__":
    root = Tk()
    app = ContractInterfaceApp(root)
    root.mainloop()
