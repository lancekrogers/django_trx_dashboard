export default {
  testEnvironment: "jsdom",
  moduleFileExtensions: ["js", "json"],
  transform: {},
  testMatch: ["**/__tests__/**/*.js", "**/?(*.)+(spec|test).js"],
  coverageDirectory: "coverage",
  collectCoverageFrom: [
    "src/js/**/*.js",
    "!src/js/main.js", // Entry point doesn't need testing
    "!**/node_modules/**",
  ],
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "<rootDir>/__mocks__/styleMock.js",
  },
};