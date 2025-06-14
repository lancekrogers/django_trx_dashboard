import { describe, test, expect, jest, beforeEach } from "@jest/globals";
import { PortfolioChart } from "../portfolio-chart.js";

describe("PortfolioChart", () => {
  let mockCanvas;
  let chartInstance;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock canvas element
    mockCanvas = {
      getContext: jest.fn(() => ({
        canvas: {},
      })),
    };

    // Create chart instance
    chartInstance = new PortfolioChart(mockCanvas);
  });

  describe("constructor", () => {
    test("should create Chart instance with correct configuration", () => {
      expect(global.Chart).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          type: "line",
          data: expect.objectContaining({
            datasets: expect.arrayContaining([
              expect.objectContaining({
                label: "Portfolio Value",
                borderColor: "rgb(59, 130, 246)",
              }),
            ]),
          }),
          options: expect.objectContaining({
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
          }),
        })
      );
    });

    test("should set maxDataPoints to 100", () => {
      expect(chartInstance.maxDataPoints).toBe(100);
    });
  });

  describe("addDataPoint", () => {
    test("should add new data point to chart", () => {
      const mockData = {
        timestamp: "2023-12-01T10:00:00Z",
        total_value_usd: 12345.67,
        change_24h: 5.43,
      };

      chartInstance.addDataPoint(mockData);

      const dataset = chartInstance.chart.data.datasets[0];
      expect(dataset.data).toHaveLength(1);
      expect(dataset.data[0]).toEqual({
        x: new Date(mockData.timestamp),
        y: mockData.total_value_usd,
      });
    });

    test("should maintain maximum of 100 data points", () => {
      // Add 101 data points
      for (let i = 0; i < 101; i++) {
        chartInstance.addDataPoint({
          timestamp: new Date(2023, 0, 1, i).toISOString(),
          total_value_usd: 10000 + i,
        });
      }

      const dataset = chartInstance.chart.data.datasets[0];
      expect(dataset.data).toHaveLength(100);
      // First point should be removed
      expect(dataset.data[0].y).toBe(10001);
    });

    test("should call chart update with 'none' animation", () => {
      const mockData = {
        timestamp: "2023-12-01T10:00:00Z",
        total_value_usd: 12345.67,
      };

      chartInstance.addDataPoint(mockData);

      expect(chartInstance.chart.update).toHaveBeenCalledWith("none");
    });
  });

  describe("updateSummaryValues", () => {
    test("should update total value element", () => {
      const mockElement = {
        textContent: "",
      };
      document.getElementById = jest.fn((id) => {
        if (id === "total-value") return mockElement;
        return null;
      });

      const data = { total_value_usd: 12345.67 };
      chartInstance.updateSummaryValues(data);

      expect(mockElement.textContent).toBe("12,345.67");
    });

    test("should update 24h change element with positive value", () => {
      const mockElement = {
        textContent: "",
        className: "",
      };
      document.getElementById = jest.fn((id) => {
        if (id === "change-24h") return mockElement;
        return null;
      });

      const data = { change_24h: 5.43 };
      chartInstance.updateSummaryValues(data);

      expect(mockElement.textContent).toBe("+5.43%");
      expect(mockElement.className).toBe("text-green-600");
    });

    test("should update 24h change element with negative value", () => {
      const mockElement = {
        textContent: "",
        className: "",
      };
      document.getElementById = jest.fn((id) => {
        if (id === "change-24h") return mockElement;
        return null;
      });

      const data = { change_24h: -3.21 };
      chartInstance.updateSummaryValues(data);

      expect(mockElement.textContent).toBe("-3.21%");
      expect(mockElement.className).toBe("text-red-600");
    });

    test("should update last updated element", () => {
      const mockElement = {
        textContent: "",
        dataset: { timestamp: "" },
      };
      document.getElementById = jest.fn((id) => {
        if (id === "last-updated") return mockElement;
        return null;
      });

      const data = { timestamp: "2023-12-01T10:00:00Z" };
      chartInstance.updateSummaryValues(data);

      expect(mockElement.textContent).toBe("Just now");
      expect(mockElement.dataset.timestamp).toBe("2023-12-01T10:00:00Z");
    });

    test("should handle missing elements gracefully", () => {
      document.getElementById = jest.fn(() => null);

      // Should not throw
      expect(() => {
        chartInstance.updateSummaryValues({
          total_value_usd: 12345.67,
          change_24h: 5.43,
          timestamp: "2023-12-01T10:00:00Z",
        });
      }).not.toThrow();
    });
  });
});