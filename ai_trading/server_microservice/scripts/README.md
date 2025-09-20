# Scripts Directory

Utility scripts for building and deploying the microservice architecture.

## Available Scripts

- **build-all.sh**: Build all service Docker images
- **deploy-dev.sh**: Deploy development environment  
- **deploy-prod.sh**: Deploy production environment

## Usage

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Build all services
./scripts/build-all.sh

# Deploy development
./scripts/deploy-dev.sh

# Deploy production
./scripts/deploy-prod.sh
```