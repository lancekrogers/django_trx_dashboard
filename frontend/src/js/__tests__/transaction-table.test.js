import { describe, test, expect, jest, beforeEach } from "@jest/globals";
import { TransactionTable } from "../transaction-table.js";

describe("TransactionTable", () => {
  let mockContainer;
  let transactionTable;

  beforeEach(() => {
    // Mock container element
    mockContainer = {
      querySelector: jest.fn(),
      insertAdjacentHTML: jest.fn(),
      innerHTML: "",
    };

    // Mock htmx
    global.htmx = {
      trigger: jest.fn(),
    };

    // Create instance
    transactionTable = new TransactionTable(mockContainer);
  });

  describe("constructor", () => {
    test("should call setupFilters and setupInfiniteScroll", () => {
      // Constructor already called in beforeEach
      expect(mockContainer.querySelector).toHaveBeenCalled();
    });
  });

  describe("setupFilters", () => {
    test("should add filter controls if not present", () => {
      mockContainer.querySelector.mockReturnValue(null); // No existing filters

      transactionTable.setupFilters();

      expect(mockContainer.insertAdjacentHTML).toHaveBeenCalledWith(
        "afterbegin",
        expect.stringContaining("tx-type-filter")
      );
      expect(mockContainer.insertAdjacentHTML).toHaveBeenCalledWith(
        "afterbegin",
        expect.stringContaining("All Types")
      );
      expect(mockContainer.insertAdjacentHTML).toHaveBeenCalledWith(
        "afterbegin",
        expect.stringContaining("Export CSV")
      );
    });

    test("should not add filter controls if already present", () => {
      mockContainer.querySelector.mockReturnValue({ id: "tx-type-filter" }); // Filters exist
      mockContainer.insertAdjacentHTML.mockClear();

      transactionTable.setupFilters();

      expect(mockContainer.insertAdjacentHTML).not.toHaveBeenCalled();
    });

    test("should include all transaction type options", () => {
      mockContainer.querySelector.mockReturnValue(null);

      transactionTable.setupFilters();

      const insertedHTML = mockContainer.insertAdjacentHTML.mock.calls[0][1];
      expect(insertedHTML).toContain('<option value="">All Types</option>');
      expect(insertedHTML).toContain('<option value="buy">Buy</option>');
      expect(insertedHTML).toContain('<option value="sell">Sell</option>');
      expect(insertedHTML).toContain('<option value="transfer">Transfer</option>');
    });

    test("should include all period options", () => {
      mockContainer.querySelector.mockReturnValue(null);

      transactionTable.setupFilters();

      const insertedHTML = mockContainer.insertAdjacentHTML.mock.calls[0][1];
      expect(insertedHTML).toContain('<option value="24h">Last 24 Hours</option>');
      expect(insertedHTML).toContain('<option value="7d">Last 7 Days</option>');
      expect(insertedHTML).toContain('<option value="30d">Last 30 Days</option>');
      expect(insertedHTML).toContain('<option value="all">All Time</option>');
    });

    test("should setup HTMX attributes correctly", () => {
      mockContainer.querySelector.mockReturnValue(null);

      transactionTable.setupFilters();

      const insertedHTML = mockContainer.insertAdjacentHTML.mock.calls[0][1];
      expect(insertedHTML).toContain('hx-get="/api/v1/transactions/"');
      expect(insertedHTML).toContain('hx-trigger="change"');
      expect(insertedHTML).toContain('hx-target="#transaction-container"');
      expect(insertedHTML).toContain('hx-include="[name=\'period\']"');
    });
  });

  describe("setupInfiniteScroll", () => {
    test("should create IntersectionObserver", () => {
      const mockObserve = jest.fn();
      const mockIntersectionObserver = jest.fn().mockImplementation(() => ({
        observe: mockObserve,
      }));
      global.IntersectionObserver = mockIntersectionObserver;

      const mockLastRow = { tagName: "TR" };
      mockContainer.querySelector.mockReturnValue(mockLastRow);

      transactionTable.setupInfiniteScroll();

      expect(mockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({ rootMargin: "100px" })
      );
      expect(mockObserve).toHaveBeenCalledWith(mockLastRow);
    });

    test("should trigger next page load when intersecting", () => {
      let observerCallback;
      global.IntersectionObserver = jest.fn().mockImplementation((callback) => {
        observerCallback = callback;
        return { observe: jest.fn() };
      });

      const mockNextButton = { getAttribute: jest.fn() };
      mockContainer.querySelector
        .mockReturnValueOnce({ tagName: "TR" }) // Last row
        .mockReturnValueOnce(mockNextButton); // Next button

      transactionTable.setupInfiniteScroll();

      // Simulate intersection
      const mockEntry = { isIntersecting: true };
      observerCallback([mockEntry]);

      expect(htmx.trigger).toHaveBeenCalledWith(mockNextButton, "click");
    });

    test("should not trigger if not intersecting", () => {
      let observerCallback;
      global.IntersectionObserver = jest.fn().mockImplementation((callback) => {
        observerCallback = callback;
        return { observe: jest.fn() };
      });

      mockContainer.querySelector.mockReturnValue({ tagName: "TR" });

      transactionTable.setupInfiniteScroll();

      // Simulate non-intersection
      const mockEntry = { isIntersecting: false };
      observerCallback([mockEntry]);

      expect(htmx.trigger).not.toHaveBeenCalled();
    });

    test("should handle missing last row gracefully", () => {
      const mockObserve = jest.fn();
      global.IntersectionObserver = jest.fn().mockImplementation(() => ({
        observe: mockObserve,
      }));

      mockContainer.querySelector.mockReturnValue(null); // No last row

      transactionTable.setupInfiniteScroll();

      expect(mockObserve).not.toHaveBeenCalled();
    });

    test("should handle missing next button gracefully", () => {
      let observerCallback;
      global.IntersectionObserver = jest.fn().mockImplementation((callback) => {
        observerCallback = callback;
        return { observe: jest.fn() };
      });

      mockContainer.querySelector
        .mockReturnValueOnce({ tagName: "TR" }) // Last row
        .mockReturnValueOnce(null); // No next button

      transactionTable.setupInfiniteScroll();

      // Simulate intersection
      const mockEntry = { isIntersecting: true };
      observerCallback([mockEntry]);

      expect(htmx.trigger).not.toHaveBeenCalled();
    });
  });
});