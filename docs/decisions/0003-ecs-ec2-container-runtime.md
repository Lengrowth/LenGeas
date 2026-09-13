# ADR-0003 — ECS on EC2 container runtime

- Status: accepted
- Phase review state: accepted
- Date: 2026-09-13
- Owners: Infrastructure owner; SRE owner
- Supersedes: none
- Superseded by: none

## Context

Canonical APIs, realtime services, workers, and simulations require private networking, AZ placement, capacity providers, ARM64 images, controlled Spot use, and managed draining.

## Decision

Run containers on Amazon ECS using EC2 capacity providers and ECS-optimized Amazon Linux 2023 ARM64 instances. Separate general, simulation, realtime, and critical-worker capacity providers; use private subnets, task roles, read-only filesystems, non-root containers, and at least one critical task per AZ.

## Consequences

This preserves the documented capacity and placement model and supports cost controls. It requires AMI, instance, draining, autoscaling, image, and capacity operations.

## Rejected designs

- Public Kubernetes control plane: rejected because it changes the documented orchestration boundary.
- Publicly addressed containers: rejected because private-subnet origin protection is mandatory.

## Validation

Terraform reproduction, image provenance, AZ-loss, draining, autoscaling, capacity, and cost tests are required before production rollout.

## Rollout and reversal

Deploy by immutable image digest to staging, run smoke and canary checks, then promote. Reverse traffic to the prior task set and retain contract-compatible data changes.
