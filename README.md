# High-Throughput Arbitrage & Optimization Engine

## Overview
A modular, high-performance Python engine designed to identify and mathematically optimize statistical arbitrage opportunities across independent data streams (bookmaker APIs). 

## Architecture
- **Asynchronous Data Ingestion**: Utilizes `aiohttp` to directly interface with internal JSON APIs, bypassing heavy headless browsers for maximum throughput.
- **Normalization Engine**: Implements fuzzy string matching (`thefuzz`) to resolve non-standardized entity names (e.g., E-Soccer teams, Tennis players) across different data structures.
- **Mathematical Optimization**: A deterministic calculator that applies specific constraint logic (e.g., fixed €50 stake limit, non-linear boosted odds) to calculate the exact hedge required to guarantee uniform positive expected value (EV), regardless of the discrete outcome.

## Tech Stack
Python | `aiohttp` | `pydantic` | `thefuzz`
