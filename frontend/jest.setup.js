// Mock Chart.js
global.Chart = jest.fn().mockImplementation(() => ({
  data: {
    datasets: [{ data: [] }],
  },
  update: jest.fn(),
}));

// Mock HTMX
global.htmx = {
  trigger: jest.fn(),
};

// Mock DOM elements that might not exist in tests
global.document.getElementById = jest.fn((id) => {
  const mockElements = {
    "portfolio-chart": {
      getContext: jest.fn(() => ({
        canvas: {},
      })),
    },
    "total-value": {
      textContent: "",
    },
    "change-24h": {
      textContent: "",
      className: "",
    },
    "last-updated": {
      textContent: "",
      dataset: { timestamp: "" },
    },
    "connection-indicator": {
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
    },
    "disconnection-indicator": {
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
    },
  };
  return mockElements[id] || null;
});