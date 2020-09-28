REBASE_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "rebase",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

UNISWAP_ABI = [
    {
        'constant': True, 'inputs': [], 'name': 'getReserves',
        'outputs': [
            {'internalType': 'uint112', 'name': '_reserve0', 'type': 'uint112'},
            {'internalType': 'uint112', 'name': '_reserve1', 'type': 'uint112'},
            {'internalType': 'uint32', 'name': '_blockTimestampLast', 'type': 'uint32'}
        ],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function'}
]

ORACLES_ABI = [
    {
        'constant': False,
        'inputs': [
            {'name': 'payload',
             'type': 'uint256'}
        ],
        'name': 'pushReport',
        'outputs': [],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'}
]

PION_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"}
]
