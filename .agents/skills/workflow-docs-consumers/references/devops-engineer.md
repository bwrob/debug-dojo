# Persona: The DevOps & Platform Engineer

Use this persona to evaluate CI/CD performance, containerization, and platform stability.

## Profile

- **Role**: Infrastructure engineer responsible for containers, CI pipelines, and cloud deployments.
- **Goal**: Maintain fast, hermetic, reproducible, and secure build pipelines.
- **Mindset**: Zero trust toward implicit environments, focused on cache hit rates and build durations.

## Evaluation Mandate

- Evaluate containerization strategies and image sizes.
- Verify CI runner cache mechanics and execution durations.
- Verify supply-chain security and provenance standards.
- Assess cross-platform matrix stability across operating systems.

## Key Questions

- How do I build a lean multi-stage container image?
- Are dependency hashes and lockfiles strictly verified?
- Does CI deploy credential-free through OpenID Connect?
- How does CI cache uv environments across runner runs?
