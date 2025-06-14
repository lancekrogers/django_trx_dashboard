export class PortfolioChart {
  constructor(canvasElement) {
    this.chart = new Chart(canvasElement.getContext("2d"), {
      type: "line",
      data: {
        datasets: [
          {
            label: "Portfolio Value",
            data: [],
            borderColor: "rgb(59, 130, 246)",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            tension: 0.1,
            pointRadius: 2,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                return `$${context.parsed.y.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`;
              },
            },
          },
          legend: {
            display: false,
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "minute",
              displayFormats: {
                minute: "HH:mm",
              },
            },
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: false,
            ticks: {
              callback: (value) => `$${value.toLocaleString()}`,
              maxTicksLimit: 6,
            },
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
          },
        },
        animation: {
          duration: 0, // Disable for real-time updates
        },
      },
    });

    this.maxDataPoints = 100;
  }

  addDataPoint(data) {
    const dataset = this.chart.data.datasets[0];

    dataset.data.push({
      x: new Date(data.timestamp),
      y: data.total_value_usd,
    });

    // Keep only last N points
    if (dataset.data.length > this.maxDataPoints) {
      dataset.data.shift();
    }

    // Update without animation
    this.chart.update("none");

    // Update summary values if elements exist
    this.updateSummaryValues(data);
  }

  updateSummaryValues(data) {
    // Update total value
    const totalValueEl = document.getElementById("total-value");
    if (totalValueEl) {
      totalValueEl.textContent = data.total_value_usd.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }

    // Update 24h change
    const changeEl = document.getElementById("change-24h");
    if (changeEl && data.change_24h !== undefined) {
      const isPositive = data.change_24h >= 0;
      changeEl.textContent = `${isPositive ? "+" : ""}${data.change_24h.toFixed(2)}%`;
      changeEl.className = isPositive ? "text-green-600" : "text-red-600";
    }

    // Update last updated time
    const lastUpdatedEl = document.getElementById("last-updated");
    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = "Just now";
      lastUpdatedEl.dataset.timestamp = data.timestamp;
    }
  }
}

