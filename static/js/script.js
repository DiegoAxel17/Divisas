console.log('script.js cargado');

// --------- Chart setup ----------
const canvas = document.getElementById('divisas-chart');
const ctx = canvas.getContext('2d');
canvas.style.width = '90%';
canvas.style.height = '250px';

let divisasChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'EUR/USD',
      data: [],
      fill: false,
      borderColor: '#0d6efd',
      backgroundColor: '#0d6efd',
      pointBackgroundColor: '#0d6efd',
      pointRadius: 3,
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: { display: true, text: 'Hora (local)' },
        ticks: { autoSkip: true, maxTicksLimit: 10 }
      },
      y: {
        beginAtZero: false,
        title: { display: true, text: 'Tasa de Cambio' },
        ticks: { stepSize: 0.01 }
      }
    }
  }
});

// Helpers
function fmtLocal(tsUtc) {
  const d = new Date(tsUtc);
  return d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
}

async function fetchHistory(pair, start = null, end = null) {
  const qs = new URLSearchParams({ pair, limit: '500' });
  if (start) qs.append('start', start);
  if (end) qs.append('end', end);
  const res = await fetch(`/api/history?${qs.toString()}`);
  const json = await res.json();
  if (!json.items) return [];
  return json.items;
}

async function fetchAndPersistRate(pair) {
  const res = await fetch(`/api/rate?pair=${encodeURIComponent(pair)}`);
  if (!res.ok) {
    const txt = await res.text();
    console.warn('Error al obtener cotización:', txt);
    return null;
  }
  const json = await res.json();
  return json; // {pair, rate, ts_utc}
}

function resetChart(pair) {
  if (divisasChart) {
    divisasChart.destroy();
  }
  const ctx2 = document.getElementById('divisas-chart').getContext('2d');
  divisasChart = new Chart(ctx2, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: pair,
        data: [],
        fill: false,
        borderColor: '#0d6efd',
        backgroundColor: '#0d6efd',
        pointBackgroundColor: '#0d6efd',
        pointRadius: 3,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: 'Hora (local)' }, ticks: { autoSkip: true, maxTicksLimit: 10 } },
        y: { beginAtZero: false, title: { display: true, text: 'Tasa de Cambio' }, ticks: { stepSize: 0.01 } }
      }
    }
  });
}

async function loadPairWithHistory(pair) {
  resetChart(pair);
  // 1) Carga historial guardado
  const hist = await fetchHistory(pair);
  hist.forEach(item => {
    divisasChart.data.labels.push(fmtLocal(item.ts_utc));
    divisasChart.data.datasets[0].data.push(item.rate);
  });
  divisasChart.update();
  // 2) Hace una nueva lectura (se guarda en servidor)
  const latest = await fetchAndPersistRate(pair);
  if (latest) {
    divisasChart.data.labels.push(fmtLocal(latest.ts_utc));
    divisasChart.data.datasets[0].data.push(latest.rate);
    divisasChart.update();
  }
}

// --- Cambio de divisas y actualización periódica ---
const currencies = ['EUR/USD', 'USD/JPY', 'GBP/USD'];
let currentCurrencyIndex = 0;

async function switchCurrency(index) {
  currentCurrencyIndex = index;
  const pair = currencies[currentCurrencyIndex];
  await loadPairWithHistory(pair);
}

document.getElementById('divisas-next').addEventListener('click', async () => {
  const i = (currentCurrencyIndex + 1) % currencies.length;
  await switchCurrency(i);
});

document.getElementById('divisas-prev').addEventListener('click', async () => {
  const i = (currentCurrencyIndex - 1 + currencies.length) % currencies.length;
  await switchCurrency(i);
});

// Actualización cada minuto: usa la API del backend (que también guarda)
setInterval(async () => {
  const pair = currencies[currentCurrencyIndex];
  const latest = await fetchAndPersistRate(pair);
  if (latest) {
    divisasChart.data.labels.push(fmtLocal(latest.ts_utc));
    divisasChart.data.datasets[0].data.push(latest.rate);
    if (divisasChart.data.labels.length > 600) {
      divisasChart.data.labels.shift();
      divisasChart.data.datasets[0].data.shift();
    }
    divisasChart.update();
  }
}, 60000);

// --- Filtros por fecha ---
function getDateInputs() {
  const s = document.getElementById('start-date').value;
  const e = document.getElementById('end-date').value;
  const toIso = (v) => v ? new Date(v).toISOString() : null;
  return { start: toIso(s), end: toIso(e) };
}

async function applyFilter() {
  const pair = currencies[currentCurrencyIndex];
  const { start, end } = getDateInputs();
  resetChart(pair);
  const hist = await fetchHistory(pair, start, end);
  hist.forEach(item => {
    divisasChart.data.labels.push(fmtLocal(item.ts_utc));
    divisasChart.data.datasets[0].data.push(item.rate);
  });
  divisasChart.update();
}

async function clearFilter() {
  document.getElementById('start-date').value = '';
  document.getElementById('end-date').value = '';
  const pair = currencies[currentCurrencyIndex];
  await loadPairWithHistory(pair);
}

async function deleteRange() {
  const pair = currencies[currentCurrencyIndex];
  const { start, end } = getDateInputs();
  if (!start && !end) {
    alert('Selecciona al menos una fecha para borrar.');
    return;
  }
  if (!confirm('¿Seguro que quieres borrar ese rango de historial?')) return;
  await fetch('/api/delete_history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pair, start, end })
  });
  await applyFilter();
}

document.getElementById('apply-filter').addEventListener('click', applyFilter);
document.getElementById('clear-filter').addEventListener('click', clearFilter);
document.getElementById('delete-range').addEventListener('click', deleteRange);

// -------- Noticias --------
const newsApiKey  = '3fceba5ce12844f0ab839aea7b08ebc1';
const newsUrl = `https://newsapi.org/v2/everything?language=es&q=noticias&apiKey=${newsApiKey}`;
const newsContainer = document.getElementById('noticias-content');
let articles = [];
let newsIndex = 0;

async function updateNews() {
  try {
    const res  = await fetch(newsUrl);
    const json = await res.json();
    if (json.status !== 'ok' || !Array.isArray(json.articles) || json.articles.length === 0) {
      newsContainer.innerHTML = '<p>No hay noticias disponibles.</p>';
      return;
    }
    articles = json.articles;
    newsIndex = 0;
    showArticle();
  } catch (err) {
    newsContainer.innerHTML = '<p>Error al cargar noticias.</p>';
  }
}

function showArticle() {
  if (!articles.length) {
    newsContainer.innerHTML = '<p>No hay noticias disponibles.</p>';
    return;
  }
  const art = articles[newsIndex];
  newsContainer.innerHTML = `
    <div class="card mb-3" style="max-width: 100%;">
      ${art.urlToImage ? `<img src="${art.urlToImage}" class="card-img-top" alt="">` : ''}
      <div class="card-body">
        <h5 class="card-title">${art.title}</h5>
        <p class="card-text">${art.description || ''}</p>
      </div>
    </div>
  `;
}

document.getElementById('noticias-next').addEventListener('click', () => {
  newsIndex = (newsIndex + 1) % articles.length;
  showArticle();
});
document.getElementById('noticias-prev').addEventListener('click', () => {
  newsIndex = (newsIndex - 1 + articles.length) % articles.length;
  showArticle();
});

// --- Carga inicial ---
(async () => {
  await loadPairWithHistory('EUR/USD');
  updateNews();
})();


