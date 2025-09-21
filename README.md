# FactorialHR Work Time Verification

![pyversions](https://img.shields.io/pypi/pyversions/fwtv) ![implementation](https://img.shields.io/pypi/implementation/fwtv) ![status](https://img.shields.io/pypi/status/fwtv) ![pypi](https://img.shields.io/pypi/v/fwtv) ![dpm](https://img.shields.io/pypi/dm/fwtv) ![docker](https://img.shields.io/docker/pulls/ghcr.io/leon1995/fwtv)

A web application built with [Reflex](https://reflex.dev) that verifies employee attendance records against German labor law requirements. The application integrates with FactorialHR's API to fetch attendance data and provides compliance checking with an intuitive web interface.

## 🎯 Features

- **German Labor Law Compliance**: Automatically verifies attendance against German work time regulations
- **FactorialHR Integration**: Seamless connection to FactorialHR API for data retrieval
- **Modern Web Interface**: Built with Reflex for a responsive, modern UI
- **Docker Support**: Containerized deployment with multi-architecture support
- **CI/CD Pipeline**: Automated testing, building, and deployment

## 📋 Compliance Rules

The application verifies the following German labor law requirements:

- ⏰ **6-hour rule**: Work time longer than 6 hours requires a 30-minute break
- ⏰ **9-hour rule**: Work time longer than 9 hours requires a 45-minute break  
- ⏰ **10-hour rule**: Work time longer than 10 hours requires an 11-hour rest period
- 🕕 **Time window**: Work time must be within 6:00 AM and 10:00 PM

![main_window](./docs/images/working_time_verification.png "Main Window")

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Pull the latest development image
docker pull ghcr.io/leon1995/fwtv:dev

# Run the container
docker run -p 8080:8080 \
  -e FACTORIAL_API_KEY=your_api_key \
  -e FACTORIAL_COMPANY_ID=your_company_id \
  ghcr.io/leon1995/fwtv:dev
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/leon1995/fwtv.git
cd fwtv

# Install dependencies
uv sync --frozen

# Configure environment
cp .env.sample .env
# Edit .env with your FactorialHR credentials

# Run the application
uv run reflex run --env prod
```

## 🐳 Docker Images

The project provides pre-built Docker images for easy deployment:

| Tag | Description | Usage |
|-----|-------------|-------|
| `dev` | Latest development build | `ghcr.io/leon1995/fwtv:dev` |
| `v1.0.0` | Specific release version | `ghcr.io/leon1995/fwtv:v1.0.0` |
| `latest` | Latest stable release | `ghcr.io/leon1995/fwtv:latest` |

### Multi-Architecture Support

All Docker images support both `linux/amd64` and `linux/arm64` architectures, making them compatible with:
- Intel/AMD x86_64 systems
- ARM64 systems (Apple Silicon, ARM servers)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables from [`.env.sample`](.env.sample)

### FactorialHR Setup

1. Log in to your FactorialHR account
2. Navigate to Settings → API
3. Generate an API key
4. Note your Company ID from the URL or settings

## 🏗️ CI/CD Pipeline

The project includes automated CI/CD pipelines:

### Development Pipeline
- **Triggers**: Push to main branch, pull requests
- **Actions**: Linting, testing, Docker image building
- **Output**: Development Docker images tagged as `dev`

### Release Pipeline  
- **Triggers**: Git tags (e.g., `v1.0.0`)
- **Actions**: Version extraction, Docker image building, GitHub release creation
- **Output**: Versioned Docker images and GitHub releases

### Workflow Features
- ✅ Multi-architecture Docker builds (AMD64 + ARM64)
- ✅ Automated testing across Python 3.11, 3.12, 3.13
- ✅ Cross-platform compatibility (Linux, Windows, macOS)
- ✅ GitHub Container Registry integration
- ✅ Automated release management

## 🧪 Development

### Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional)

### Setup Development Environment

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format .

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** development dependencies (`uv sync --group dev`)
4. **Make** your changes
5. **Run** tests (`uv run pytest`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Development Guidelines

- Follow the existing code style (enforced by Ruff)
- Add tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass

## ⚠️ Disclaimer

**Important**: This application is provided for informational purposes only. While it implements German labor law requirements, I do not guarantee complete compliance with current regulations. Labor laws may change, and this tool should not be considered legal advice.

**Use at your own risk**: Always consult with legal professionals for official compliance verification.

## 📄 License

This project is licensed under the GNU Affero General Public License v3 - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Homepage**: https://github.com/leon1995/fwtv
- **Bug Tracker**: https://github.com/leon1995/fwtv/issues
- **Changelog**: https://github.com/leon1995/fwtv/blob/main/CHANGELOG.md
- **Docker Hub**: https://github.com/leon1995/fwtv/pkgs/container/fwtv
