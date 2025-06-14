import { describe, test, expect, jest, beforeEach, afterEach } from "@jest/globals";
import { RealTimeManager } from "../real-time-manager.js";

describe("RealTimeManager", () => {
  let manager;
  let mockConnectionIndicator;
  let mockDisconnectionIndicator;

  beforeEach(() => {
    // Mock DOM elements
    mockConnectionIndicator = {
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
    };

    mockDisconnectionIndicator = {
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
    };

    document.getElementById = jest.fn((id) => {
      if (id === "connection-indicator") return mockConnectionIndicator;
      if (id === "disconnection-indicator") return mockDisconnectionIndicator;
      return null;
    });

    // Mock timers
    jest.useFakeTimers();

    // Create manager instance
    manager = new RealTimeManager();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe("constructor", () => {
    test("should initialize with default values", () => {
      expect(manager.connected).toBe(false);
      expect(manager.reconnectAttempts).toBe(0);
      expect(manager.maxReconnectAttempts).toBe(5);
      expect(manager.reconnectDelay).toBe(1000);
    });

    test("should start heartbeat timer", () => {
      // Fast-forward time by 10 seconds
      jest.advanceTimersByTime(10000);
      
      // updateRelativeTimes should be called
      const spy = jest.spyOn(manager, "updateRelativeTimes");
      jest.advanceTimersByTime(10000);
      expect(spy).toHaveBeenCalled();
    });
  });

  describe("setConnected", () => {
    test("should handle connected status", () => {
      manager.setConnected(true);

      expect(manager.connected).toBe(true);
      expect(manager.reconnectAttempts).toBe(0);
      expect(manager.reconnectDelay).toBe(1000);
      expect(mockConnectionIndicator.classList.remove).toHaveBeenCalledWith("hidden");
      expect(mockDisconnectionIndicator.classList.add).toHaveBeenCalledWith("hidden");
    });

    test("should handle disconnected status", () => {
      const attemptReconnectSpy = jest.spyOn(manager, "attemptReconnect");
      
      manager.setConnected(false);

      expect(manager.connected).toBe(false);
      expect(mockConnectionIndicator.classList.add).toHaveBeenCalledWith("hidden");
      expect(mockDisconnectionIndicator.classList.remove).toHaveBeenCalledWith("hidden");
      expect(attemptReconnectSpy).toHaveBeenCalled();
    });
  });

  describe("attemptReconnect", () => {
    test("should attempt reconnection with exponential backoff", () => {
      const mockSSEElement = { getAttribute: jest.fn() };
      document.querySelector = jest.fn(() => mockSSEElement);

      manager.attemptReconnect();

      // First attempt after 1 second
      expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 1000);
      
      jest.advanceTimersByTime(1000);
      
      expect(manager.reconnectAttempts).toBe(1);
      expect(htmx.trigger).toHaveBeenCalledWith(mockSSEElement, "htmx:sseReconnect");
      expect(manager.reconnectDelay).toBe(2000); // Exponential backoff
    });

    test("should stop reconnecting after max attempts", () => {
      manager.reconnectAttempts = 5; // Already at max
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      manager.attemptReconnect();

      expect(consoleSpy).toHaveBeenCalledWith("Max reconnection attempts reached");
      expect(setTimeout).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });

    test("should cap reconnect delay at 30 seconds", () => {
      manager.reconnectDelay = 20000; // 20 seconds

      manager.attemptReconnect();
      jest.advanceTimersByTime(20000);

      expect(manager.reconnectDelay).toBe(30000); // Capped at 30 seconds
    });
  });

  describe("updateRelativeTimes", () => {
    test("should update 'Just now' for recent timestamps", () => {
      const mockElement = {
        textContent: "",
        dataset: { timestamp: new Date().toISOString() },
      };
      document.getElementById = jest.fn((id) => {
        if (id === "last-updated") return mockElement;
        return null;
      });

      manager.updateRelativeTimes();

      expect(mockElement.textContent).toBe("Just now");
    });

    test("should update with minutes for timestamps < 1 hour old", () => {
      const mockElement = {
        textContent: "",
        dataset: { 
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString() // 5 minutes ago
        },
      };
      document.getElementById = jest.fn((id) => {
        if (id === "last-updated") return mockElement;
        return null;
      });

      manager.updateRelativeTimes();

      expect(mockElement.textContent).toBe("5 minutes ago");
    });

    test("should update with hours for timestamps > 1 hour old", () => {
      const mockElement = {
        textContent: "",
        dataset: { 
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
        },
      };
      document.getElementById = jest.fn((id) => {
        if (id === "last-updated") return mockElement;
        return null;
      });

      manager.updateRelativeTimes();

      expect(mockElement.textContent).toBe("2 hours ago");
    });

    test("should handle missing element gracefully", () => {
      document.getElementById = jest.fn(() => null);

      // Should not throw
      expect(() => manager.updateRelativeTimes()).not.toThrow();
    });

    test("should handle singular time units", () => {
      const mockElement = {
        textContent: "",
        dataset: { 
          timestamp: new Date(Date.now() - 1 * 60 * 1000).toISOString() // 1 minute ago
        },
      };
      document.getElementById = jest.fn((id) => {
        if (id === "last-updated") return mockElement;
        return null;
      });

      manager.updateRelativeTimes();

      expect(mockElement.textContent).toBe("1 minute ago");
    });
  });

  describe("showConnected/showDisconnected", () => {
    test("should handle missing indicators gracefully", () => {
      manager.connectionIndicator = null;
      manager.disconnectionIndicator = null;

      // Should not throw
      expect(() => manager.showConnected()).not.toThrow();
      expect(() => manager.showDisconnected()).not.toThrow();
    });
  });
});