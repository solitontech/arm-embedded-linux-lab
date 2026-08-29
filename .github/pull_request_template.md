## Summary
<!-- One sentence describing what this PR does -->

## Type of Change
- [ ] New project feature
- [ ] Infrastructure / tooling
- [ ] Bug fix
- [ ] Documentation

## Checklist
- [ ] Code compiles with the AArch64 cross-compiler (`aarch64-linux-gnu-g++`)
- [ ] No board-specific values (CPU flags, serial ports) hardcoded in `shared/`
- [ ] New hardware boards have a `tools/deploy/boards/<name>.env.example` file
- [ ] New projects start from `shared/templates/new_project/`
- [ ] CI smoke test passes

## Testing Done
<!-- How did you verify this change? (e.g., compiled locally, deployed to rpi4, ran CI) -->
