# Multi-Counterparty Trade Management Platform (MCTMP)

A simple base project for managing trades across many counterparties with credit control.

## Features
- Counterparty master data: rating, credit limit, netting agreement, collateral, active/suspended
- Trade submission with validation and automatic approval/rejection
- Pre-trade credit check: projected exposure must stay within the counterparty limit
- Exposure = current replacement cost + 5% add-on - collateral (netted or gross)
- Cancel and settle (cash flow per trade) lifecycle
- Reports: trade blotter and counterparty exposure / limit utilisation

## Structure
- `mctmp/models.py` - Counterparty, Trade, enums
- `mctmp/repository.py` - in-memory storage
- `mctmp/exposure.py` - exposure and netting logic
- `mctmp/manager.py` - workflow and credit checks
- `mctmp/reports.py` - text reports
- `main.py` - demo
- `tests/test_mctmp.py` - unit tests

## Run
```
python main.py
python -m unittest discover -s tests
```
Python 3.8+, no third-party packages.

## Ideas to extend
Database storage (SQLite/PostgreSQL), REST API (FastAPI), user roles and approvals, live prices, multi-currency, margin calls.
