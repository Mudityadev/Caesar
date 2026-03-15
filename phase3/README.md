# Phase 3 Build Start: C++ Hot-Path Baseline

Per latency-first direction, Phase 3 begins migration of execution-critical runtime from Python prototypes to C++.

## Implemented in this phase
- C++20 project bootstrap via `CMakeLists.txt`.
- `hft_core` library implementing OMS + pre-trade risk in:
  - `cpp/include/hft/oms_core.hpp`
  - `cpp/src/oms_core.cpp`
- Native unit-test executable:
  - `cpp/tests/oms_core_test.cpp`

## Build and test
```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Design notes
- Keep transition logic deterministic and in-process.
- Avoid dynamic dependencies on the hot path.
- Preserve behavior parity with current Python OMS semantics for safe incremental migration.
