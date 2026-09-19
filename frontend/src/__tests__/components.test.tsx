import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { PriorityBadge, StatusBadge } from "../components/SeverityBadge";
import { RiskGauge } from "../components/RiskGauge";

describe("Frontend Component Tests", () => {
  it("renders PriorityBadge correctly for P1", () => {
    render(<PriorityBadge priority="P1" />);
    expect(screen.getByText("P1")).toBeDefined();
  });

  it("renders StatusBadge correctly for CONTAINED", () => {
    render(<StatusBadge status="CONTAINED" />);
    expect(screen.getByText("CONTAINED")).toBeDefined();
  });

  it("renders RiskGauge with numeric score", () => {
    render(<RiskGauge score={85.5} priority="P1" />);
    expect(screen.getByText("85.5")).toBeDefined();
    expect(screen.getByText("P1")).toBeDefined();
  });
});
