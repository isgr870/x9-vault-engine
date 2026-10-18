# X9 // Dual-Track Vault

Tactical & Enterprise secure data vault, binary sharding engine, and autonomous subnet mesh telemetry system.

## Overview
X9-Vault is an advanced local-first secure vault architecture featuring:
- **HTTP Core Engine** running on port `8090`[span_0](start_span)[span_0](end_span).
- **Tactical Deadman Timer & Zeroization** routines for emergency state wiping[span_1](start_span)[span_1](end_span).
- **Subnet Mesh Telemetry & WebRTC Peering**[span_2](start_span)[span_2](end_span).

## Installation & Local Run
1. Clone the repository into an empty directory[span_3](start_span)[span_3](end_span).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the vault server:
   ```bash
   python3 x9_unified.py
   ```

## Environment Variables
- `TMPDIR`: Working directory for volatile shards and temporary vault files[span_4](start_span)[span_4](end_span).
- `HTTP_PORT`: Port binding for the web dashboard and API (default: `8090`)[span_5](start_span)[span_5](end_span).

## Testing
Run the test suite via pytest:
```bash
pytest tests/ -v
```
