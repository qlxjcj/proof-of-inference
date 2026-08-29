# Deployment Guide

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your private key
```

## Deployment

### Deploy to Testnet

```bash
python scripts/deploy.py --network testnet_bradbury
```

This will:
- Deploy the contract to GenLayer Bradbury testnet
- Save deployment info to `deployment.json`
- Display the contract address and explorer link

### Deploy to Other Networks

```bash
# Asimov testnet
python scripts/deploy.py --network testnet_asimov

# Local network (for development)
python scripts/deploy.py --network localnet
```

## Testing

### Run Local Tests

```bash
python -m pytest tests/direct/ -v
```

### Run Testnet Tests

After deployment, run end-to-end tests:

```bash
python scripts/testnet_test.py --network testnet_bradbury
```

Or specify a custom address:

```bash
python scripts/testnet_test.py --address 0x...
```

## Contract Verification

After deployment, verify your contract on the explorer:

1. Visit the explorer link from deployment output
2. Click "Verify Contract"
3. Upload `proof_of_inference.py`
4. Wait for verification

## Updating Frontend

After deployment, update the contract address in `index.html`:

```javascript
const CONTRACT = '0x...'; // Your deployed contract address
```

## Troubleshooting

### Common Issues

1. **Insufficient balance**: Ensure your account has enough ETH for deployment
2. **Network connection**: Check RPC URL in .env
3. **Private key**: Ensure private key is correct (without 0x prefix)

### Getting Testnet ETH

Visit the GenLayer faucet to get testnet ETH:
- Bradbury: https://faucet-bradbury.genlayer.com
- Asimov: https://faucet-asimov.genlayer.com
