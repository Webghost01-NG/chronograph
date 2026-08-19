"""Authentic on-chain protocol records, contract deployments, EIP evolutions, and exploit forensics."""

ONCHAIN_ENTITIES = [
    # ─── Protocols & Foundations ───
    {
        "id": "proto_uniswap",
        "name": "Uniswap",
        "type": "DEX_Protocol",
        "aliases": ["Uniswap Labs", "UNI", "Hayden Adams"],
    },
    {
        "id": "proto_ethereum",
        "name": "Ethereum",
        "type": "L1_Blockchain",
        "aliases": ["ETH", "Mainnet", "Vitalik Buterin"],
    },
    {
        "id": "proto_aave",
        "name": "Aave",
        "type": "Lending_Protocol",
        "aliases": ["ETHLend", "Aave Labs", "Stani Kulechov"],
    },
    {
        "id": "proto_curve",
        "name": "Curve Finance",
        "type": "Stableswap_DEX",
        "aliases": ["Curve", "CRV", "Michael Egorov"],
    },
    {
        "id": "proto_eigenlayer",
        "name": "EigenLayer",
        "type": "Restaking_Protocol",
        "aliases": ["Eigen", "Sreeram Kannan"],
    },
    {
        "id": "proto_makerdao",
        "name": "MakerDAO",
        "type": "CDP_Protocol",
        "aliases": ["Sky", "DAI", "Rune Christensen"],
    },
    {
        "id": "proto_euler",
        "name": "Euler Finance",
        "type": "Lending_Protocol",
        "aliases": ["Euler", "EUL", "Michael Bentley"],
    },
    # ─── Smart Contracts & Implementations ───
    {
        "id": "contract_univ1_factory",
        "name": "UniswapV1Factory",
        "type": "SmartContract",
        "address": "0xc0a47dFe034B400B47bDaD5FecDa2621de6c4d95",
    },
    {
        "id": "contract_univ2_factory",
        "name": "UniswapV2Factory",
        "type": "SmartContract",
        "address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    },
    {
        "id": "contract_univ3_factory",
        "name": "UniswapV3Factory",
        "type": "SmartContract",
        "address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    },
    {
        "id": "contract_univ4_poolmanager",
        "name": "UniswapV4PoolManager",
        "type": "SmartContract",
        "address": "0x000000000004444c5dc75cB358380D2e3dE08A90",
    },
    {
        "id": "contract_aave_v3_pool",
        "name": "AaveV3PoolAddressesProvider",
        "type": "SmartContract",
        "address": "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
    },
    {
        "id": "contract_euler_etoken",
        "name": "EulerEToken",
        "type": "SmartContract",
        "address": "0xbbbbbbbb29d6606822736796ec56bb01ec04e5c4",
    },
    # ─── Core Upgrades & EIPs ───
    {
        "id": "eip_1559",
        "name": "EIP-1559",
        "type": "Ethereum_Standard",
        "title": "Fee market change for ETH 1.0 chain",
    },
    {
        "id": "eip_4844",
        "name": "EIP-4844",
        "type": "Ethereum_Standard",
        "title": "Shard Blob Transactions (Proto-Danksharding)",
    },
    {
        "id": "eip_4337",
        "name": "EIP-4337",
        "type": "Ethereum_Standard",
        "title": "Account Abstraction using Alt Mempool",
    },
]

ONCHAIN_TEMPORAL_FACTS = [
    # ─── Uniswap Architectural Evolution ───
    {
        "id": "fact_uni_v1",
        "subject": "Uniswap",
        "object": "UniswapV1Factory",
        "content": "Uniswap V1 launched on Ethereum Mainnet in November 2018 using constant product formula x*y=k with mandatory ETH trading pairs.",
        "timestamp": 1541116800000,  # Nov 2018
        "valid_from": 1541116800000,
        "valid_to": 1589760000000,  # Superseded by V2 in May 2020
    },
    {
        "id": "fact_uni_v2",
        "subject": "Uniswap",
        "object": "UniswapV2Factory",
        "content": "Uniswap V2 launched in May 2020 enabling direct ERC20-to-ERC20 pairs, on-chain TWAP price oracles, and flash swaps.",
        "timestamp": 1589760000000,  # May 2020
        "valid_from": 1589760000000,
        "valid_to": 1620172800000,  # Superseded by V3 in May 2021
    },
    {
        "id": "fact_uni_v3",
        "subject": "Uniswap",
        "object": "UniswapV3Factory",
        "content": "Uniswap V3 launched in May 2021 introducing Concentrated Liquidity, customizable fee tiers (0.05%, 0.3%, 1%), and NFT LP positions.",
        "timestamp": 1620172800000,  # May 2021
        "valid_from": 1620172800000,
        "valid_to": 1718236800000,  # Superseded by V4 in 2024
    },
    {
        "id": "fact_uni_v4",
        "subject": "Uniswap",
        "object": "UniswapV4PoolManager",
        "content": "Uniswap V4 introduces Custom Hooks, Singleton architecture (all pools in one contract), dynamic fees, and Flash Accounting via EIP-1153 transient storage.",
        "timestamp": 1718236800000,  # June 2024
        "valid_from": 1718236800000,
        "valid_to": -1,  # Current active standard
    },
    # ─── Ethereum Network Hard Forks ───
    {
        "id": "fact_eth_london",
        "subject": "Ethereum",
        "object": "EIP-1559",
        "content": "London Hard Fork activated at block 12,965,000 introducing base fee burning via EIP-1559 and dynamic block sizing.",
        "timestamp": 1628164800000,  # Aug 2021
        "valid_from": 1628164800000,
        "valid_to": -1,
    },
    {
        "id": "fact_eth_dencun",
        "subject": "Ethereum",
        "object": "EIP-4844",
        "content": "Dencun Upgrade activated on March 13 2024 introducing Blobspace (EIP-4844 Proto-Danksharding) cutting L2 rollup gas fees by 90%.",
        "timestamp": 1710334800000,  # March 2024
        "valid_from": 1710334800000,
        "valid_to": -1,
    },
    # ─── Real Exploits & Forensics ───
    {
        "id": "fact_euler_exploit",
        "subject": "Euler Finance",
        "object": "EulerEToken",
        "content": "On March 13 2023 Euler Finance suffered a $197M exploit via a flawed donation mechanism in eToken.donateToReserve which created unbacked debt without health factor checks.",
        "timestamp": 1678665600000,  # March 2023
        "valid_from": 1678665600000,
        "valid_to": 1680566400000,  # Superseded by full funds return in April 2023
    },
    {
        "id": "fact_euler_recovered",
        "subject": "Euler Finance",
        "object": "EulerEToken",
        "content": "On April 4 2023 all $197M of recoverable stolen assets were returned by the exploiter following on-chain negotiations, and Euler V2 was rebuilt as a modular vault architecture.",
        "timestamp": 1680566400000,  # April 2023
        "valid_from": 1680566400000,
        "valid_to": -1,
    },
]

ONCHAIN_SUPERSEDED_CHAINS = [
    ("fact_uni_v1", "fact_uni_v2", "protocol_upgrade", 1589760000000),
    ("fact_uni_v2", "fact_uni_v3", "concentrated_liquidity_upgrade", 1620172800000),
    ("fact_uni_v3", "fact_uni_v4", "hooks_singleton_upgrade", 1718236800000),
    (
        "fact_euler_exploit",
        "fact_euler_recovered",
        "exploit_resolution_and_v2_pivot",
        1680566400000,
    ),
]
