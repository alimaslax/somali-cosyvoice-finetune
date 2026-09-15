'use strict';

// Audio stays native HTML; pause other samples when a comparison starts.
document.querySelectorAll('audio').forEach(player => {
  player.addEventListener('play', () => {
    document.querySelectorAll('audio').forEach(other => {
      if (other !== player) other.pause();
    });
  });
});

async function loadCharts() {
  const charts = [...document.querySelectorAll('.chart')];
  try {
    if (!window.Plotly) throw new Error('Plotly could not load');
    const response = await fetch('assets/charts.json');
    if (!response.ok) throw new Error(`Chart data: ${response.status}`);
    const figures = await response.json();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(async entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const index = charts.indexOf(entry.target);
        const figure = figures[index];
        try {
          entry.target.replaceChildren();
          await Plotly.newPlot(entry.target, figure.data, figure.layout, {
            displayModeBar: false, responsive: true, staticPlot: true
          });
        } catch (error) {
          entry.target.textContent = 'This chart could not be displayed. Please reload the page.';
          entry.target.classList.add('chart-error');
          console.error(error);
        }
      });
    }, { rootMargin: '250px' });
    charts.forEach(chart => observer.observe(chart));
  } catch (error) {
    charts.forEach(chart => {
      chart.textContent = 'Charts could not load. Please reload the page.';
      chart.classList.add('chart-error');
    });
    console.error(error);
  }
}
loadCharts();
