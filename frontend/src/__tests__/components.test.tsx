import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PriorityBadge, StatusBadge } from "../components/SeverityBadge";
import { RiskGauge } from "../components/RiskGauge";
import type { RiskBreakdown } from "../types";

describe("Frontend Component Tests", () => {
  it("renders PriorityBadge correctly for P1", () => {
    render(<PriorityBadge priority="P1" />);
    expect(screen.getByText("P1")).toBeDefined();
  });

  it("renders StatusBadge correctly for CONTAINED", () => {
    render(<StatusBadge status="CONTAINED" />);
    expect(screen.getByText("CONTAINED")).toBeDefined();
  });

  it("renders RiskGauge with numeric score and breakdown", () => {
    const mockBreakdown: RiskBreakdown = {
      score: 85.5,
      priority: "P1",
      correlation_bonus: 10.0,
      summary: "Critical multi-vector attack detected on domain controller.",
      factors: [
        {
          factor_name: "Base Severity",
          raw_value: 0.9,
          weight: 0.35,
          contribution: 31.5,
          explanation: "High severity attack pattern",
        },
        {
          factor_name: "Asset Criticality",
          raw_value: 5,
          weight: 0.25,
          contribution: 25.0,
          explanation: "Protected asset targeted",
        },
      ],
    };

    render(<RiskGauge breakdown={mockBreakdown} />);
    expect(screen.getByText("85.5")).toBeDefined();
    expect(screen.getByText("P1 Priority")).toBeDefined();
    expect(screen.getByText("Base Severity")).toBeDefined();
    expect(screen.getByText("Explanation:")).toBeDefined();
  });
});
